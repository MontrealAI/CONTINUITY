"""Strict, bounded wire formats for the separately versioned local Harness.

Canonical serialization is UTF-8 encoded ASCII JSON with sorted string keys,
no whitespace, finite *integer* numbers only, and no Unicode surrogates.  It is
an explicitly versioned local format, not a claim to implement RFC 8785.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Any


MAX_JSON_BYTES = 1_048_576
MAX_NODES = 50_000
MAX_DEPTH = 32
MAX_EVENTS = 4_096
MAX_ORDERS = 1_024
MAX_UNITS = 1_000_000_000
MAX_TICKS = 1_000_000_000
MAX_INTEGER = 9_007_199_254_740_991
MAX_NS = (1 << 63) - 1
ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
SHA_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
CONTRACT_SCHEMA = "continuity-harness/contract/v1"
REFERENCE_SCHEMA = "continuity-harness/reference/v1"
ARTIFACT_SCHEMA = "continuity-harness/artifact/v1"


ERROR_MESSAGES = {
    "INVALID_JSON": ("The input is not valid JSON.", "L’entrée n’est pas un document JSON valide."),
    "JSON_TOO_LARGE": ("The JSON input exceeds the size limit.", "Le document JSON dépasse la taille autorisée."),
    "JSON_TOO_COMPLEX": ("The JSON structure exceeds the depth or item limit.", "La structure JSON dépasse la profondeur ou le nombre d’éléments autorisé."),
    "DUPLICATE_KEY": ("Duplicate JSON keys are not allowed.", "Les clés JSON en double sont interdites."),
    "NON_INTEGER_NUMBER": ("Only exact integer numbers are supported.", "Seuls les nombres entiers exacts sont acceptés."),
    "INVALID_UNICODE": ("The text contains invalid Unicode.", "Le texte contient des caractères Unicode invalides."),
    "INVALID_TYPE": ("A value has the wrong type.", "Une valeur présente un type incorrect."),
    "INVALID_FIELDS": ("Required fields are missing or unknown fields are present.", "Des champs requis sont absents ou des champs inconnus sont présents."),
    "INVALID_RANGE": ("A value is outside the supported range.", "Une valeur dépasse les limites autorisées."),
    "INVALID_IDENTIFIER": ("An identifier is invalid or unsafe.", "Un identifiant est invalide ou non sûr."),
    "INVALID_DIGEST": ("A SHA-256 digest is invalid.", "Une empreinte SHA-256 est invalide."),
    "UNSUPPORTED_VERSION": ("The schema or version is unsupported.", "Le schéma ou la version n’est pas pris en charge."),
    "INVALID_EVENT": ("An order event is inconsistent with its history.", "Un événement de commande est incompatible avec son historique."),
    "SOURCE_DIGEST_MISMATCH": ("The source events do not match their declared digest.", "Les événements sources ne correspondent pas à l’empreinte déclarée."),
    "UNSAFE_PATH": ("The path is unsafe or is not a regular file.", "Le chemin n’est pas sûr ou ne désigne pas un fichier ordinaire."),
    "MISSING_FILE": ("A required file is missing.", "Un fichier requis est absent."),
    "FILE_READ_ERROR": ("A required file could not be read.", "Un fichier requis n’a pas pu être lu."),
}


class HarnessError(ValueError):
    """Stable machine code plus a technical location, never a favorable result."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)

    def as_dict(self, language: str = "en") -> dict[str, str]:
        pair = ERROR_MESSAGES.get(self.code, (self.code, self.code))
        return {"code": self.code, "message": pair[1 if language == "fr" else 0], "detail": self.detail}


def _fail(code: str, path: str) -> None:
    raise HarnessError(code, path)


def _bounded(value: Any) -> None:
    count = 0
    todo = [(value, 0)]
    while todo:
        item, depth = todo.pop()
        count += 1
        if count > MAX_NODES or depth > MAX_DEPTH:
            _fail("JSON_TOO_COMPLEX", "json")
        if item is None or type(item) is bool:
            continue
        if type(item) is int:
            if not -MAX_NS <= item <= MAX_NS:
                _fail("INVALID_RANGE", "json.integer")
        elif type(item) is str:
            if any(0xD800 <= ord(ch) <= 0xDFFF for ch in item):
                _fail("INVALID_UNICODE", "json.string")
        elif type(item) is list:
            todo.extend((x, depth + 1) for x in item)
        elif type(item) is dict:
            if any(type(key) is not str for key in item):
                _fail("INVALID_TYPE", "json.key")
            todo.extend((x, depth + 1) for x in item.values())
            todo.extend((key, depth + 1) for key in item)
        elif isinstance(item, float):
            _fail("NON_INTEGER_NUMBER", "json.number")
        else:
            _fail("INVALID_TYPE", "json")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("DUPLICATE_KEY", key)
        result[key] = value
    return result


def _no_fraction(value: str) -> None:
    _fail("NON_INTEGER_NUMBER", value[:64])


def strict_loads(data: str | bytes) -> Any:
    if type(data) not in (str, bytes):
        _fail("INVALID_TYPE", "json")
    try:
        raw = data.encode("utf-8") if isinstance(data, str) else data
        if len(raw) > MAX_JSON_BYTES:
            _fail("JSON_TOO_LARGE", "json")
        decoded = raw.decode("utf-8", errors="strict")
        value = json.loads(decoded, object_pairs_hook=_pairs,
                           parse_float=_no_fraction, parse_constant=_no_fraction)
    except HarnessError:
        raise
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise HarnessError("INVALID_JSON", type(exc).__name__) from exc
    _bounded(value)
    return value


def read_bytes(path: str | Path, max_bytes: int = MAX_JSON_BYTES) -> bytes:
    """Bounded no-follow read; callers retain responsibility for trusted parents."""
    path = Path(path)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        if path.is_symlink():
            _fail("UNSAFE_PATH", path.name)
        fd = os.open(path, flags)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                _fail("UNSAFE_PATH", path.name)
            if info.st_size > max_bytes:
                _fail("JSON_TOO_LARGE", path.name)
            chunks = []
            size = 0
            while True:
                chunk = os.read(fd, min(65_536, max_bytes + 1 - size))
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
                if size > max_bytes:
                    _fail("JSON_TOO_LARGE", path.name)
            return b"".join(chunks)
        finally:
            os.close(fd)
    except FileNotFoundError as exc:
        raise HarnessError("MISSING_FILE", path.name) from exc
    except HarnessError:
        raise
    except OSError as exc:
        raise HarnessError("FILE_READ_ERROR", path.name) from exc


def strict_load(path: str | Path) -> Any:
    return strict_loads(read_bytes(path))


def canonical(value: Any) -> bytes:
    _bounded(value)
    data = json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")
    if len(data) > MAX_JSON_BYTES:
        _fail("JSON_TOO_LARGE", "canonical")
    return data


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def object_fields(value: Any, required: set[str], optional: set[str] | None = None,
                  path: str = "object") -> dict:
    if type(value) is not dict:
        _fail("INVALID_TYPE", path)
    if not required <= set(value) or not set(value) <= required | (optional or set()):
        _fail("INVALID_FIELDS", path)
    return value


def integer(value: Any, path: str, lower: int = 0, upper: int = MAX_INTEGER) -> int:
    if type(value) is not int:
        _fail("INVALID_TYPE", path)
    if not lower <= value <= upper:
        _fail("INVALID_RANGE", path)
    return value


def boolean(value: Any, path: str) -> bool:
    if type(value) is not bool:
        _fail("INVALID_TYPE", path)
    return value


def identifier(value: Any, path: str) -> str:
    if type(value) is not str or ID_PATTERN.fullmatch(value) is None or ".." in value:
        _fail("INVALID_IDENTIFIER", path)
    return value


def sha256(value: Any, path: str) -> str:
    if type(value) is not str or SHA_PATTERN.fullmatch(value) is None:
        _fail("INVALID_DIGEST", path)
    return value


def _text(value: Any, path: str, maximum: int = 256) -> str:
    if type(value) is not str or not 1 <= len(value) <= maximum:
        _fail("INVALID_TYPE", path)
    return value


def _list(value: Any, path: str, maximum: int) -> list:
    if type(value) is not list or len(value) > maximum:
        _fail("INVALID_TYPE", path)
    return value


def validate_events(events: Any) -> list[dict]:
    _list(events, "source_events", MAX_EVENTS)
    states = {}
    for seq, event in enumerate(events, 1):
        path = f"source_events[{seq - 1}]"
        if type(event) is not dict:
            _fail("INVALID_TYPE", path)
        action = event.get("type")
        common = {"sequence", "type", "order_id"}
        fields = {"recipient", "product", "spec_sha256", "quantity", "deadline_tick"}
        if action == "ACCEPT":
            object_fields(event, common | fields, path=path)
        elif action == "AMEND":
            object_fields(event, common, fields, path)
            if not set(event) & fields:
                _fail("INVALID_EVENT", path)
        elif action == "CANCEL":
            object_fields(event, common, path=path)
        elif action == "FULFILL":
            object_fields(event, common | {"quantity"}, path=path)
        else:
            _fail("INVALID_EVENT", path + ".type")
        if integer(event["sequence"], path + ".sequence", 1, MAX_EVENTS) != seq:
            _fail("INVALID_EVENT", path + ".sequence")
        oid = identifier(event["order_id"], path + ".order_id")
        for key in ("recipient", "product"):
            if key in event:
                identifier(event[key], path + "." + key)
        if "spec_sha256" in event:
            sha256(event["spec_sha256"], path + ".spec_sha256")
        if "quantity" in event:
            integer(event["quantity"], path + ".quantity", 1, MAX_UNITS)
        if "deadline_tick" in event:
            integer(event["deadline_tick"], path + ".deadline_tick", 1, MAX_TICKS)
        if action == "ACCEPT":
            if oid in states or len(states) >= MAX_ORDERS:
                _fail("INVALID_EVENT", path + ".order_id")
            states[oid] = {"quantity": event["quantity"], "fulfilled": 0, "cancelled": False}
        else:
            previous = states.get(oid)
            if previous is None or previous["cancelled"] or previous["fulfilled"] == previous["quantity"]:
                _fail("INVALID_EVENT", path + ".order_id")
            if action == "AMEND" and "quantity" in event:
                if event["quantity"] < previous["fulfilled"]:
                    _fail("INVALID_EVENT", path + ".quantity")
                previous["quantity"] = event["quantity"]
            elif action == "CANCEL":
                previous["cancelled"] = True
            elif action == "FULFILL":
                previous["fulfilled"] += event["quantity"]
                if previous["fulfilled"] > previous["quantity"]:
                    _fail("INVALID_EVENT", path + ".quantity")
    return events


def validate_contract(value: Any) -> dict:
    required = {"schema", "version", "contract_id", "run_id", "mode", "source_events",
                "source_sha256", "cutoff_sequence", "source_complete", "deadline_tick",
                "wall_deadline_ms", "recovery_objective_ms", "window", "lease_ticks",
                "capacities", "allowed_routes", "permissions", "dependencies",
                "blocked_dependencies", "currency", "budget_minor", "scenario", "seed",
                "fault_schedule", "comparison"}
    c = object_fields(value, required, path="contract")
    canonical(c)  # also bounds direct Python callers before state-changing actions
    if c["schema"] != CONTRACT_SCHEMA or type(c["version"]) is not int or c["version"] != 1:
        _fail("UNSUPPORTED_VERSION", "contract")
    if c["mode"] != "SYNTHETIC_LOCAL_EXECUTION":
        _fail("UNSUPPORTED_VERSION", "contract.mode")
    for key in ("contract_id", "run_id", "scenario"):
        identifier(c[key], "contract." + key)
    validate_events(c["source_events"])
    sha256(c["source_sha256"], "contract.source_sha256")
    if digest(c["source_events"]) != c["source_sha256"]:
        _fail("SOURCE_DIGEST_MISMATCH", "contract.source_sha256")
    integer(c["cutoff_sequence"], "contract.cutoff_sequence", 0, len(c["source_events"]))
    if c["cutoff_sequence"] != len(c["source_events"]):
        _fail("INVALID_EVENT", "contract.cutoff_sequence")
    boolean(c["source_complete"], "contract.source_complete")
    integer(c["deadline_tick"], "contract.deadline_tick", 1, MAX_TICKS)
    integer(c["wall_deadline_ms"], "contract.wall_deadline_ms", 1, 86_400_000)
    integer(c["recovery_objective_ms"], "contract.recovery_objective_ms", 1, 86_400_000)
    integer(c["lease_ticks"], "contract.lease_ticks", 1, MAX_TICKS)
    integer(c["seed"], "contract.seed", 0, MAX_INTEGER)
    integer(c["budget_minor"], "contract.budget_minor", 0, MAX_INTEGER)
    if c["currency"] != "USD":
        _fail("UNSUPPORTED_VERSION", "contract.currency")
    window = object_fields(c["window"], {"start", "end"}, path="contract.window")
    integer(window["start"], "contract.window.start", 0, MAX_TICKS)
    integer(window["end"], "contract.window.end", 1, MAX_TICKS)
    if window["start"] >= window["end"]:
        _fail("INVALID_RANGE", "contract.window")
    capacities = object_fields(c["capacities"], {"primary", "backup"}, path="contract.capacities")
    dependencies = object_fields(c["dependencies"], {"primary", "backup"}, path="contract.dependencies")
    for route in ("primary", "backup"):
        integer(capacities[route], "contract.capacities." + route, 0, MAX_UNITS)
        identifier(dependencies[route], "contract.dependencies." + route)
    routes = _list(c["allowed_routes"], "contract.allowed_routes", 2)
    if any(type(route) is not str or route not in ("primary", "backup") for route in routes) or len(set(routes)) != len(routes):
        _fail("INVALID_TYPE", "contract.allowed_routes")
    permissions = object_fields(c["permissions"], {"activation", "sharing"}, path="contract.permissions")
    for name in permissions:
        boolean(permissions[name], "contract.permissions." + name)
    blocked = _list(c["blocked_dependencies"], "contract.blocked_dependencies", 32)
    for item in blocked:
        identifier(item, "contract.blocked_dependencies")
    if len(set(blocked)) != len(blocked):
        _fail("INVALID_FIELDS", "contract.blocked_dependencies")
    schedule = _list(c["fault_schedule"], "contract.fault_schedule", 128)
    for index, fault in enumerate(schedule):
        p = f"contract.fault_schedule[{index}]"
        object_fields(fault, {"event", "action", "target"}, {"order_id", "tick"}, p)
        for key in ("event", "action", "target", "order_id"):
            if key in fault:
                identifier(fault[key], p + "." + key)
        if "tick" in fault:
            integer(fault["tick"], p + ".tick", 0, MAX_TICKS)
    if len({fault["event"] for fault in schedule}) != len(schedule):
        _fail("INVALID_FIELDS", "contract.fault_schedule")
    comparison = object_fields(c["comparison"], {"suite_id", "fixture_id", "held_out", "information", "resource_policy"}, path="contract.comparison")
    for key in ("suite_id", "fixture_id"):
        identifier(comparison[key], "contract.comparison." + key)
    boolean(comparison["held_out"], "contract.comparison.held_out")
    if comparison["information"] != "EQUAL" or comparison["resource_policy"] != "SHARED_SERVICES":
        _fail("UNSUPPORTED_VERSION", "contract.comparison")
    return c


def validate_reference(value: Any) -> dict:
    r = object_fields(value, {"schema", "run_id", "contract_sha256", "source_sha256", "cutoff_sequence", "source_complete"}, path="reference")
    if r["schema"] != REFERENCE_SCHEMA:
        _fail("UNSUPPORTED_VERSION", "reference.schema")
    identifier(r["run_id"], "reference.run_id")
    sha256(r["contract_sha256"], "reference.contract_sha256")
    sha256(r["source_sha256"], "reference.source_sha256")
    integer(r["cutoff_sequence"], "reference.cutoff_sequence", 0, MAX_EVENTS)
    boolean(r["source_complete"], "reference.source_complete")
    return r


def validate_artifact(value: Any) -> dict:
    keys = {"schema", "run_id", "contract_sha256", "order_id", "recipient", "product",
            "spec_sha256", "quantity", "state", "route", "key", "completed_tick", "completed_monotonic_ns"}
    a = object_fields(value, keys, path="artifact")
    if a["schema"] != ARTIFACT_SCHEMA or a["state"] != "COMPLETED":
        _fail("UNSUPPORTED_VERSION", "artifact")
    for name in ("run_id", "order_id", "recipient", "product", "key"):
        identifier(a[name], "artifact." + name)
    sha256(a["contract_sha256"], "artifact.contract_sha256")
    sha256(a["spec_sha256"], "artifact.spec_sha256")
    integer(a["quantity"], "artifact.quantity", 1, MAX_UNITS)
    integer(a["completed_tick"], "artifact.completed_tick", 0, MAX_TICKS)
    integer(a["completed_monotonic_ns"], "artifact.completed_monotonic_ns", 0, MAX_NS)
    if a["route"] not in ("primary", "backup"):
        _fail("INVALID_IDENTIFIER", "artifact.route")
    return a


def expected_obligations(contract: dict) -> list[dict]:
    """Independent reference replay; imports no constructor, adapter or service.

    The retained contract has authored synthetic provenance.  Replaying it is
    not evidence that a real customer's records are authentic or complete.
    """
    validate_contract(contract)
    state = {}
    for event in contract["source_events"]:
        if event["sequence"] > contract["cutoff_sequence"]:
            break
        oid = event["order_id"]
        kind = event["type"]
        if kind == "ACCEPT":
            state[oid] = {key: event[key] for key in ("order_id", "recipient", "product", "spec_sha256", "quantity", "deadline_tick")}
            state[oid]["fulfilled"] = 0
            state[oid]["cancelled"] = False
        elif kind == "AMEND":
            for key in ("recipient", "product", "spec_sha256", "quantity", "deadline_tick"):
                if key in event:
                    state[oid][key] = event[key]
        elif kind == "CANCEL":
            state[oid]["cancelled"] = True
        elif kind == "FULFILL":
            state[oid]["fulfilled"] += event["quantity"]
    result = []
    for oid, order in sorted(state.items()):
        remaining = order["quantity"] - order["fulfilled"]
        if order["cancelled"] or remaining == 0:
            continue
        result.append({key: order[key] for key in ("order_id", "recipient", "product", "spec_sha256", "deadline_tick")} | {"quantity": remaining})
    return result
