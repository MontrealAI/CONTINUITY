"""Fresh, independent acceptance of retained digital-product exercises.

This module does not import the producer, receiver, participant decision service,
candidate, or controller.  It reads immutable evidence afresh, independently
checks literal label content and replays modeled consent, resource and money
effects.  A saved Passport or a component's favorable verdict is never proof.

The bounded JSON/file primitives come from the preserved v0.1 Harness at
396227d8da2f55f674f479de16089c7ce28ef290.  Their use does not extend that release's
qualification to the separately versioned economic/digital-product experiment.
"""

from __future__ import annotations

import hashlib
from copy import deepcopy
from pathlib import Path, PurePosixPath
import re
import sqlite3
import time
from typing import Any

from continuity_harness.schema import (
    HarnessError, canonical, digest, identifier, integer, object_fields,
    read_bytes, sha256, strict_load, strict_loads,
)


VERSION = "0.2.0"
MAX_DATABASE_BYTES = 134_217_728
MAX_ROWS = 100_000
MAX_EVIDENCE_FILES = 20_000
MAX_NS = 9_223_372_036_854_775_807
PROBE_NAMES = {
    "authority_open_denied", "workspace_open_denied", "network_denied",
    "spawn_denied", "process_inspection_denied",
}
PRODUCT_SCHEMA = "continuity-economy/label-job/v1"
PRODUCT_FIELDS = {
    "schema", "run_id", "contract_id", "contract_sha256", "obligation_id",
    "revision", "recipient", "production_id", "arrangement_id", "provider_id",
    "delivery_id", "capacity_key", "lot_id", "attempt", "first_unit", "last_unit", "supersedes", "labels",
}
LABEL_FIELDS = {
    "ordinal", "serial", "sku", "name_en", "name_fr", "instructions_en",
    "instructions_fr", "lot",
}
LITERAL_FIELDS = LABEL_FIELDS - {"ordinal", "serial"}


class Findings:
    """Preserve observed counterexamples separately from missing evidence."""

    def __init__(self) -> None:
        self.failures: list[dict] = []
        self.unresolved: list[dict] = []
        self._seen: set[tuple] = set()

    def add(self, code: str, detail: str = "", *, scope: str = "integrity",
            obligation_id: str | None = None, arrangement_id: str | None = None,
            unknown: bool = False) -> None:
        identity = (code, detail, scope, obligation_id, arrangement_id, unknown)
        if identity in self._seen:
            return
        self._seen.add(identity)
        row = {"code": code, "detail": detail, "scope": scope}
        if obligation_id is not None:
            row["obligation_id"] = obligation_id
        if arrangement_id is not None:
            row["arrangement_id"] = arrangement_id
        (self.unresolved if unknown else self.failures).append(row)

    def failed(self, *scopes: str) -> bool:
        return any(row["scope"] in scopes for row in self.failures)

    def missing(self, *scopes: str) -> bool:
        return any(row["scope"] in scopes for row in self.unresolved)


def _safe_path(path: Path) -> Path:
    absolute = path.absolute()
    for part in (absolute, *absolute.parents):
        if part.is_symlink():
            raise HarnessError("UNSAFE_PATH", str(part))
    return absolute


def _evidence_path(root: Path, relative: str) -> Path:
    if type(relative) is not str or "\\" in relative:
        raise HarnessError("UNSAFE_PATH", "evidence manifest")
    parts = PurePosixPath(relative)
    if (parts.is_absolute() or not relative.startswith("evidence/")
            or parts.as_posix() != relative or not parts.parts
            or any(piece in ("", ".", "..") or
                   re.fullmatch(r"[A-Za-z0-9_.-]+", piece) is None
                   for piece in parts.parts)):
        raise HarnessError("UNSAFE_PATH", relative)
    return _safe_path(root.joinpath(*parts.parts))


def _hash_file(path: Path) -> str:
    return hashlib.sha256(read_bytes(path, MAX_DATABASE_BYTES)).hexdigest()


def _database(path: Path, tables: dict[str, int]) -> dict[str, list[dict]]:
    """Inspect a closed SQLite evidence copy without creating journals."""
    path = _safe_path(path)
    read_bytes(path, MAX_DATABASE_BYTES)
    for suffix in ("-wal", "-journal"):
        journal = Path(str(path) + suffix)
        _safe_path(journal)
        if journal.exists() and journal.stat().st_size:
            raise HarnessError("DATABASE_NOT_CHECKPOINTED", path.name + suffix)
    db = sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA query_only=ON")
        db.execute("PRAGMA trusted_schema=OFF")
        if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise HarnessError("DATABASE_INVALID", path.name)
        available = {row["name"]: (row["type"], row["sql"])
                     for row in db.execute("SELECT name,type,sql FROM sqlite_master")}
        actual_tables = {name for name, definition in available.items()
                         if definition[0] == "table" and name != "sqlite_sequence"}
        if actual_tables != set(tables):
            raise HarnessError("DATABASE_INVALID", "unsupported table inventory")
        result = {}
        for table, bound in tables.items():
            if not re.fullmatch(r"[a-z_]+", table):
                raise HarnessError("DATABASE_INVALID", "table name")
            definition = available.get(table)
            if (definition is None or definition[0] != "table"
                    or "VIRTUAL TABLE" in (definition[1] or "").upper()):
                raise HarnessError("DATABASE_INVALID", "missing ordinary table: " + table)
            rows = [dict(row) for row in db.execute(
                "SELECT * FROM " + table + " LIMIT ?", (bound + 1,))]
            if len(rows) > bound:
                raise HarnessError("INVALID_RANGE", table)
            result[table] = rows
        return result
    except sqlite3.Error as exc:
        raise HarnessError("DATABASE_INVALID", type(exc).__name__) from exc
    finally:
        db.close()


def _logical_database_hash(path: Path) -> str:
    path = _safe_path(path)
    db = sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)
    try:
        db.execute("PRAGMA query_only=ON")
        result = hashlib.sha256()
        for line in db.iterdump():
            result.update((line + "\n").encode("utf-8"))
        return result.hexdigest()
    finally:
        db.close()


def _metadata(rows: list[dict]) -> dict:
    result = {}
    for row in rows:
        object_fields(row, {"key", "value"}, path="database.metadata")
        key = identifier(row["key"], "database.metadata.key")
        if key in result:
            raise HarnessError("DATABASE_INVALID", "duplicate metadata")
        result[key] = strict_loads(row["value"])
    return result


def _source_state(contract: dict, findings: Findings) -> dict[str, dict]:
    """Replay the original digital obligation history, not producer admission."""
    state = {}
    events = contract["source_events"]
    if type(events) is not list or contract["cutoff_sequence"] != len(events):
        findings.add("SOURCE_INCOMPLETE", unknown=True)
        return state
    for sequence, event in enumerate(events, 1):
        if type(event) is not dict or type(event.get("sequence")) is not int or event["sequence"] != sequence:
            raise HarnessError("SOURCE_HISTORY_INVALID", "sequence")
        kind = event.get("type")
        object_fields(event, {"sequence", "type", "obligation_id"} |
                      ({"obligation"} if kind in ("ACCEPT", "AMEND") else set()), path="source_event")
        oid = identifier(event["obligation_id"], "source_event.obligation_id")
        if kind == "ACCEPT":
            if oid in state:
                raise HarnessError("SOURCE_HISTORY_INVALID", "duplicate original obligation")
        elif kind in ("AMEND", "CANCEL"):
            if oid not in state or state[oid]["status"] != "ACTIVE":
                raise HarnessError("SOURCE_HISTORY_INVALID", "inactive obligation")
        else:
            raise HarnessError("SOURCE_HISTORY_INVALID", "unsupported event")
        if kind == "CANCEL":
            state[oid] = dict(state[oid], status="CANCELLED")
            continue
        item = object_fields(event["obligation"],
                             {"obligation_id", "recipient", "revision", "quantity", "deadline_tick", "status", "spec"},
                             path="source_obligation")
        if item["obligation_id"] != oid or item["status"] != "ACTIVE":
            raise HarnessError("SOURCE_HISTORY_INVALID", "obligation binding")
        if kind == "AMEND" and item["revision"] <= state[oid]["revision"]:
            raise HarnessError("SOURCE_HISTORY_INVALID", "revision did not advance")
        state[oid] = dict(item, spec=dict(item["spec"]))
    if [state[key] for key in sorted(state)] != contract["obligations"]:
        findings.add("SOURCE_OBLIGATION_MISMATCH")
    return state


def _controller(value: Any) -> dict:
    fields = {"schema", "run_id", "contract_sha256", "policies_sha256", "method", "fixture_id",
              "cohort", "state", "started_monotonic_ns", "finished_monotonic_ns", "implementation",
              "isolation", "fault_schedule", "faults_observed", "events", "errors", "target_verdict",
              "resources", "clock_tick", "capacity_databases", "db_snapshots"}
    row = object_fields(value, fields, {"started_utc"}, path="controller")
    if row["schema"] != "continuity-economy/controller/v1":
        raise HarnessError("UNSUPPORTED_VERSION", "controller")
    for name in ("run_id", "method", "fixture_id", "cohort", "target_verdict"):
        identifier(row[name], "controller." + name)
    for name in ("contract_sha256", "policies_sha256"):
        sha256(row[name], "controller." + name)
    if row["state"] not in ("COMPLETE", "INCOMPLETE", "ERROR", "NOT_RUN"):
        raise HarnessError("INVALID_TYPE", "controller.state")
    start = integer(row["started_monotonic_ns"], "controller.started_monotonic_ns", 0, MAX_NS)
    integer(row["finished_monotonic_ns"], "controller.finished_monotonic_ns", start, MAX_NS)
    integer(row["clock_tick"], "controller.clock_tick", 0, 1_000_000_000)
    for name in ("fault_schedule", "faults_observed", "events", "errors", "capacity_databases"):
        if type(row[name]) is not list or len(row[name]) > MAX_ROWS:
            raise HarnessError("INVALID_TYPE", "controller." + name)
    for name in ("implementation", "resources", "db_snapshots", "isolation"):
        if type(row[name]) is not dict:
            raise HarnessError("INVALID_TYPE", "controller." + name)
    previous_tick, previous_ns = 0, start
    for event in row["events"]:
        object_fields(event, {"event", "tick", "monotonic_ns", "detail"}, path="controller.event")
        identifier(event["event"], "controller.event.event")
        tick = integer(event["tick"], "controller.event.tick", previous_tick, row["clock_tick"])
        stamp = integer(event["monotonic_ns"], "controller.event.monotonic_ns", previous_ns, row["finished_monotonic_ns"])
        if type(event["detail"]) is not dict:
            raise HarnessError("INVALID_TYPE", "controller.event.detail")
        previous_tick, previous_ns = tick, stamp
    for path, checksum in row["db_snapshots"].items():
        if type(path) is not str:
            raise HarnessError("UNSAFE_PATH", "controller.db_snapshots")
        sha256(checksum, "controller.db_snapshots")
    return row


def _reference_check(root: Path, authority: Path, expected_pin: str | None,
                     findings: Findings) -> tuple[dict | None, dict | None, dict | None, dict | None]:
    """Load retained inputs; the pin must be obtained outside candidate control."""
    from .schema import validate_contract, validate_policies

    contract = policies = reference = capacity_inputs = None
    try:
        contract = validate_contract(strict_load(authority / "contract.json"))
        policies = validate_policies(strict_load(authority / "policies.json"))
        reference = object_fields(strict_load(authority / "reference.json"),
                                  {"schema", "run_id", "contract_sha256", "policies_sha256",
                                   "source_sha256", "cutoff_sequence", "source_complete", "capacity_inputs_sha256"},
                                  path="reference")
        if reference["schema"] != "continuity-economy/reference/v1":
            raise HarnessError("UNSUPPORTED_VERSION", "reference")
        identifier(reference["run_id"], "reference.run_id")
        for name in ("contract_sha256", "policies_sha256", "source_sha256", "capacity_inputs_sha256"):
            sha256(reference[name], "reference." + name)
        integer(reference["cutoff_sequence"], "reference.cutoff_sequence", 1)
        if type(reference["source_complete"]) is not bool:
            raise HarnessError("INVALID_TYPE", "reference.source_complete")
        capacity_inputs = strict_load(authority / "capacity-inputs.json")
        if type(capacity_inputs) is not dict or len(capacity_inputs) > 256:
            raise HarnessError("INVALID_TYPE", "capacity_inputs")
    except HarnessError as exc:
        findings.add("AUTHORITY_MISSING" if exc.code == "MISSING_FILE" else "AUTHORITY_INVALID",
                     exc.code, unknown=exc.code == "MISSING_FILE")
        return contract, policies, reference, capacity_inputs
    if expected_pin is None:
        findings.add("REFERENCE_PIN_MISSING", unknown=True)
    else:
        try:
            sha256(expected_pin, "expected_reference_sha256")
            if digest(reference) != expected_pin:
                findings.add("REFERENCE_PIN_MISMATCH")
        except HarnessError:
            findings.add("REFERENCE_PIN_MISMATCH", "invalid digest")
    if (reference.get("run_id") != contract["run_id"]
            or reference.get("contract_sha256") != digest(contract)
            or reference.get("policies_sha256") != digest(policies)
            or reference.get("source_sha256") != digest(contract["source_events"])
            or reference.get("cutoff_sequence") != contract["cutoff_sequence"]
            or reference.get("source_complete") != contract["source_complete"]
            or reference.get("capacity_inputs_sha256") != digest(capacity_inputs)):
        findings.add("AUTHORITY_BINDING")
    if not contract["source_complete"]:
        findings.add("SOURCE_INCOMPLETE", unknown=True)
    return contract, policies, reference, capacity_inputs


def _seal_check(root: Path, authority: Path, contract: dict | None,
                controller: dict | None, findings: Findings) -> dict[str, str]:
    hashes = {}
    try:
        seal = object_fields(strict_load(authority / "execution.json"),
                             {"schema", "run_id", "contract_sha256", "controller_sha256", "files"},
                             path="execution_seal")
        if seal["schema"] != "continuity-economy/execution-seal/v1":
            raise HarnessError("UNSUPPORTED_VERSION", "execution_seal")
        if contract and (seal["run_id"] != contract["run_id"]
                         or seal["contract_sha256"] != digest(contract)):
            findings.add("EXECUTION_SEAL_BINDING", "contract")
        if controller and seal["controller_sha256"] != digest(controller):
            findings.add("EXECUTION_SEAL_BINDING", "controller")
        manifest = seal["files"]
        if type(manifest) is not dict or len(manifest) > MAX_EVIDENCE_FILES:
            raise HarnessError("INVALID_TYPE", "evidence_manifest")
        for relative, checksum in manifest.items():
            try:
                sha256(checksum, "evidence_manifest")
                actual = _hash_file(_evidence_path(root, relative))
                hashes[relative] = actual
                if actual != checksum:
                    findings.add("EVIDENCE_CHANGED", relative)
            except HarnessError as exc:
                findings.add("UNSAFE_EVIDENCE_PATH" if exc.code == "UNSAFE_PATH" else "EVIDENCE_MISSING",
                             str(relative), unknown=exc.code == "MISSING_FILE")
        evidence = _safe_path(root / "evidence")
        files = sorted(evidence.rglob("*")) if evidence.is_dir() else []
        if len(files) > MAX_EVIDENCE_FILES * 2:
            raise HarnessError("INVALID_RANGE", "evidence paths")
        for path in files:
            if path.is_symlink():
                findings.add("UNSAFE_EVIDENCE_PATH", str(path.relative_to(root)))
            elif path.is_file() and path.relative_to(root).as_posix() not in manifest:
                findings.add("UNSEALED_EVIDENCE", path.relative_to(root).as_posix())
    except HarnessError as exc:
        findings.add("EXECUTION_SEAL_MISSING" if exc.code == "MISSING_FILE" else "EXECUTION_SEAL_INVALID",
                     exc.code, unknown=exc.code == "MISSING_FILE")
    return hashes


def _observed_clock(observation: Any, controller: dict, deadline_tick: int,
                    wall_deadline_ms: int, findings: Findings, *, obligation_id: str,
                    tick_field: str = "tick", ns_field: str = "monotonic_ns",
                    wall_origin_ns: int | None = None) -> bool:
    """A durable post-transition observation is a conservative completion bound."""
    if type(observation) is not dict or type(observation.get(tick_field)) is not int or type(observation.get(ns_field)) is not int:
        findings.add("ACCEPTANCE_OBSERVATION_MISSING", scope="outcome",
                     obligation_id=obligation_id, unknown=True)
        return False
    tick, stamp = observation[tick_field], observation[ns_field]
    start, end = controller["started_monotonic_ns"], controller["finished_monotonic_ns"]
    if tick < 0 or not start <= stamp <= end:
        findings.add("CLOCK_OUTSIDE_RUN", scope="outcome", obligation_id=obligation_id)
        return False
    origin = start if wall_origin_ns is None else wall_origin_ns
    if tick > deadline_tick or stamp - origin > wall_deadline_ms * 1_000_000:
        findings.add("LATE_ACCEPTANCE", scope="outcome", obligation_id=obligation_id)
        return False
    return True


def _revoked(contract: dict, party_id: str, action: str, tick: int) -> bool:
    """Revocation applies prospectively, including the declared effective tick."""
    return any(event["party_id"] == party_id and event["action"] == action
               and event["tick"] <= tick for event in contract["revocations"])


def _lots(contract: dict) -> dict[str, dict]:
    """Derive permitted work partitions independently of candidate planning."""
    result = {}
    for obligation in contract["obligations"]:
        if obligation["status"] != "ACTIVE":
            continue
        size = contract["lot_size"] if contract["allow_split"] else obligation["quantity"]
        for index, first in enumerate(range(1, obligation["quantity"] + 1, size), 1):
            last = min(first + size - 1, obligation["quantity"])
            lot_id = f"{obligation['obligation_id']}.L{index:03d}"
            result[lot_id] = {
                "lot_id": lot_id, "obligation_id": obligation["obligation_id"],
                "first_unit": first, "last_unit": last, "quantity": last - first + 1,
                "recipient": obligation["recipient"], "revision": obligation["revision"],
                "spec": obligation["spec"], "deadline_tick": obligation["deadline_tick"],
            }
    return result


def _legacy_orders(contract: dict) -> list[dict]:
    """Exact per-attempt capacity obligations for the unchanged v0.1 service."""
    result = []
    for lot in _lots(contract).values():
        for attempt in range(1, contract["max_attempts"] + 1):
            content = {key: lot[key] for key in (
                "obligation_id", "revision", "recipient", "spec", "first_unit", "last_unit")}
            content["attempt"] = attempt
            result.append({
                "order_id": f"{lot['lot_id']}.A{attempt}", "recipient": lot["recipient"],
                "product": "DIGITAL_LABEL_JOB", "spec_sha256": digest(content),
                "quantity": lot["quantity"], "deadline_tick": lot["deadline_tick"],
            })
    return sorted(result, key=lambda item: item["order_id"])


def _inspect_product(raw: bytes, contract: dict) -> dict:
    """Check literal substantive content without importing any generation code.

    Invalid production can be an expected retained rejection.  Consequently this
    returns observations rather than immediately failing the exercise: accepting
    an invalid product is a verification failure; rejecting and correcting it can
    still preserve the final promise, with all attempts and costs counted.
    """
    codes = []
    product = None
    try:
        product = object_fields(strict_loads(raw), PRODUCT_FIELDS, path="product")
        if product["schema"] != PRODUCT_SCHEMA:
            codes.append("UNSUPPORTED_PRODUCT_FORMAT")
        for name in ("run_id", "contract_id", "obligation_id", "recipient", "production_id",
                     "arrangement_id", "provider_id", "delivery_id", "capacity_key", "lot_id"):
            identifier(product[name], "product." + name)
        sha256(product["contract_sha256"], "product.contract_sha256")
        integer(product["revision"], "product.revision", 1)
        attempt = integer(product["attempt"], "product.attempt", 1, contract["max_attempts"])
        first = integer(product["first_unit"], "product.first_unit", 1)
        last = integer(product["last_unit"], "product.last_unit", first)
        if product["supersedes"] is not None:
            identifier(product["supersedes"], "product.supersedes")
        if type(product["labels"]) is not list or len(product["labels"]) > MAX_ROWS:
            raise HarnessError("INVALID_TYPE", "product.labels")
        if (product["run_id"] != contract["run_id"]
                or product["contract_id"] != contract["contract_id"]
                or product["contract_sha256"] != digest(contract)):
            codes.append("PRODUCT_CONTRACT_BINDING")
        obligations = {row["obligation_id"]: row for row in contract["obligations"]}
        order = obligations.get(product["obligation_id"])
        if order is None:
            codes.append("UNKNOWN_OBLIGATION")
        else:
            if order["status"] != "ACTIVE":
                codes.append("CANCELLED_OBLIGATION")
            if product["revision"] != order["revision"]:
                codes.append("STALE_REVISION")
            if product["recipient"] != order["recipient"]:
                codes.append("WRONG_RECIPIENT")
            if last > order["quantity"]:
                codes.append("WRONG_QUANTITY")
            if order["spec"]["format"] != PRODUCT_SCHEMA:
                codes.append("UNSUPPORTED_PRODUCT_FORMAT")
            permitted = {(lot["first_unit"], lot["last_unit"])
                         for lot in _lots(contract).values()
                         if lot["obligation_id"] == order["obligation_id"]}
            if (first, last) not in permitted:
                codes.append("UNAUTHORIZED_PARTITION")
            lot = _lots(contract).get(product["lot_id"])
            if (lot is None or lot["obligation_id"] != order["obligation_id"]
                    or (lot["first_unit"], lot["last_unit"]) != (first, last)):
                codes.append("WRONG_LOT")
        production_id = f"{product['arrangement_id']}.{product['lot_id']}.A{attempt}"
        if (product["production_id"] != production_id or product["capacity_key"] != production_id
                or product["delivery_id"] != production_id + ".D"):
            codes.append("PRODUCT_IDEMPOTENCY_BINDING")
        if len(product["labels"]) != last - first + 1:
            codes.append("WRONG_QUANTITY")
        seen = set()
        for position, label in enumerate(product["labels"], first):
            object_fields(label, LABEL_FIELDS, path="product.label")
            ordinal = integer(label["ordinal"], "label.ordinal", 1)
            if ordinal in seen:
                codes.append("DUPLICATE_UNIT")
            seen.add(ordinal)
            if ordinal != position or not first <= ordinal <= last:
                codes.append("UNIT_SEQUENCE")
            if any(type(label[key]) is not str for key in LABEL_FIELDS - {"ordinal"}):
                raise HarnessError("INVALID_TYPE", "label.text")
            if order is not None:
                if label["serial"] != order["spec"]["serial_prefix"] + format(ordinal, "06d"):
                    codes.append("WRONG_SERIAL")
                if any(label[key] != order["spec"][key] for key in LITERAL_FIELDS):
                    codes.append("WRONG_CONTENT")
    except HarnessError as exc:
        codes.append("PRODUCT_INVALID")
        codes.append(exc.code)
    return {"valid": not codes, "codes": sorted(set(codes)), "product": product,
            "content_sha256": hashlib.sha256(raw).hexdigest(), "byte_count": len(raw)}


CAPACITY_ORDER_FIELDS = {"order_id", "recipient", "product", "spec_sha256", "quantity", "deadline_tick"}
RESERVATION_FIELDS = {
    "key", "run_id", "contract_sha256", "order_id", "recipient", "product", "spec_sha256", "quantity",
    "route", "window_start", "window_end", "expires_tick", "status", "request_sha256", "created_tick", "updated_tick",
}
LIVE = {"RESERVED", "COMMITTED", "FULFILLED"}
CAPACITY_TABLES = {"metadata": 64, "routes": 2, "authorized_orders": 64, "orders": 128,
                   "reservations": MAX_ROWS, "receipts": MAX_ROWS, "history": MAX_ROWS}


def _capacity_source(events: list[dict], cutoff: int) -> list[dict]:
    """Independent replay of the unchanged service's retained recovery journal."""
    if type(events) is not list or type(cutoff) is not int or cutoff != len(events) or not events:
        raise HarnessError("CAPACITY_SOURCE_INCOMPLETE", "cutoff")
    state = {}
    for sequence, event in enumerate(events, 1):
        if type(event) is not dict or type(event.get("sequence")) is not int or event["sequence"] != sequence:
            raise HarnessError("CAPACITY_SOURCE_INVALID", "sequence")
        kind = event.get("type")
        required = {"sequence", "type", "order_id"}
        if kind == "ACCEPT":
            required |= CAPACITY_ORDER_FIELDS
        elif kind == "FULFILL":
            required.add("quantity")
        object_fields(event, required, CAPACITY_ORDER_FIELDS - {"order_id"} if kind == "AMEND" else set(),
                      path="capacity_source")
        oid = identifier(event["order_id"], "capacity_source.order_id")
        if kind == "ACCEPT":
            if oid in state:
                raise HarnessError("CAPACITY_SOURCE_INVALID", "duplicate acceptance")
            item = {key: event[key] for key in CAPACITY_ORDER_FIELDS}
            state[oid] = dict(item, fulfilled=0, state="ACTIVE", source_sequence=sequence)
        elif kind in ("AMEND", "FULFILL", "CANCEL"):
            if oid not in state or state[oid]["state"] != "ACTIVE":
                raise HarnessError("CAPACITY_SOURCE_INVALID", "inactive source order")
            item = dict(state[oid], source_sequence=sequence)
            if kind == "CANCEL":
                item["state"] = "CANCELLED"
            elif kind == "AMEND":
                if set(event) == {"sequence", "type", "order_id"}:
                    raise HarnessError("CAPACITY_SOURCE_INVALID", "empty amendment")
                item.update({key: event[key] for key in CAPACITY_ORDER_FIELDS - {"order_id"} if key in event})
            else:
                item["fulfilled"] += integer(event["quantity"], "capacity_source.fulfilled", 1)
            if item["fulfilled"] > item["quantity"]:
                raise HarnessError("CAPACITY_SOURCE_INVALID", "overfulfillment")
            if item["fulfilled"] == item["quantity"] and item["state"] == "ACTIVE":
                item["state"] = "FULFILLED"
            state[oid] = item
        else:
            raise HarnessError("CAPACITY_SOURCE_INVALID", "kind")
        current = state[oid]
        for name in ("order_id", "recipient", "product"):
            identifier(current[name], "capacity_source." + name)
        sha256(current["spec_sha256"], "capacity_source.spec_sha256")
        integer(current["quantity"], "capacity_source.quantity", 1)
        integer(current["deadline_tick"], "capacity_source.deadline_tick", 1)
    return [state[key] for key in sorted(state)]


def _load_at(rows: list[dict], route: str, tick: int) -> int:
    deltas = {}
    for row in rows:
        if row["route"] != route or row["status"] not in LIVE or row["window_end"] <= tick:
            continue
        start, end = max(tick, row["window_start"]), row["window_end"]
        deltas[start] = deltas.get(start, 0) + row["quantity"]
        deltas[end] = deltas.get(end, 0) - row["quantity"]
    load = maximum = 0
    for stamp in sorted(deltas):
        load += deltas[stamp]
        maximum = max(maximum, load)
    return maximum


def _capacity_row(row: dict, contract: dict, provider: dict, window: dict, expected: dict,
                  findings: Findings) -> dict:
    object_fields(row, RESERVATION_FIELDS, path="capacity.reservation")
    for name in ("key", "run_id", "order_id", "recipient", "product"):
        identifier(row[name], "capacity.reservation." + name)
    for name in ("contract_sha256", "spec_sha256", "request_sha256"):
        sha256(row[name], "capacity.reservation." + name)
    for name in ("quantity", "window_start", "window_end", "expires_tick", "created_tick", "updated_tick"):
        integer(row[name], "capacity.reservation." + name, 1 if name == "quantity" else 0)
    order = expected.get(row["order_id"])
    route = "primary" if provider["role"] == "primary" else "backup"
    if (row["run_id"] != contract["run_id"] or row["contract_sha256"] != digest(contract)
            or order is None or any(row[key] != order[key] for key in CAPACITY_ORDER_FIELDS - {"deadline_tick"})):
        findings.add("CAPACITY_OBLIGATION_BINDING", row["key"], scope="safety")
    if row["route"] != route or row["status"] not in LIVE | {"RELEASED", "EXPIRED"}:
        findings.add("CAPACITY_ROUTE_BINDING", row["key"], scope="safety")
    if not window["start"] <= row["window_start"] < row["window_end"] <= window["end"]:
        findings.add("CAPACITY_WINDOW_BINDING", row["key"], scope="safety")
    if not row["created_tick"] < row["expires_tick"] <= row["window_end"] or row["updated_tick"] < row["created_tick"]:
        findings.add("CAPACITY_CLOCK_BINDING", row["key"], scope="safety")
    request = {key: row[key] for key in RESERVATION_FIELDS - {"status", "request_sha256", "created_tick", "updated_tick"}}
    if digest(request) != row["request_sha256"]:
        findings.add("CAPACITY_IDEMPOTENCY_BINDING", row["key"], scope="safety")
    return row


def _capacity_database(root: Path, contract: dict, provider: dict, window: dict,
                       retained: dict, controller: dict, findings: Findings) -> dict:
    """Replay each actual v0.1 capacity ledger, including unused/released work."""
    pid, wid = provider["provider_id"], window["window_id"]
    relative = f"evidence/capacity/{pid}.{wid}.sqlite"
    tables = _database(_evidence_path(root, relative), CAPACITY_TABLES)
    metadata = _metadata(tables["metadata"])
    object_fields(retained, {"provider_id", "window_id", "route", "init", "journal", "cutoff"}, path="capacity_inputs")
    route = "primary" if provider["role"] == "primary" else "backup"
    expected_list = _legacy_orders(contract)
    expected = {row["order_id"]: row for row in expected_list}
    capacities = {"primary": window["capacity"] if route == "primary" else 0,
                  "backup": window["capacity"] if route == "backup" else 0}
    source = _capacity_source(retained["journal"], retained["cutoff"])
    source_active = sorted([{key: row[key] for key in CAPACITY_ORDER_FIELDS} |
                            {"quantity": row["quantity"] - row["fulfilled"]}
                            for row in source if row["state"] == "ACTIVE" and row["quantity"] > row["fulfilled"]],
                           key=lambda item: item["order_id"])
    init = object_fields(retained["init"], {"run_id", "contract_sha256", "capacities", "allowed_orders",
                                           "snapshot", "window_start", "window_end", "source_sha256"}, path="capacity_init")
    if (retained["provider_id"] != pid or retained["window_id"] != wid or retained["route"] != route
            or init["run_id"] != contract["run_id"] or init["contract_sha256"] != digest(contract)
            or init["capacities"] != capacities or init["allowed_orders"] != expected_list
            or init["window_start"] != window["start"] or init["window_end"] != window["end"]
            or init["source_sha256"] != digest(retained["journal"]) or source_active != expected_list):
        findings.add("CAPACITY_AUTHORITY_BINDING", pid + "." + wid, scope="integrity")
    if (metadata.get("schema") != "continuity-harness/service/v1"
            or metadata.get("run_id") != contract["run_id"] or metadata.get("contract_sha256") != digest(contract)
            or metadata.get("init_sha256") != digest(init)
            or metadata.get("source_sha256") != digest(retained["journal"])
            or metadata.get("window_start") != window["start"] or metadata.get("window_end") != window["end"]):
        findings.add("CAPACITY_DATABASE_BINDING", pid + "." + wid, scope="integrity")
    if sorted(tables["authorized_orders"], key=lambda row: row["order_id"]) != expected_list:
        findings.add("CAPACITY_OBLIGATIONS_CHANGED", pid + "." + wid, scope="integrity")
    current, final = {}, {}
    for raw in tables["reservations"]:
        row = _capacity_row(raw, contract, provider, window, expected, findings)
        if row["key"] in final:
            findings.add("CAPACITY_HISTORY_INVALID", "duplicate reservation", scope="safety")
        final[row["key"]] = row
    available = {"primary": True, "backup": True}
    peak = {"primary": 0, "backup": 0}
    initialized = restored = False
    previous_tick = 0
    history = sorted(tables["history"], key=lambda row: row["sequence"])
    for index, event in enumerate(history, 1):
        object_fields(event, {"sequence", "operation", "key", "order_id", "route", "tick", "monotonic_ns", "detail"}, path="capacity.history")
        if integer(event["sequence"], "capacity.history.sequence", 1) != index:
            findings.add("CAPACITY_HISTORY_INVALID", "sequence", scope="safety")
        tick = integer(event["tick"], "capacity.history.tick", previous_tick)
        stamp = integer(event["monotonic_ns"], "capacity.history.monotonic_ns", 0, MAX_NS)
        if not controller["started_monotonic_ns"] <= stamp <= controller["finished_monotonic_ns"]:
            findings.add("CLOCK_OUTSIDE_RUN", "capacity", scope="safety")
        previous_tick = tick
        detail = strict_loads(event["detail"])
        if type(detail) is not dict:
            raise HarnessError("CAPACITY_HISTORY_INVALID", "detail")
        op = event["operation"]
        if op == "INIT":
            if (initialized or index != 1 or detail.get("capacities") != capacities
                    or detail.get("window_start") != window["start"] or detail.get("window_end") != window["end"]
                    or detail.get("allowed_orders_sha256") != digest(expected_list)):
                findings.add("CAPACITY_HISTORY_INVALID", "initialization", scope="safety")
            initialized = True
        elif not initialized:
            findings.add("CAPACITY_HISTORY_INVALID", "missing initialization", scope="safety")
        elif op == "RESTORED":
            restored = detail.get("source_sha256") == digest(retained["journal"]) and detail.get("cutoff") == retained["cutoff"]
            if not restored:
                findings.add("PRIMARY_RECOVERY_INVALID", pid, scope="safety")
        elif op == "CAPACITY_CHANGED":
            changed_route = event["route"]
            if changed_route not in capacities:
                raise HarnessError("CAPACITY_HISTORY_INVALID", "capacity route")
            value = integer(detail.get("capacity"), "capacity.change", 0)
            if detail.get("previous_capacity") != capacities[changed_route] or value > init["capacities"][changed_route]:
                findings.add("CAPACITY_AUTHORITY_CHANGED", pid, scope="safety")
            capacities[changed_route] = value
        elif op == "ROUTE_DISABLED":
            if event["route"] not in available or detail.get("available") is not False:
                raise HarnessError("CAPACITY_HISTORY_INVALID", "withdrawal")
            available[event["route"]] = False
        elif op in LIVE | {"RELEASED", "EXPIRED"}:
            row = _capacity_row(detail.get("reservation"), contract, provider, window, expected, findings)
            old = current.get(row["key"])
            if (row["status"] != op or event["key"] != row["key"] or event["order_id"] != row["order_id"]
                    or event["route"] != row["route"] or row["updated_tick"] != tick):
                findings.add("CAPACITY_HISTORY_INVALID", "transition binding", scope="safety")
            if old is None:
                if op != "RESERVED" or row["created_tick"] != tick or row["expires_tick"] <= tick:
                    findings.add("CAPACITY_ILLEGAL_TRANSITION", row["key"], scope="safety")
            else:
                legal = {"RESERVED": {"COMMITTED", "RELEASED", "EXPIRED"}, "COMMITTED": {"FULFILLED", "RELEASED"},
                         "FULFILLED": set(), "RELEASED": set(), "EXPIRED": set()}
                if (op not in legal[old["status"]]
                        or any(row[key] != old[key] for key in RESERVATION_FIELDS - {"status", "updated_tick"})
                        or (old["status"] == "RESERVED" and op != "EXPIRED" and tick >= old["expires_tick"])):
                    findings.add("CAPACITY_ILLEGAL_TRANSITION", row["key"], scope="safety")
            if op == "EXPIRED" and tick < row["expires_tick"]:
                findings.add("CAPACITY_ILLEGAL_TRANSITION", "early expiry", scope="safety")
            if op in LIVE:
                if not available[row["route"]]:
                    findings.add("WITHDRAWN_CAPACITY_USED", row["key"], scope="safety")
                if provider["dependency"] in contract["blocked_dependencies"]:
                    findings.add("FAILED_DEPENDENCY_USED", row["key"], scope="safety")
                if not provider["permissions"]["production"] or _revoked(contract, pid, "produce", tick):
                    findings.add("PRODUCTION_PERMISSION_MISSING", row["key"], scope="safety")
                if row["route"] == "primary" and not restored:
                    findings.add("PRIMARY_NOT_RECOVERED", row["key"], scope="safety")
            if op in {"COMMITTED", "FULFILLED"} and tick > min(expected[row["order_id"]]["deadline_tick"], row["window_end"]):
                findings.add("CAPACITY_LATE_EFFECT", row["key"], scope="safety")
            if op == "FULFILLED" and tick < row["window_start"]:
                findings.add("CAPACITY_EARLY_EFFECT", row["key"], scope="safety")
            current[row["key"]] = row
        else:
            findings.add("CAPACITY_HISTORY_INVALID", str(op), scope="safety")
        live_orders = [row["order_id"] for row in current.values() if row["status"] in LIVE]
        if len(live_orders) != len(set(live_orders)):
            findings.add("CAPACITY_DUPLICATE_OBLIGATION", pid, scope="safety")
        for resource in capacities:
            load = _load_at(list(current.values()), resource, tick)
            peak[resource] = max(peak[resource], load)
            if load > capacities[resource]:
                findings.add("CAPACITY_EXCEEDED", pid + "." + wid, scope="safety")
    if not initialized or current != final or metadata.get("last_tick", -1) < previous_tick:
        findings.add("CAPACITY_HISTORY_INVALID", "final state", scope="safety")
    final_routes = [{"route": key, "capacity": capacities[key], "available": int(available[key])} for key in sorted(capacities)]
    if sorted(tables["routes"], key=lambda row: row["route"]) != final_routes:
        findings.add("CAPACITY_HISTORY_INVALID", "route final state", scope="safety")
    if restored and (sorted(tables["orders"], key=lambda row: row["order_id"]) != source
                     or metadata.get("recovery_cutoff") != retained["cutoff"]
                     or metadata.get("recovery_source_sha256") != digest(retained["journal"])):
        findings.add("PRIMARY_RECOVERY_INVALID", "final source rows", scope="safety")
    receipts = {}
    for raw in tables["receipts"]:
        object_fields(raw, {"key", "order_id", "payload", "sha256", "completed_tick", "completed_monotonic_ns"}, path="capacity.receipt")
        payload = strict_loads(raw["payload"])
        allocation = final.get(raw["key"])
        if (type(payload) is not dict or allocation is None or allocation["status"] != "FULFILLED"
                or raw["order_id"] != allocation["order_id"]
                or any(payload.get(key) != allocation[key] for key in (
                    "run_id", "contract_sha256", "order_id", "recipient", "product", "spec_sha256", "quantity", "route", "key"))
                or payload.get("state") != "COMPLETED" or payload.get("completed_tick") != raw["completed_tick"]
                or payload.get("completed_monotonic_ns") != raw["completed_monotonic_ns"]
                or raw["completed_tick"] != allocation["updated_tick"]
                or raw["sha256"] != hashlib.sha256(canonical(payload) + b"\n").hexdigest()):
            findings.add("CAPACITY_RECEIPT_MISMATCH", raw["key"], scope="safety")
        if raw["key"] in receipts:
            findings.add("CAPACITY_DUPLICATE_RECEIPT", raw["key"], scope="safety")
        artifact_path = _evidence_path(root, f"evidence/capacity-artifacts/{pid}.{wid}/{raw['order_id']}.json")
        try:
            if read_bytes(artifact_path) != canonical(payload) + b"\n":
                findings.add("CAPACITY_ARTIFACT_CHANGED", raw["key"], scope="integrity")
        except HarnessError as exc:
            findings.add("CAPACITY_ARTIFACT_MISSING", raw["key"], scope="integrity", unknown=exc.code == "MISSING_FILE")
        receipts[raw["key"]] = payload
    if {key for key, row in final.items() if row["status"] == "FULFILLED"} != set(receipts):
        findings.add("CAPACITY_RECEIPT_MISSING", pid + "." + wid, scope="integrity", unknown=True)
    return {"provider_id": pid, "window_id": wid, "path": relative, "reservations": final,
            "receipts": receipts, "history": history, "peak": peak, "primary_recovered": restored}


PARTICIPANT_TABLES = {
    "metadata": 64, "policy_versions": 64, "proposals": 256, "decisions": 2048,
    "agreements": 256, "accounts": 128, "holds": 4096, "entries": 16384,
    "productions": 4096, "authorizations": 16384, "events": 16384,
}


def _proposal_terms(contract: dict, policies: dict, proposal: dict) -> dict:
    """Recompute modeled terms without calling the participant's pricing code."""
    from .policy_schema import validate_proposal_shape

    validate_proposal_shape(proposal)
    if proposal["contract_sha256"] != digest(contract):
        raise HarnessError("PROPOSAL_CONTRACT_BINDING")
    if proposal["cancellation_fee_minor"] > proposal["buyer_price_minor"]:
        raise HarnessError("PROPOSAL_CANCELLATION_BINDING")
    lots = _lots(contract)
    providers = {row["provider_id"]: row for row in contract["providers"]}
    provider_policies = {row["party_id"]: row for row in policies["providers"]}
    if set(providers) != set(provider_policies):
        raise HarnessError("POLICY_PROVIDER_BINDING")
    assignments, usage, units, payments = {}, {}, {}, {}
    for allocation in proposal["allocations"]:
        lid, pid, wid = allocation["lot_id"], allocation["provider_id"], allocation["window_id"]
        expected = lots.get(lid)
        if expected is None or lid in assignments or pid not in providers:
            raise HarnessError("PROPOSAL_COVERAGE", lid)
        if any(allocation[key] != expected[key] for key in ("obligation_id", "first_unit", "last_unit")):
            raise HarnessError("PROPOSAL_COVERAGE", lid)
        windows = {row["window_id"]: row for row in providers[pid]["windows"]}
        if wid not in windows or windows[wid]["start"] > expected["deadline_tick"]:
            raise HarnessError("PROPOSAL_CAPACITY", lid)
        assignments[lid] = allocation
        key = (pid, wid)
        usage[key] = usage.get(key, 0) + expected["quantity"]
        units[pid] = units.get(pid, 0) + expected["quantity"]
        payments[pid] = payments.get(pid, 0) + allocation["pay_minor"]
        if usage[key] > windows[wid]["capacity"]:
            raise HarnessError("PROPOSAL_CAPACITY", lid)
    if set(assignments) != set(lots):
        raise HarnessError("PROPOSAL_COVERAGE", "incomplete promise")
    provider_rows = []
    for pid in sorted(units):
        policy = provider_policies[pid]
        base = policy["setup_cost_minor"] + units[pid] * policy["unit_cost_minor"]
        correction = (policy["rework_setup_cost_minor"] + units[pid] * policy["rework_unit_cost_minor"]
                      if contract["max_attempts"] == 2 else 0)
        participation = max(policy["min_profit_minor"], policy["outside_profit_minor"])
        provider_rows.append({
            "party_id": pid, "units": units[pid], "promised_payment_minor": payments[pid],
            "base_cost_minor": base, "rework_cost_minor": correction,
            "maximum_unpaid_cost_exposure_minor": base + correction,
            "participation_profit_minor": participation,
            "minimum_payment_minor": base + correction + participation,
            "guaranteed_profit_minor": payments[pid] - base - correction,
        })
    coordinator, buyer = policies["coordinator"], policies["buyer"]
    coordinator_floor = coordinator["operating_cost_minor"] + max(coordinator["min_profit_minor"], coordinator["outside_profit_minor"])
    minimum = sum(row["minimum_payment_minor"] for row in provider_rows) + coordinator_floor
    return {
        "currency": "SMU", "providers": provider_rows,
        "minimum_coordinator_fee_minor": coordinator_floor, "minimum_buyer_price_minor": minimum,
        "rework_budget_minor": sum(row["rework_cost_minor"] for row in provider_rows),
        "buyer_definite_max_price_minor": min(buyer["max_price_minor"], buyer["value_min_minor"] - buyer["outside_utility_minor"]),
        "buyer_possible_max_price_minor": min(buyer["max_price_minor"], buyer["value_max_minor"] - buyer["outside_utility_minor"]),
        "break_even_value_minor": minimum + buyer["outside_utility_minor"],
        "scope": "AUTHORED_SYNTHETIC_MODEL",
    }


def _party(policies: dict, party_id: str) -> tuple[dict, str]:
    for role in ("buyer", "coordinator", "technical_sponsor"):
        if policies[role]["party_id"] == party_id:
            return policies[role], role
    for row in policies["providers"]:
        if row["party_id"] == party_id:
            return row, "provider"
    raise HarnessError("UNKNOWN_PARTICIPANT", party_id)


def _has_consent(contract: dict, policies: dict, party_id: str, action: str, tick: int) -> bool:
    policy, role = _party(policies, party_id)
    if role == "technical_sponsor":
        return policy["authorized"]
    return (tick < policy["consent_until_tick"]
            and not _revoked(contract, party_id, action, tick)
            and not _revoked(contract, party_id, "consent", tick))


def _decision_expected(contract: dict, policies: dict, proposal: dict, quote: dict,
                       tick: int, free: dict[str, int], prior_committed: bool) -> list[dict]:
    """Separate implementation of each participant's authored outside option."""
    global_code = None
    if proposal["policy_revision"] != policies["revision"]:
        global_code = "POLICY_REVISION_MISMATCH"
    elif tick >= proposal["expires_tick"]:
        global_code = "PROPOSAL_EXPIRED"
    elif proposal["buyer_price_minor"] != sum(row["pay_minor"] for row in proposal["allocations"]) + proposal["coordinator_fee_minor"]:
        global_code = "PRICE_NOT_BALANCED"
    elif proposal["rework_budget_minor"] != quote["rework_budget_minor"]:
        global_code = "REWORK_BUDGET_MISMATCH"
    elif prior_committed:
        global_code = "CONTRACT_ALREADY_COMMITTED"
    quoted = {row["party_id"]: row for row in quote["providers"]}
    parties = [(policies["buyer"], "buyer")]
    parties += [(row, "provider") for row in policies["providers"] if row["party_id"] in quoted]
    parties += [(policies["coordinator"], "coordinator")]
    result = []
    for policy, role in parties:
        pid, verdict, code = policy["party_id"], "ACCEPTED", global_code or "ACCEPTED"
        if global_code is None:
            actions = {"consent", "produce", "transfer"} if role == "provider" else {"consent", "accept"} if role == "buyer" else {"consent"}
            if any(not _has_consent(contract, policies, pid, action, tick) for action in actions):
                code = "CONSENT_REVOKED"
            elif role == "buyer":
                price = proposal["buyer_price_minor"]
                if price > policy["max_price_minor"] or policy["value_max_minor"] - price < policy["outside_utility_minor"]:
                    code = "BUYER_OUTSIDE_OPTION"
                elif policy["value_min_minor"] - price < policy["outside_utility_minor"]:
                    code, verdict = "UNCERTAIN_BUYER_VALUE", "NOT_ESTABLISHED"
                elif free[pid] < price:
                    code = "INSUFFICIENT_FUNDS"
            elif role == "provider":
                row = quoted[pid]
                provider = next(item for item in contract["providers"] if item["provider_id"] == pid)
                if not provider["permissions"]["production"] or (provider["role"] != "primary" and not provider["permissions"]["disclosure"]):
                    code = "ACTION_NOT_ALLOWED"
                elif row["promised_payment_minor"] < row["minimum_payment_minor"]:
                    code = "PROVIDER_PARTICIPATION"
                elif row["maximum_unpaid_cost_exposure_minor"] > policy["liability_limit_minor"]:
                    code = "LIABILITY_LIMIT"
                elif free[pid] < row["base_cost_minor"] + row["rework_cost_minor"]:
                    code = "INSUFFICIENT_FUNDS"
            else:
                if proposal["coordinator_fee_minor"] < quote["minimum_coordinator_fee_minor"]:
                    code = "COORDINATOR_PARTICIPATION"
                elif policy["operating_cost_minor"] > policy["liability_limit_minor"]:
                    code = "LIABILITY_LIMIT"
                elif free[pid] < policy["operating_cost_minor"]:
                    code = "INSUFFICIENT_FUNDS"
        if code != "ACCEPTED" and verdict != "NOT_ESTABLISHED":
            verdict = "REJECTED"
        result.append({"party_id": pid, "role": role, "verdict": verdict, "code": code})
    return result


def _sequences(rows: list[dict], name: str) -> list[dict]:
    ordered = sorted(rows, key=lambda row: row["sequence"])
    for index, row in enumerate(ordered, 1):
        if type(row["sequence"]) is not int or row["sequence"] != index:
            raise HarnessError("HISTORY_SEQUENCE_INVALID", name)
    return ordered


def _policy_at(versions: dict[int, dict], tick: int) -> dict:
    choices = [row for row in versions.values() if row["effective_tick"] <= tick]
    if not choices:
        raise HarnessError("POLICY_EVIDENCE_MISSING")
    return max(choices, key=lambda row: (row["effective_tick"], row["revision"]))["payload"]


def _agreement_open(agreement: dict, tick: int) -> bool:
    return (agreement["accepted_tick"] <= tick
            and (agreement["cancelled_tick"] is None or tick < agreement["cancelled_tick"])
            and (agreement["settled_tick"] is None or tick < agreement["settled_tick"]))


def _authorization_expected(contract: dict, versions: dict, proposals: dict, agreement: dict,
                            party_id: str, action: str, tick: int) -> str:
    if not _agreement_open(agreement, tick):
        return "AGREEMENT_CLOSED"
    proposal = proposals[agreement["proposal_id"]]["payload"]
    if tick >= proposal["expires_tick"] or tick > contract["deadline_tick"]:
        return "PROPOSAL_EXPIRED"
    policies = _policy_at(versions, tick)
    selected = {row["provider_id"] for row in proposal["allocations"]}
    buyer, coordinator = policies["buyer"]["party_id"], policies["coordinator"]["party_id"]
    allowed = {"produce": selected, "transfer": selected | {coordinator}, "accept": {buyer},
               "consent": selected | {buyer, coordinator}}
    if action not in allowed or party_id not in allowed[action]:
        return "ACTION_NOT_ALLOWED"
    required = {party_id} | ({buyer, coordinator} if action in {"produce", "transfer"} else set())
    if any(not _has_consent(contract, policies, pid, action, tick) for pid in required):
        return "CONSENT_REVOKED"
    cp = next((row for row in contract["providers"] if row["provider_id"] == party_id), None)
    if cp and action in {"produce", "transfer"}:
        if not cp["permissions"]["production"] or (action == "transfer" and cp["role"] != "primary" and not cp["permissions"]["disclosure"]):
            return "ACTION_NOT_ALLOWED"
    if agreement["kind"] == "TECHNICAL":
        if not policies["technical_sponsor"]["authorized"]:
            return "TECHNICAL_CONTROL_FORBIDDEN"
        for pid in required - {buyer}:
            if not _party(policies, pid)[0].get("technical_control_allowed", False):
                return "TECHNICAL_CONTROL_FORBIDDEN"
    return "AUTHORIZED"


def _money_replay(tables: dict, policies: dict, agreements: dict, findings: Findings) -> dict:
    """Rebuild balances and encumbrances from every immutable ledger entry."""
    initial = {}
    roles = {}
    for role in ("buyer", "coordinator", "technical_sponsor"):
        party = policies[role]
        initial[party["party_id"]] = party["balance_minor"]
        roles[party["party_id"]] = role
    for party in policies["providers"]:
        initial[party["party_id"]] = party["balance_minor"]
        roles[party["party_id"]] = "provider"
    initial.update(COST_SINK=0, OUTSIDE_ACCOUNT=0)
    roles.update(COST_SINK="modeled_cost_sink", OUTSIDE_ACCOUNT="modeled_withdrawal_destination")
    balances, held, holds = dict(initial), dict.fromkeys(initial, 0), {}
    entries = _sequences(tables["entries"], "entries")
    free_before_tick, free_before_agreement = {}, {}
    seen_ids = set()
    money_kinds = {"BASE_COST", "REWORK_COST", "COORDINATION_COST", "PROVIDER_PAYMENT",
                   "COORDINATOR_PAYMENT", "CANCELLATION_PAYMENT", "WITHDRAWAL"}
    previous_tick = 0
    for entry in entries:
        object_fields(entry, {"sequence", "entry_id", "agreement_id", "kind", "from_party", "to_party",
                              "amount_minor", "hold_kind", "tick", "detail"}, path="financial.entry")
        eid = identifier(entry["entry_id"], "financial.entry_id")
        if eid in seen_ids:
            findings.add("DUPLICATE_FINANCIAL_EFFECT", eid, scope="safety")
        seen_ids.add(eid)
        tick = integer(entry["tick"], "financial.tick", previous_tick)
        previous_tick = tick
        free_before_tick.setdefault(tick, {pid: balances[pid] - held[pid] for pid in balances})
        amount = integer(entry["amount_minor"], "financial.amount_minor", 0)
        aid, src, dst, kind = entry["agreement_id"], entry["from_party"], entry["to_party"], entry["kind"]
        if type(entry["detail"]) is not dict or src not in balances:
            raise HarnessError("FINANCIAL_ENTRY_INVALID", eid)
        if aid is not None and aid not in agreements:
            findings.add("FINANCIAL_AGREEMENT_MISSING", eid, scope="safety")
        if kind != "WITHDRAWAL" and aid is None:
            findings.add("FINANCIAL_AGREEMENT_MISSING", eid, scope="safety")
        if kind in {"HOLD", "RELEASE"}:
            if dst is not None or type(entry["hold_kind"]) is not str:
                raise HarnessError("FINANCIAL_ENTRY_INVALID", eid)
            hid = digest({"agreement_id": aid, "party_id": src, "kind": entry["hold_kind"]})
            if kind == "HOLD":
                if aid not in free_before_agreement:
                    free_before_agreement[aid] = {pid: balances[pid] - held[pid] for pid in balances}
                if hid in holds or eid != "hold." + hid or balances[src] - held[src] < amount:
                    findings.add("FUNDING_HOLD_INVALID", eid, scope="safety")
                holds[hid] = {"hold_id": hid, "agreement_id": aid, "party_id": src, "kind": entry["hold_kind"],
                              "amount_minor": amount, "initial_minor": amount, "created_tick": tick, "closed_tick": None}
                held[src] += amount
            else:
                old = holds.get(hid)
                if old is None or eid != "release." + hid or old["closed_tick"] is not None or old["amount_minor"] != amount:
                    findings.add("FUNDING_RELEASE_INVALID", eid, scope="safety")
                if old is not None:
                    held[src] -= old["amount_minor"]
                    old.update(amount_minor=0, closed_tick=tick)
        elif kind in money_kinds:
            if dst not in balances:
                raise HarnessError("FINANCIAL_ENTRY_INVALID", eid)
            if balances[src] < amount:
                findings.add("INSUFFICIENT_MODELED_FUNDS", eid, scope="safety")
            if entry["hold_kind"] is not None:
                hid = digest({"agreement_id": aid, "party_id": src, "kind": entry["hold_kind"]})
                hold = holds.get(hid)
                if hold is None or hold["closed_tick"] is not None or hold["amount_minor"] < amount:
                    findings.add("UNFUNDED_MODELED_TRANSFER", eid, scope="safety")
                if hold is not None:
                    hold["amount_minor"] -= amount
                    held[src] -= amount
            elif balances[src] - held[src] < amount:
                findings.add("ENCUMBERED_FUNDS_SPENT", eid, scope="safety")
            balances[src] -= amount
            balances[dst] += amount
        else:
            findings.add("UNKNOWN_FINANCIAL_EFFECT", str(kind), scope="safety")
        if sum(balances.values()) != sum(initial.values()) or any(balances[pid] < held[pid] or held[pid] < 0 for pid in balances):
            findings.add("MODELED_FUNDS_NOT_CONSERVED", eid, scope="safety")
    actual_accounts = {}
    for row in tables["accounts"]:
        object_fields(row, {"party_id", "role", "balance_minor", "initial_balance_minor"}, path="financial.account")
        pid = identifier(row["party_id"], "financial.account.party_id")
        integer(row["balance_minor"], "financial.account.balance_minor", 0, MAX_NS)
        integer(row["initial_balance_minor"], "financial.account.initial_balance_minor", 0, MAX_NS)
        if pid in actual_accounts:
            findings.add("DUPLICATE_FINANCIAL_ACCOUNT", pid, scope="safety")
        actual_accounts[pid] = row
    expected_accounts = {pid: {"party_id": pid, "role": roles[pid], "balance_minor": balance,
                               "initial_balance_minor": initial[pid]} for pid, balance in balances.items()}
    if actual_accounts != expected_accounts:
        findings.add("FINANCIAL_BALANCE_MISMATCH", scope="safety")
    if {row["hold_id"]: row for row in tables["holds"]} != holds or len(holds) != len(tables["holds"]):
        findings.add("FINANCIAL_HOLD_HISTORY_MISMATCH", scope="safety")
    return {"initial": initial, "balances": balances, "held": held, "holds": holds, "entries": entries,
            "free_before_tick": free_before_tick, "free_before_agreement": free_before_agreement,
            "final_free": {pid: balances[pid] - held[pid] for pid in balances}, "roles": roles}


def _free_at_decision(money: dict, tick: int, agreement_id: str | None) -> dict:
    if agreement_id in money["free_before_agreement"]:
        return money["free_before_agreement"][agreement_id]
    following = [stamp for stamp in money["free_before_tick"] if stamp >= tick]
    return money["free_before_tick"][min(following)] if following else money["final_free"]


def _participants_data(root: Path, contract: dict, original: dict, findings: Findings) -> dict:
    from .policy_schema import validate_policies, validate_proposal_shape

    tables = _database(root / "evidence/participants.sqlite", PARTICIPANT_TABLES)
    metadata = _metadata(tables["metadata"])
    if (metadata.get("schema") != "continuity-economy/participants/v1"
            or metadata.get("run_id") != contract["run_id"]
            or metadata.get("contract_sha256") != digest(contract)
            or metadata.get("initial_policy_sha256") != digest(original)):
        findings.add("PARTICIPANT_DATABASE_BINDING")
    decoded_fields = {"policy_versions": ("payload",), "proposals": ("payload",), "decisions": ("detail",),
                      "agreements": ("pricing", "acceptance_ids"), "entries": ("detail",), "events": ("payload",)}
    for table, fields in decoded_fields.items():
        for row in tables[table]:
            for field in fields:
                if row[field] is not None:
                    row[field] = strict_loads(row[field])
    versions = {}
    initial_ids = {original[role]["party_id"]: original[role]["balance_minor"] for role in ("buyer", "coordinator", "technical_sponsor")}
    initial_ids.update({row["party_id"]: row["balance_minor"] for row in original["providers"]})
    previous_revision = original["revision"] - 1
    previous_tick = 0
    for row in sorted(tables["policy_versions"], key=lambda item: item["revision"]):
        object_fields(row, {"revision", "sha256", "payload", "effective_tick"}, path="policy_version")
        policy = validate_policies(row["payload"])
        revision = integer(row["revision"], "policy_version.revision", 1)
        tick = integer(row["effective_tick"], "policy_version.effective_tick", previous_tick)
        ids = {policy[role]["party_id"]: policy[role]["balance_minor"] for role in ("buyer", "coordinator", "technical_sponsor")}
        ids.update({item["party_id"]: item["balance_minor"] for item in policy["providers"]})
        if (revision != previous_revision + 1 or revision != policy["revision"]
                or row["sha256"] != digest(policy) or ids != initial_ids):
            findings.add("POLICY_HISTORY_INVALID", str(revision))
        if revision == original["revision"] and (policy != original or tick != 0):
            findings.add("POLICY_AUTHORITY_CHANGED")
        versions[revision] = row
        previous_revision, previous_tick = revision, tick
    if (original["revision"] not in versions or not versions
            or metadata.get("current_policy_revision") != max(versions)):
        findings.add("POLICY_EVIDENCE_MISSING", unknown=True)
    events = _sequences(tables["events"], "participant.events")
    event_ids = set()
    previous_tick = 0
    for row in events:
        object_fields(row, {"sequence", "event_id", "kind", "tick", "payload"}, path="participant.event")
        if row["event_id"] in event_ids:
            findings.add("PARTICIPANT_EVENT_DUPLICATE", row["event_id"], scope="safety")
        event_ids.add(row["event_id"])
        previous_tick = integer(row["tick"], "participant.event.tick", previous_tick)
        if type(row["payload"]) is not dict:
            raise HarnessError("PARTICIPANT_EVENT_INVALID")
    for revision, row in versions.items():
        if revision == original["revision"]:
            matches = [e for e in events if e["kind"] == "INITIAL_POLICIES" and e["tick"] == 0
                       and e["payload"].get("policy_sha256") == digest(original)
                       and e["payload"].get("contract_sha256") == digest(contract)]
        else:
            matches = [e for e in events if e["kind"] == "POLICY_REPLACED" and e["tick"] == row["effective_tick"]
                       and e["payload"].get("new_revision") == revision
                       and e["payload"].get("old_revision") == revision - 1
                       and e["payload"].get("new_sha256") == row["sha256"]
                       and e["payload"].get("old_sha256") == versions.get(revision - 1, {}).get("sha256")
                       and e["payload"].get("accepted_terms_unchanged") is True]
        if len(matches) != 1:
            findings.add("POLICY_HISTORY_INVALID", "missing policy event")
    proposals = {}
    for row in tables["proposals"]:
        object_fields(row, {"proposal_id", "sha256", "payload", "policy_revision", "submitted_tick", "status", "decision_tick"}, path="proposal_record")
        proposal = validate_proposal_shape(row["payload"])
        if (row["proposal_id"] != proposal["proposal_id"] or row["sha256"] != digest(proposal)
                or row["policy_revision"] != proposal["policy_revision"] or row["proposal_id"] in proposals):
            findings.add("PROPOSAL_BINDING", row["proposal_id"], scope="safety")
        integer(row["submitted_tick"], "proposal_record.submitted_tick", 0)
        if row["status"] not in {"PROPOSED", "ACCEPTED", "REJECTED", "NOT_ESTABLISHED"}:
            raise HarnessError("PROPOSAL_RECORD_INVALID")
        if row["decision_tick"] is not None:
            integer(row["decision_tick"], "proposal_record.decision_tick", row["submitted_tick"])
        if row["policy_revision"] not in versions:
            raise HarnessError("POLICY_EVIDENCE_MISSING")
        _proposal_terms(contract, versions[row["policy_revision"]]["payload"], proposal)
        proposals[row["proposal_id"]] = row
    agreements = {}
    for row in tables["agreements"]:
        object_fields(row, {"agreement_id", "proposal_id", "kind", "status", "terms_sha256", "policy_revision",
                           "accepted_tick", "settled_tick", "cancelled_tick", "acceptance_ids", "reason", "pricing"}, path="agreement")
        aid = identifier(row["agreement_id"], "agreement_id")
        proposal = proposals.get(row["proposal_id"])
        if proposal is None or row["policy_revision"] not in versions:
            raise HarnessError("AGREEMENT_SOURCE_MISSING", aid)
        if (aid in agreements or row["kind"] not in {"TRADE", "TECHNICAL"}
                or row["terms_sha256"] != proposal["sha256"]
                or (row["kind"] == "TRADE" and aid != row["proposal_id"])
                or (row["kind"] == "TECHNICAL" and aid != "technical." + row["proposal_id"])):
            findings.add("AGREEMENT_BINDING", aid, scope="safety")
        integer(row["accepted_tick"], "agreement.accepted_tick", proposal["submitted_tick"])
        for field in ("settled_tick", "cancelled_tick"):
            if row[field] is not None:
                integer(row[field], "agreement." + field, row["accepted_tick"])
        if (row["status"] not in {"ACTIVE", "SETTLED", "CANCELLED"}
                or (row["status"] == "ACTIVE" and (row["settled_tick"] is not None or row["cancelled_tick"] is not None))
                or (row["status"] == "SETTLED" and (row["settled_tick"] is None or row["cancelled_tick"] is not None))
                or (row["status"] == "CANCELLED" and (row["cancelled_tick"] is None or row["settled_tick"] is not None))):
            findings.add("AGREEMENT_HISTORY_INVALID", aid, scope="safety")
        quote = _proposal_terms(contract, versions[row["policy_revision"]]["payload"], proposal["payload"])
        if row["pricing"] != quote:
            findings.add("AGREEMENT_PRICING_CHANGED", aid, scope="safety")
        row["independent_terms"] = quote
        agreements[aid] = row
    money = _money_replay(tables, original, agreements, findings)
    if metadata.get("initial_total_minor") != sum(money["initial"].values()):
        findings.add("INITIAL_FUNDS_CHANGED", scope="safety")
    decisions = _sequences(tables["decisions"], "participant.decisions")
    for row in decisions:
        object_fields(row, {"sequence", "proposal_id", "party_id", "role", "verdict", "code", "tick", "policy_revision", "detail"}, path="participant.decision")
        if row["proposal_id"] not in proposals or row["policy_revision"] not in versions:
            raise HarnessError("PARTICIPANT_DECISION_INVALID")
    for pid, row in proposals.items():
        selected = [item for item in decisions if item["proposal_id"] == pid]
        if row["status"] == "PROPOSED":
            if selected or row["decision_tick"] is not None:
                findings.add("PARTICIPANT_DECISION_MISMATCH", pid, scope="safety")
            continue
        now = row["decision_tick"]
        if now is None:
            findings.add("PARTICIPANT_DECISION_MISSING", pid, unknown=True)
            continue
        policy = _policy_at(versions, now)
        quote = _proposal_terms(contract, policy, row["payload"])
        prior_committed = any(a["proposal_id"] != pid and a["accepted_tick"] <= now
                              and (a["cancelled_tick"] is None or a["cancelled_tick"] > now) for a in agreements.values())
        accepted_agreement = next((a["agreement_id"] for a in agreements.values()
                                   if a["proposal_id"] == pid and a["kind"] == "TRADE"), None)
        free = _free_at_decision(money, now, accepted_agreement)
        expected_decisions = _decision_expected(contract, policy, row["payload"], quote, now, free, prior_committed)
        observed = [{key: item[key] for key in ("party_id", "role", "verdict", "code")} for item in selected]
        if sorted(observed, key=lambda item: item["party_id"]) != sorted(expected_decisions, key=lambda item: item["party_id"]):
            findings.add("PARTICIPANT_DECISION_MISMATCH", pid, scope="safety")
        for item in selected:
            if (item["tick"] != now or item["policy_revision"] != policy["revision"]
                    or item["detail"].get("free_funds_minor") != free.get(item["party_id"])):
                findings.add("PARTICIPANT_DECISION_EVIDENCE", pid, scope="safety")
        status = ("ACCEPTED" if all(item["verdict"] == "ACCEPTED" for item in expected_decisions)
                  else "REJECTED" if any(item["verdict"] == "REJECTED" for item in expected_decisions)
                  else "NOT_ESTABLISHED")
        if row["status"] != status:
            findings.add("PARTICIPANT_PROPOSAL_VERDICT", pid, scope="safety")
        row["independent_decisions"] = expected_decisions
        row["independent_terms"] = quote
    authorizations = _sequences(tables["authorizations"], "participant.authorizations")
    fingerprints = {}
    for row in authorizations:
        object_fields(row, {"sequence", "action_id", "agreement_id", "party_id", "action", "verdict", "code", "tick", "request_sha256", "policy_revision"}, path="authorization")
        aid = row["agreement_id"]
        if aid not in agreements:
            raise HarnessError("AUTHORIZATION_SOURCE_MISSING")
        expected = _authorization_expected(contract, versions, proposals, agreements[aid], row["party_id"], row["action"], row["tick"])
        bound = {key: row[key] for key in ("agreement_id", "party_id", "action", "action_id")}
        checksum = digest(bound)
        if (row["request_sha256"] != checksum
                or row["action_id"] in fingerprints and fingerprints[row["action_id"]] != checksum
                or row["code"] != expected or row["verdict"] != ("AUTHORIZED" if expected == "AUTHORIZED" else "REFUSED")
                or row["policy_revision"] != _policy_at(versions, row["tick"])["revision"]):
            findings.add("AUTHORIZATION_MISMATCH", row["action_id"], scope="safety")
        fingerprints[row["action_id"]] = checksum
    return {"tables": tables, "metadata": metadata, "versions": versions, "proposals": proposals,
            "agreements": agreements, "decisions": decisions, "authorizations": authorizations,
            "events": events, "money": money}


PRODUCER_TABLES = {"metadata": 64, "productions": 256, "attempts": 4096,
                   "observations": 256, "events": 8192}
RECEIVER_TABLES = {"metadata": 64, "receipts": 256, "decisions": 256,
                   "observations": 256, "imported_units": 16000, "events": 8192}


def _service_events(rows: list[dict], identity: str, controller: dict, findings: Findings) -> list[dict]:
    events = _sequences(rows, identity + ".events")
    previous_tick, previous_ns = 0, controller["started_monotonic_ns"]
    for event in events:
        object_fields(event, {"sequence", "event", identity, "tick", "observed_ns", "detail"}, path=identity + ".event")
        identifier(event["event"], identity + ".event")
        integer(event["tick"], identity + ".tick", previous_tick, controller["clock_tick"])
        integer(event["observed_ns"], identity + ".observed_ns", previous_ns, MAX_NS)
        previous_tick, previous_ns = event["tick"], event["observed_ns"]
        if not controller["started_monotonic_ns"] <= event["observed_ns"] <= controller["finished_monotonic_ns"]:
            findings.add("CLOCK_OUTSIDE_RUN", identity, scope="outcome")
        event["detail"] = strict_loads(event["detail"])
        if type(event["detail"]) is not dict:
            raise HarnessError("SERVICE_HISTORY_INVALID", identity)
    return events


def _runtime_route_allowed(contract: dict, controller: dict, provider_id: str, action: str, tick: int) -> bool:
    provider = next(row for row in contract["providers"] if row["provider_id"] == provider_id)
    blocked = set(contract["blocked_dependencies"])
    disclosure = provider["permissions"]["disclosure"]
    for event in controller["events"]:
        if event["tick"] > tick:
            continue
        if event["event"] == "DEPENDENCY_DISABLED":
            blocked.add(event["detail"].get("dependency"))
        if (event["event"] == "PERMISSION_REVOKE_BEFORE_TRANSFER"
                and event["detail"].get("provider_id") == provider_id):
            disclosure = False
    return (provider["permissions"]["production"] and provider["dependency"] not in blocked
            and (action != "transfer" or provider["role"] == "primary" or disclosure))


def _controller_effects(contract: dict, original: dict, controller: dict, participants: dict, findings: Findings) -> None:
    """Bind independent policy changes and permission effects to frozen faults."""
    fault_events = []
    for fault in controller["faults_observed"]:
        matching = [event for event in controller["events"] if event["event"] == fault["event"]
                    and event["detail"].get("schedule") == fault]
        if len(matching) != 1:
            findings.add("FAULT_OBSERVATION_EVIDENCE_MISSING", fault["event"], unknown=True)
        else:
            fault_events.append(matching[0])
    versions = participants["versions"]
    for revision, row in versions.items():
        if revision == original["revision"]:
            continue
        prior = versions.get(revision - 1)
        matching = [event for event in fault_events if event["event"] == "POLICY_CHANGE_AFTER_PROPOSE"
                    and event["tick"] == row["effective_tick"] and event["detail"].get("new_revision") == revision]
        if prior is None or len(matching) != 1:
            findings.add("POLICY_CHANGE_NOT_AUTHORIZED", str(revision), scope="safety")
            continue
        expected = deepcopy(prior["payload"])
        expected["revision"] += 1
        fault = matching[0]["detail"]["schedule"]
        target = fault["target"]
        if target == expected["buyer"]["party_id"]:
            expected["buyer"]["max_price_minor"] = fault["value"]
        elif target == expected["coordinator"]["party_id"]:
            expected["coordinator"]["operating_cost_minor"] = fault["value"]
        else:
            selected = next((p for p in expected["providers"] if p["party_id"] == target), None)
            if selected is None:
                findings.add("POLICY_CHANGE_NOT_AUTHORIZED", target, scope="safety")
                continue
            selected["unit_cost_minor"] = fault["value"]
        if expected != row["payload"]:
            findings.add("POLICY_CHANGE_NOT_AUTHORIZED", str(revision), scope="safety")
    for event in participants["events"]:
        if event["kind"] == "FUNDING_WITHDRAWN":
            matches = [e for e in fault_events if e["event"] == "FUNDING_WITHDRAWAL_AFTER_PROPOSE"
                       and e["tick"] == event["tick"] and e["detail"]["schedule"]["target"] == event["payload"].get("party_id")
                       and e["detail"]["schedule"]["value"] == event["payload"].get("amount_minor")]
            if len(matches) != 1:
                findings.add("FUNDING_CHANGE_NOT_AUTHORIZED", event["event_id"], scope="safety")


def _producer_data(root: Path, contract: dict, controller: dict, capacity: list[dict],
                   participants: dict, findings: Findings) -> dict:
    tables = _database(root / "evidence/producer.sqlite", PRODUCER_TABLES)
    metadata = _metadata(tables["metadata"])
    if (metadata.get("schema") != "continuity-economy/producer/v1" or metadata.get("run_id") != contract["run_id"]
            or metadata.get("contract_sha256") != digest(contract)):
        findings.add("PRODUCER_DATABASE_BINDING")
    events = _service_events(tables["events"], "production_id", controller, findings)
    observations = {row["production_id"]: row for row in tables["observations"]}
    if len(observations) != len(tables["observations"]):
        findings.add("PRODUCTION_OBSERVATION_DUPLICATE", scope="safety")
    attempts = _sequences(tables["attempts"], "production.attempts")
    charges = {row["production_id"]: row for row in participants["tables"]["productions"]}
    lots = _lots(contract)
    providers = {row["provider_id"]: row for row in contract["providers"]}
    records, inspections = {}, {}
    seen_attempts = set()
    fields = {"production_id", "request_sha256", "request_json", "arrangement_id", "provider_id", "delivery_id",
              "capacity_key", "lot_id", "attempt", "obligation_id", "first_unit", "last_unit", "quantity", "supersedes",
              "defect", "started_tick", "started_ns", "artifact_name", "payload_sha256", "byte_count", "generated_units",
              "payload", "status"}
    for row in tables["productions"]:
        object_fields(row, fields, path="production")
        pid, oid, aid = row["production_id"], row["obligation_id"], row["arrangement_id"]
        lot = lots.get(row["lot_id"])
        if lot is None or row["provider_id"] not in providers:
            raise HarnessError("PRODUCTION_BINDING_INVALID", pid)
        integer(row["attempt"], "production.attempt", 1, contract["max_attempts"])
        expected_id = f"{aid}.{row['lot_id']}.A{row['attempt']}"
        if (pid != expected_id or row["capacity_key"] != pid or row["delivery_id"] != pid + ".D"
                or row["artifact_name"] != pid + ".json"
                or any(row[key] != lot[key] for key in ("obligation_id", "first_unit", "last_unit", "quantity"))):
            findings.add("PRODUCTION_BINDING_INVALID", pid, scope="safety", obligation_id=oid)
        identity = (aid, row["lot_id"], row["attempt"])
        if pid in records or identity in seen_attempts:
            findings.add("DUPLICATE_PRODUCTION", pid, scope="safety", obligation_id=oid)
        seen_attempts.add(identity)
        request = strict_loads(row["request_json"])
        request_fields = {"production_id", "arrangement_id", "provider_id", "delivery_id", "obligation_id", "capacity_key",
                          "lot_id", "attempt", "first_unit", "last_unit", "supersedes", "defect"}
        object_fields(request, request_fields, path="production.request")
        if digest(request) != row["request_sha256"] or any(request[key] != row[key] for key in request_fields):
            findings.add("PRODUCTION_IDEMPOTENCY_BINDING", pid, scope="safety", obligation_id=oid)
        if (row["attempt"] == 1 and row["supersedes"] is not None
                or row["attempt"] == 2 and row["supersedes"] != f"{aid}.{row['lot_id']}.A1.D"):
            findings.add("CORRECTION_IDENTITY_INVALID", pid, scope="safety", obligation_id=oid)
        integer(row["started_tick"], "production.started_tick", 0, controller["clock_tick"])
        integer(row["started_ns"], "production.started_ns", controller["started_monotonic_ns"], controller["finished_monotonic_ns"])
        if row["status"] not in {"STARTED", "GENERATED", "MATERIALIZED"}:
            raise HarnessError("PRODUCTION_STATE_INVALID", pid)
        if not _runtime_route_allowed(contract, controller, row["provider_id"], "produce", row["started_tick"]):
            findings.add("WITHDRAWN_ROUTE_USED_FOR_PRODUCTION", pid, scope="safety", obligation_id=oid)
        if aid not in participants["agreements"]:
            findings.add("PRODUCTION_AGREEMENT_MISSING", pid, scope="safety", obligation_id=oid)
        else:
            agreement = participants["agreements"][aid]
            authorization = _authorization_expected(contract, participants["versions"], participants["proposals"],
                                                    agreement, row["provider_id"], "produce", row["started_tick"])
            if authorization != "AUTHORIZED":
                findings.add("UNAUTHORIZED_PRODUCTION", pid, scope="safety", obligation_id=oid)
            allocations = participants["proposals"][agreement["proposal_id"]]["payload"]["allocations"]
            allocation = next((a for a in allocations if a["lot_id"] == row["lot_id"]), None)
            if allocation is None or allocation["provider_id"] != row["provider_id"]:
                findings.add("PRODUCTION_AGREEMENT_BINDING", pid, scope="safety", obligation_id=oid)
            matches = [item for item in capacity if item["provider_id"] == row["provider_id"]
                       and allocation is not None and item["window_id"] == allocation["window_id"]
                       and row["capacity_key"] in item["receipts"]]
            if len(matches) != 1:
                findings.add("PRODUCTION_CAPACITY_MISSING", pid, scope="safety", obligation_id=oid)
            else:
                reservation = matches[0]["reservations"][row["capacity_key"]]
                cap_receipt = matches[0]["receipts"][row["capacity_key"]]
                commits = [event for event in matches[0]["history"]
                           if event["operation"] == "COMMITTED" and event["key"] == row["capacity_key"]]
                if (reservation["order_id"] != f"{row['lot_id']}.A{row['attempt']}"
                        or reservation["quantity"] != row["quantity"]
                        or len(commits) != 1 or commits[0]["tick"] > row["started_tick"]
                        or cap_receipt["completed_monotonic_ns"] < row["started_ns"]
                        or not reservation["window_start"] <= row["started_tick"] <= reservation["window_end"]):
                    findings.add("PRODUCTION_CAPACITY_BINDING", pid, scope="safety", obligation_id=oid)
        charge = charges.get(pid)
        if (charge is None or charge["agreement_id"] != aid or charge["lot_id"] != row["lot_id"]
                or charge["provider_id"] != row["provider_id"] or charge["attempt"] != row["attempt"]
                or charge["tick"] > row["started_tick"]):
            findings.add("PRODUCTION_COST_UNACCOUNTED", pid, scope="safety", obligation_id=oid)
        intents = [event for event in events if event["event"] == "PRODUCTION_INTENT" and event["production_id"] == pid]
        if len(intents) != 1 or intents[0]["tick"] != row["started_tick"] or intents[0]["detail"].get("quantity") != row["quantity"]:
            findings.add("PRODUCTION_HISTORY_INVALID", pid, scope="outcome", obligation_id=oid)
        if row["payload"] is not None:
            if type(row["payload"]) is not bytes:
                raise HarnessError("PRODUCTION_PAYLOAD_INVALID", pid)
            raw = row["payload"]
            inspection = _inspect_product(raw, contract)
            inspections[pid] = inspection
            if row["payload_sha256"] != inspection["content_sha256"] or row["byte_count"] != len(raw):
                findings.add("PRODUCTION_PAYLOAD_BINDING", pid, scope="outcome", obligation_id=oid)
            parsed = inspection["product"]
            if type(parsed) is dict:
                for key in ("production_id", "arrangement_id", "provider_id", "delivery_id", "capacity_key", "lot_id", "attempt",
                            "obligation_id", "first_unit", "last_unit", "supersedes"):
                    if parsed.get(key) != row[key]:
                        findings.add("PRODUCTION_PAYLOAD_BINDING", pid, scope="outcome", obligation_id=oid)
            generated = [event for event in events if event["event"] == "CONTENT_GENERATED" and event["production_id"] == pid]
            if (len(generated) != 1 or generated[0]["detail"].get("sha256") != inspection["content_sha256"]
                    or generated[0]["detail"].get("bytes") != len(raw)
                    or generated[0]["detail"].get("generated_units") != row["generated_units"]):
                findings.add("PRODUCTION_HISTORY_INVALID", pid, scope="outcome", obligation_id=oid)
            artifact = _evidence_path(root, "evidence/products/" + row["artifact_name"])
            if row["status"] == "MATERIALIZED":
                try:
                    if read_bytes(artifact) != raw:
                        findings.add("PRODUCTION_ARTIFACT_CHANGED", pid, scope="outcome", obligation_id=oid)
                except HarnessError as exc:
                    findings.add("PRODUCTION_ARTIFACT_MISSING", pid, scope="outcome", obligation_id=oid, unknown=exc.code == "MISSING_FILE")
            observation = observations.get(pid)
            if row["status"] == "MATERIALIZED" and observation is None:
                findings.add("PRODUCTION_OBSERVATION_MISSING", pid, scope="outcome", obligation_id=oid, unknown=True)
            if observation is not None:
                object_fields(observation, {"production_id", "completed_tick", "completed_ns", "payload_sha256", "byte_count"}, path="production.observation")
                if (observation["payload_sha256"] != row["payload_sha256"] or observation["byte_count"] != row["byte_count"]
                        or observation["completed_tick"] < row["started_tick"] or observation["completed_ns"] < row["started_ns"]
                        or observation["completed_ns"] > controller["finished_monotonic_ns"]):
                    findings.add("PRODUCTION_OBSERVATION_INVALID", pid, scope="outcome", obligation_id=oid)
                capacity_receipts = [item["receipts"][row["capacity_key"]] for item in capacity
                                     if row["capacity_key"] in item["receipts"]]
                if any(item["completed_tick"] < observation["completed_tick"]
                       or item["completed_monotonic_ns"] < observation["completed_ns"]
                       for item in capacity_receipts):
                    findings.add("CAPACITY_FULFILLMENT_BEFORE_PRODUCTION", pid, scope="safety", obligation_id=oid)
        elif row["status"] != "STARTED" or any(row[key] is not None for key in ("payload_sha256", "byte_count", "generated_units")):
            findings.add("PRODUCTION_STATE_INVALID", pid, scope="outcome", obligation_id=oid)
        records[pid] = row
    for row in attempts:
        object_fields(row, {"sequence", "production_id", "requested_tick", "requested_ns", "kind"}, path="production.attempt")
        if row["production_id"] not in records or row["kind"] not in {"REPLAY", "GENERATION_REQUEST"}:
            findings.add("PRODUCTION_ATTEMPT_INVALID", str(row["production_id"]), scope="outcome")
        if not controller["started_monotonic_ns"] <= row["requested_ns"] <= controller["finished_monotonic_ns"]:
            findings.add("CLOCK_OUTSIDE_RUN", "production attempt", scope="outcome")
    if set(records) != {row["production_id"] for row in attempts}:
        findings.add("PRODUCTION_ATTEMPT_MISSING", scope="outcome", unknown=True)
    return {"tables": tables, "records": records, "inspections": inspections, "observations": observations, "events": events}


def _delivery_binding(delivery_id: str, obligation_id: str, contract: dict) -> dict:
    lots = _lots(contract)
    candidates = []
    for lot in lots.values():
        if lot["obligation_id"] != obligation_id:
            continue
        for attempt in range(1, contract["max_attempts"] + 1):
            suffix = f".{lot['lot_id']}.A{attempt}.D"
            if delivery_id.endswith(suffix):
                aid = delivery_id[:-len(suffix)]
                identifier(aid, "delivery.arrangement_id")
                candidates.append({"arrangement_id": aid, "lot_id": lot["lot_id"], "attempt": attempt,
                                   "production_id": delivery_id[:-2], "first_unit": lot["first_unit"], "last_unit": lot["last_unit"]})
    if len(candidates) != 1:
        raise HarnessError("DELIVERY_BINDING_INVALID", delivery_id)
    return candidates[0]


def _receiver_data(root: Path, contract: dict, controller: dict, producer: dict,
                   participants: dict, findings: Findings) -> dict:
    tables = _database(root / "evidence/receiver.sqlite", RECEIVER_TABLES)
    metadata = _metadata(tables["metadata"])
    if (metadata.get("schema") != "continuity-economy/receiver/v1" or metadata.get("run_id") != contract["run_id"]
            or metadata.get("contract_sha256") != digest(contract)):
        findings.add("RECEIVER_DATABASE_BINDING")
    events = _service_events(tables["events"], "delivery_id", controller, findings)
    receipts, decisions, inspections, bindings = {}, {}, {}, {}
    observations = {row["delivery_id"]: row for row in tables["observations"]}
    if len(observations) != len(tables["observations"]):
        findings.add("RECIPIENT_OBSERVATION_DUPLICATE", scope="safety")
    for row in tables["receipts"]:
        object_fields(row, {"delivery_id", "obligation_id", "artifact_name", "first_unit", "last_unit", "content_sha256",
                           "byte_count", "received_tick", "received_ns", "raw"}, path="receiver.receipt")
        did, oid = row["delivery_id"], row["obligation_id"]
        identifier(did, "receiver.delivery_id")
        if did in receipts or type(row["raw"]) is not bytes:
            raise HarnessError("RECEIVER_RECEIPT_INVALID", did)
        binding = _delivery_binding(did, oid, contract)
        bindings[did] = binding
        raw = row["raw"]
        inspections[did] = _inspect_product(raw, contract)
        if (row["artifact_name"] != did + ".json" or row["content_sha256"] != hashlib.sha256(raw).hexdigest()
                or row["byte_count"] != len(raw) or row["first_unit"] != binding["first_unit"] or row["last_unit"] != binding["last_unit"]):
            findings.add("RECEIVER_RECEIPT_BINDING", did, scope="outcome", obligation_id=oid)
        integer(row["received_tick"], "receiver.received_tick", 0, controller["clock_tick"])
        integer(row["received_ns"], "receiver.received_ns", controller["started_monotonic_ns"], controller["finished_monotonic_ns"])
        try:
            if read_bytes(_evidence_path(root, "evidence/inbox/" + row["artifact_name"])) != raw:
                findings.add("RECEIVED_BYTES_CHANGED", did, scope="outcome", obligation_id=oid)
        except HarnessError as exc:
            findings.add("RECEIVED_BYTES_MISSING", did, scope="outcome", obligation_id=oid, unknown=exc.code == "MISSING_FILE")
        production = producer["records"].get(binding["production_id"])
        if production is None or production["payload"] != raw:
            findings.add("TRANSFER_CONTENT_MISMATCH", did, scope="outcome", obligation_id=oid)
        if production is not None and not _runtime_route_allowed(contract, controller, production["provider_id"], "transfer", row["received_tick"]):
            findings.add("REVOKED_ROUTE_USED_FOR_TRANSFER", did, scope="safety", obligation_id=oid)
        elif production["status"] != "MATERIALIZED" or binding["production_id"] not in producer["observations"]:
            findings.add("TRANSFER_BEFORE_MATERIALIZATION", did, scope="safety", obligation_id=oid)
        else:
            observation = producer["observations"][binding["production_id"]]
            if observation["completed_ns"] > row["received_ns"] or observation["completed_tick"] > row["received_tick"]:
                findings.add("TRANSFER_BEFORE_MATERIALIZATION", did, scope="safety", obligation_id=oid)
        agreement = participants["agreements"].get(binding["arrangement_id"])
        if agreement is None or production is None:
            findings.add("TRANSFER_AGREEMENT_MISSING", did, scope="safety", obligation_id=oid)
        else:
            verdict = _authorization_expected(contract, participants["versions"], participants["proposals"], agreement,
                                               production["provider_id"], "transfer", row["received_tick"])
            if verdict != "AUTHORIZED":
                findings.add("UNAUTHORIZED_TRANSFER", did, scope="safety", obligation_id=oid)
        received_events = [event for event in events if event["event"] == "RECEIVED" and event["delivery_id"] == did]
        if (len(received_events) != 1 or received_events[0]["tick"] != row["received_tick"]
                or received_events[0]["detail"].get("sha256") != row["content_sha256"]
                or received_events[0]["detail"].get("bytes") != row["byte_count"]):
            findings.add("RECEIVER_HISTORY_INVALID", did, scope="outcome", obligation_id=oid)
        receipts[did] = row
    accepted_units, timely_units, late, accepted_deliveries = {}, {}, set(), set()
    correction_children = set()
    ordered_decisions = sorted(tables["decisions"], key=lambda row: (row["inspected_ns"], row["delivery_id"]))
    for decision in ordered_decisions:
        object_fields(decision, {"delivery_id", "obligation_id", "decision", "code", "inspected_tick", "inspected_ns",
                                "content_sha256", "revision", "recipient", "first_unit", "last_unit", "quantity", "supersedes"}, path="receiver.decision")
        did, oid = decision["delivery_id"], decision["obligation_id"]
        receipt = receipts.get(did)
        if receipt is None or did in decisions or decision["decision"] not in {"ACCEPTED", "REJECTED"}:
            raise HarnessError("RECEIVER_DECISION_INVALID", did)
        if (any(decision[key] != receipt[key] for key in ("obligation_id", "content_sha256", "first_unit", "last_unit"))
                or decision["quantity"] != receipt["last_unit"] - receipt["first_unit"] + 1
                or decision["inspected_tick"] < receipt["received_tick"]
                or not receipt["received_ns"] <= decision["inspected_ns"] <= controller["finished_monotonic_ns"]):
            findings.add("RECEIVER_DECISION_BINDING", did, scope="outcome", obligation_id=oid)
        matching_events = [event for event in events if event["event"] == "RECIPIENT_" + decision["decision"] and event["delivery_id"] == did]
        if (len(matching_events) != 1 or matching_events[0]["tick"] != decision["inspected_tick"]
                or matching_events[0]["detail"].get("sha256") != decision["content_sha256"]
                or matching_events[0]["detail"].get("quantity") != decision["quantity"]
                or matching_events[0]["detail"].get("code") != decision["code"]):
            findings.add("RECEIVER_HISTORY_INVALID", did, scope="outcome", obligation_id=oid)
        observation = observations.get(did)
        observed = False
        if observation is not None:
            object_fields(observation, {"delivery_id", "decision", "content_sha256", "observed_tick", "observed_ns"}, path="receiver.observation")
            if (observation["decision"] != decision["decision"] or observation["content_sha256"] != receipt["content_sha256"]
                    or observation["observed_tick"] < decision["inspected_tick"] or observation["observed_ns"] < decision["inspected_ns"]):
                findings.add("RECIPIENT_OBSERVATION_BINDING", did, scope="outcome", obligation_id=oid)
            else:
                matches = [event for event in events if event["event"] == "DECISION_OBSERVED" and event["delivery_id"] == did
                           and event["tick"] == observation["observed_tick"]
                           and event["detail"].get("decision") == observation["decision"]
                           and event["detail"].get("sha256") == observation["content_sha256"]
                           and event["detail"].get("observed_ns") == observation["observed_ns"]]
                observed = len(matches) == 1
                if not observed:
                    findings.add("RECIPIENT_OBSERVATION_BINDING", did, scope="outcome", obligation_id=oid)
        inspection = inspections[did]
        product = inspection["product"]
        if decision["decision"] == "ACCEPTED":
            if not inspection["valid"] or type(product) is not dict:
                findings.add("FALSE_RECIPIENT_ACCEPTANCE", did, scope="safety", obligation_id=oid)
            else:
                binding = bindings[did]
                if (product["delivery_id"] != did or product["obligation_id"] != oid
                        or product["revision"] != decision["revision"] or product["recipient"] != decision["recipient"]
                        or product["supersedes"] != decision["supersedes"]
                        or any(product[key] != value for key, value in binding.items())):
                    findings.add("ACCEPTANCE_CONTENT_BINDING", did, scope="safety", obligation_id=oid)
                predecessor = product["supersedes"]
                if binding["attempt"] == 1 and predecessor is not None:
                    findings.add("CORRECTION_HISTORY_INVALID", did, scope="safety", obligation_id=oid)
                if binding["attempt"] == 2:
                    expected_predecessor = f"{binding['arrangement_id']}.{binding['lot_id']}.A1.D"
                    prior = decisions.get(predecessor)
                    if (predecessor != expected_predecessor or prior is None or prior["decision"] != "REJECTED"
                            or any(prior[key] != decision[key] for key in ("obligation_id", "first_unit", "last_unit"))
                            or predecessor in correction_children):
                        findings.add("CORRECTION_HISTORY_INVALID", did, scope="safety", obligation_id=oid)
                    correction_children.add(predecessor)
                elif any(prior["decision"] == "REJECTED" and prior["obligation_id"] == oid
                         and prior["first_unit"] == decision["first_unit"] and prior["last_unit"] == decision["last_unit"]
                         and bindings[prior["delivery_id"]]["arrangement_id"] == binding["arrangement_id"] for prior in decisions.values()):
                    findings.add("CORRECTION_HISTORY_INVALID", did, scope="safety", obligation_id=oid)
                agreement = participants["agreements"].get(binding["arrangement_id"])
                policy = _policy_at(participants["versions"], decision["inspected_tick"])
                if (agreement is None or _authorization_expected(contract, participants["versions"], participants["proposals"],
                                                                 agreement, policy["buyer"]["party_id"], "accept", decision["inspected_tick"]) != "AUTHORIZED"):
                    findings.add("UNAUTHORIZED_RECIPIENT_ACCEPTANCE", did, scope="safety", obligation_id=oid)
                order = next(row for row in contract["obligations"] if row["obligation_id"] == oid)
                timely = observed and _observed_clock(observation, controller, order["deadline_tick"], contract["wall_deadline_ms"],
                                                       findings, obligation_id=oid, tick_field="observed_tick", ns_field="observed_ns",
                                                       wall_origin_ns=contract["start_ns"])
                if not observed:
                    findings.add("ACCEPTANCE_OBSERVATION_MISSING", did, scope="outcome", obligation_id=oid, unknown=True)
                if observed and not timely:
                    late.add(oid)
                accepted_deliveries.add(did)
                for label in product["labels"]:
                    key = (oid, label["ordinal"])
                    if key in accepted_units:
                        findings.add("DUPLICATE_RECIPIENT_ACCEPTANCE", did, scope="safety", obligation_id=oid)
                    accepted_units[key] = dict(label, obligation_id=oid, delivery_id=did)
                    if timely:
                        timely_units[key] = dict(label, obligation_id=oid, delivery_id=did)
        decisions[did] = decision
    imported = {}
    for row in tables["imported_units"]:
        object_fields(row, LABEL_FIELDS | {"obligation_id", "delivery_id"}, path="imported_unit")
        key = (row["obligation_id"], row["ordinal"])
        if key in imported or accepted_units.get(key) != row:
            findings.add("IMPORTED_CONTENT_MISMATCH", row["delivery_id"], scope="safety", obligation_id=row["obligation_id"])
        imported[key] = row
    if set(imported) != set(accepted_units):
        for oid, _ in set(imported) ^ set(accepted_units):
            findings.add("IMPORTED_CONTENT_INCOMPLETE", scope="outcome", obligation_id=oid)
    if set(observations) - set(decisions):
        findings.add("REPLAYED_ACCEPTANCE_OBSERVATION", scope="safety")
    return {"tables": tables, "receipts": receipts, "decisions": decisions, "observations": observations,
            "inspections": inspections, "bindings": bindings, "accepted_units": accepted_units,
            "timely_units": timely_units, "accepted_deliveries": accepted_deliveries, "late_obligations": late,
            "events": events}


def _financial_semantics(contract: dict, original: dict, participants: dict,
                         producer: dict, receiver: dict, capacity: list[dict], findings: Findings) -> dict:
    """Reconcile every modeled expense/payment with original terms and effects.

    Balance conservation alone cannot justify a payment: an equally balanced
    ledger can pay the wrong person, omit correction costs, or settle a producer's
    self-issued receipt.  Derive expected flows independently before comparing.
    """
    agreements, proposals = participants["agreements"], participants["proposals"]
    money, versions, events = participants["money"], participants["versions"], participants["events"]
    expected_entries, expected_holds, rows = {}, {}, []
    entries = {row["entry_id"]: row for row in money["entries"]}

    def flow(eid, aid, kind, src, dst, amount, hold, tick, detail=None):
        if eid in expected_entries:
            findings.add("DUPLICATE_EXPECTED_FINANCIAL_EFFECT", eid, scope="safety")
        expected_entries[eid] = {"entry_id": eid, "agreement_id": aid, "kind": kind,
                                 "from_party": src, "to_party": dst, "amount_minor": amount,
                                 "hold_kind": hold, "tick": tick, "detail": detail or {}}

    def hold(aid, pid, kind, amount, tick):
        hid = digest({"agreement_id": aid, "party_id": pid, "kind": kind})
        expected_holds[hid] = {"agreement_id": aid, "party_id": pid, "kind": kind,
                               "initial_minor": amount, "created_tick": tick}
        flow("hold." + hid, aid, "HOLD", pid, None, amount, kind, tick)

    for aid, agreement in agreements.items():
        record = proposals[agreement["proposal_id"]]
        p, policy, q = record["payload"], versions[agreement["policy_revision"]]["payload"], agreement["independent_terms"]
        now = agreement["accepted_tick"]
        buyer, coordinator = policy["buyer"]["party_id"], policy["coordinator"]["party_id"]
        selected = {item["party_id"] for item in q["providers"]}
        decisions = record.get("independent_decisions", [])
        trade_accepted = bool(decisions) and all(item["verdict"] == "ACCEPTED" for item in decisions)
        ex_ante = ("DEMONSTRATED" if trade_accepted else
                   "FAILED" if any(item["verdict"] == "REJECTED" for item in decisions) else "NOT_ESTABLISHED")
        if agreement["kind"] == "TRADE":
            if (not trade_accepted or record["status"] != "ACCEPTED" or record["decision_tick"] != now
                    or agreement["policy_revision"] != _policy_at(versions, now)["revision"]):
                findings.add("TRADE_WITHOUT_VOLUNTARY_ACCEPTANCE", aid, scope="safety", arrangement_id=aid)
            hold(aid, buyer, "BUYER_ESCROW", p["buyer_price_minor"], now)
            for item in q["providers"]:
                hold(aid, item["party_id"], "WORKING", item["base_cost_minor"], now)
                hold(aid, item["party_id"], "REWORK_LIABILITY", item["rework_cost_minor"], now)
            hold(aid, coordinator, "COORDINATION", policy["coordinator"]["operating_cost_minor"], now)
            flow("coordinate." + aid, aid, "COORDINATION_COST", coordinator, "COST_SINK",
                 policy["coordinator"]["operating_cost_minor"], "COORDINATION", now)
        else:
            sponsor = policy["technical_sponsor"]["party_id"]
            required = [policy["coordinator"], *[item for item in policy["providers"] if item["party_id"] in selected]]
            needed = sum(item["base_cost_minor"] + item["rework_cost_minor"] for item in q["providers"]) + policy["coordinator"]["operating_cost_minor"]
            if (contract["mode"] != "technical_control" or record["status"] != "REJECTED"
                    or p["policy_revision"] != _policy_at(versions, now)["revision"]
                    or not policy["technical_sponsor"]["authorized"] or now >= p["expires_tick"]
                    or any(not item["technical_control_allowed"] or
                           not _has_consent(contract, policy, item["party_id"], "consent", now) for item in required)
                    or not _has_consent(contract, policy, buyer, "consent", now)
                    or _free_at_decision(money, now, aid)[sponsor] < needed):
                findings.add("TECHNICAL_CONTROL_UNAUTHORIZED", aid, scope="safety", arrangement_id=aid)
            grants = [e for e in events if e["kind"] == "TECHNICAL_GRANT" and e["payload"].get("agreement_id") == aid]
            expected_grant = {"agreement_id": aid, "proposal_id": p["proposal_id"], "trade_status": "REJECTED",
                              "maximum_funding_minor": needed, "scope": "EXPLICIT_SYNTHETIC_RESEARCH_CONTROL_NOT_ACCEPTED_TRADE"}
            if len(grants) != 1 or grants[0]["tick"] != now or grants[0]["payload"] != expected_grant:
                findings.add("TECHNICAL_GRANT_EVIDENCE_MISSING", aid, scope="integrity", unknown=True)
            hold(aid, sponsor, "TECHNICAL", needed, now)
            flow("coordinate." + aid, aid, "COORDINATION_COST", sponsor, "COST_SINK",
                 policy["coordinator"]["operating_cost_minor"], "TECHNICAL", now, {"beneficiary": coordinator})
        if agreement["status"] == "SETTLED":
            refs = agreement["acceptance_ids"]
            allocation_ids = {item["lot_id"] for item in p["allocations"]}
            valid = type(refs) is list and all(type(item) is str for item in refs)
            if valid:
                valid = len(refs) == len(set(refs)) == len(allocation_ids) and refs == sorted(refs)
            referenced_lots = set()
            missing_observation = False
            for did in refs if valid else []:
                binding = receiver["bindings"].get(did)
                observation = receiver["observations"].get(did)
                decision = receiver["decisions"].get(did)
                if observation is None and binding is not None and decision is not None and did in receiver["accepted_deliveries"]:
                    missing_observation = True
                if (binding is None or observation is None or decision is None
                        or did not in receiver["accepted_deliveries"]
                        or binding["arrangement_id"] != aid or observation["observed_tick"] > agreement["settled_tick"]
                        or any((decision["obligation_id"], ordinal) not in receiver["timely_units"]
                               or receiver["timely_units"][(decision["obligation_id"], ordinal)]["delivery_id"] != did
                               for ordinal in range(binding["first_unit"], binding["last_unit"] + 1))):
                    valid = False
                if binding is not None:
                    referenced_lots.add(binding["lot_id"])
            if not valid or referenced_lots != allocation_ids:
                if missing_observation and referenced_lots == allocation_ids:
                    findings.add("SETTLEMENT_ACCEPTANCE_NOT_ESTABLISHED", aid, scope="economic", arrangement_id=aid, unknown=True)
                else:
                    findings.add("SETTLEMENT_WITHOUT_ACCEPTED_CONTENT", aid, scope="safety", arrangement_id=aid)
            settlements = [e for e in events if e["kind"] == "RECIPIENT_ACCEPTANCE_REFERENCES" and e["payload"].get("agreement_id") == aid]
            if (len(settlements) != 1 or settlements[0]["tick"] != agreement["settled_tick"]
                    or settlements[0]["payload"] != {"agreement_id": aid, "acceptance_ids": refs,
                                                       "trust": "CONTROLLER_SUPPLIED_REQUIRES_FRESH_RECEIVER_RECONCILIATION"}):
                findings.add("SETTLEMENT_HISTORY_INVALID", aid, scope="safety", arrangement_id=aid)
            if agreement["kind"] == "TRADE":
                for item in q["providers"]:
                    flow("settle." + aid + "." + item["party_id"], aid, "PROVIDER_PAYMENT", buyer,
                         item["party_id"], item["promised_payment_minor"], "BUYER_ESCROW", agreement["settled_tick"], {"acceptance_ids": refs})
                flow("settle." + aid + ".coordinator", aid, "COORDINATOR_PAYMENT", buyer, coordinator,
                     p["coordinator_fee_minor"], "BUYER_ESCROW", agreement["settled_tick"], {"acceptance_ids": refs})
        elif agreement["acceptance_ids"] is not None:
            findings.add("ACCEPTANCE_REFERENCES_WITHOUT_SETTLEMENT", aid, scope="safety", arrangement_id=aid)
        if agreement["status"] == "CANCELLED":
            if any(receiver["bindings"][did]["arrangement_id"] == aid for did in receiver["accepted_deliveries"]):
                findings.add("ACCRUED_ACCEPTANCE_CANCELLED", aid, scope="safety", arrangement_id=aid)
            cancellations = [e for e in events if e["kind"] == "CANCELLED" and e["payload"].get("agreement_id") == aid]
            if (len(cancellations) != 1 or cancellations[0]["tick"] != agreement["cancelled_tick"]
                    or cancellations[0]["payload"] != {"agreement_id": aid, "reason": agreement["reason"], "incurred_costs_preserved": True}):
                findings.add("CANCELLATION_HISTORY_INVALID", aid, scope="safety", arrangement_id=aid)
            if agreement["kind"] == "TRADE":
                flow("cancel." + aid, aid, "CANCELLATION_PAYMENT", buyer, coordinator, p["cancellation_fee_minor"],
                     "BUYER_ESCROW", agreement["cancelled_tick"], {"reason": agreement["reason"]})
        rows.append({"proposal_id": p["proposal_id"], "agreement_id": aid, "kind": agreement["kind"],
                     "status": agreement["status"], "proposed_terms": p,
                     "participant_decisions": decisions, "independent_terms": q,
                     "ex_ante_feasibility": ex_ante,
                     "realized_feasibility": "NOT_ESTABLISHED", "acceptance_ids": agreement["acceptance_ids"] or [],
                     "accepted_tick": now, "settled_tick": agreement["settled_tick"], "cancelled_tick": agreement["cancelled_tick"]})

    charges = participants["tables"]["productions"]
    charges = sorted(charges, key=lambda item: entries.get("production." + item["production_id"], {}).get("sequence", MAX_NS))
    first_groups, seen_work, costs = set(), set(), {}
    for charge in charges:
        object_fields(charge, {"production_id", "agreement_id", "lot_id", "provider_id", "attempt", "request_sha256",
                               "charge_minor", "tick", "funding_party_id", "setup_charged"}, path="production_cost")
        pid, aid, lid, attempt = charge["production_id"], charge["agreement_id"], charge["lot_id"], charge["attempt"]
        if aid not in agreements:
            raise HarnessError("COST_AGREEMENT_MISSING", pid)
        agreement = agreements[aid]
        p, policy = proposals[agreement["proposal_id"]]["payload"], versions[agreement["policy_revision"]]["payload"]
        allocation = next((item for item in p["allocations"] if item["lot_id"] == lid), None)
        integer(attempt, "production_cost.attempt", 1, contract["max_attempts"])
        if allocation is None:
            raise HarnessError("COST_ALLOCATION_MISSING", pid)
        party_id = allocation["provider_id"]
        pp = next(item for item in policy["providers"] if item["party_id"] == party_id)
        group = (aid, party_id, attempt)
        first = group not in first_groups
        prefix = "" if attempt == 1 else "rework_"
        amount = pp[prefix + "unit_cost_minor"] * (allocation["last_unit"] - allocation["first_unit"] + 1)
        if first:
            amount += pp[prefix + "setup_cost_minor"]
        funder = policy["technical_sponsor"]["party_id"] if agreement["kind"] == "TECHNICAL" else party_id
        hold_kind = "TECHNICAL" if agreement["kind"] == "TECHNICAL" else "WORKING" if attempt == 1 else "REWORK_LIABILITY"
        bound = {"agreement_id": aid, "production_id": pid, "lot_id": lid, "attempt": attempt}
        if (charge["provider_id"] != party_id or charge["charge_minor"] != amount or charge["funding_party_id"] != funder
                or type(charge["setup_charged"]) is not int or charge["setup_charged"] != int(first)
                or charge["request_sha256"] != digest(bound) or pid != f"{aid}.{lid}.A{attempt}"
                or (aid, lid, attempt) in seen_work or attempt == 2 and (aid, lid, 1) not in seen_work
                or _authorization_expected(contract, versions, proposals, agreement, party_id, "produce", charge["tick"]) != "AUTHORIZED"):
            findings.add("PRODUCTION_COST_INCORRECT", pid, scope="safety", arrangement_id=aid)
        if pid not in producer["records"]:
            findings.add("CHARGED_PRODUCTION_NOT_OBSERVED", pid, scope="outcome", arrangement_id=aid, unknown=True)
        first_groups.add(group)
        seen_work.add((aid, lid, attempt))
        costs[pid] = {"party_id": party_id, "funder": funder, "amount_minor": amount, "attempt": attempt}
        flow("production." + pid, aid, "BASE_COST" if attempt == 1 else "REWORK_COST", funder, "COST_SINK",
             amount, hold_kind, charge["tick"], {"lot_id": lid, "provider_id": party_id, "attempt": attempt,
                                                "setup_charged": first, "production_id": pid})
    for hid, expected in expected_holds.items():
        agreement = agreements[expected["agreement_id"]]
        if agreement["status"] not in {"SETTLED", "CANCELLED"}:
            continue
        aid, pid, kind = expected["agreement_id"], expected["party_id"], expected["kind"]
        spent = sum(e["amount_minor"] for e in expected_entries.values()
                    if e["agreement_id"] == aid and e["from_party"] == pid and e["hold_kind"] == kind
                    and e["kind"] not in {"HOLD", "RELEASE"})
        remaining = expected["initial_minor"] - spent
        tick = agreement["settled_tick"] if agreement["status"] == "SETTLED" else agreement["cancelled_tick"]
        if remaining < 0:
            findings.add("CONTRACT_FUNDS_EXCEEDED", aid, scope="safety", arrangement_id=aid)
        flow("release." + hid, aid, "RELEASE", pid, None, remaining, kind, tick)
    for event in events:
        if event["kind"] != "FUNDING_WITHDRAWN":
            continue
        data = object_fields(event["payload"], {"party_id", "amount_minor", "event_id"}, path="funding_event")
        if data["event_id"] != event["event_id"] or data["party_id"] in {"COST_SINK", "OUTSIDE_ACCOUNT"}:
            findings.add("FUNDING_EVENT_INVALID", event["event_id"], scope="safety")
        flow("withdraw." + event["event_id"], None, "WITHDRAWAL", data["party_id"], "OUTSIDE_ACCOUNT",
             data["amount_minor"], None, event["tick"])
    for eid in set(entries) | set(expected_entries):
        actual = entries.get(eid)
        expected = expected_entries.get(eid)
        if actual is None or expected is None or {key: value for key, value in actual.items() if key != "sequence"} != expected:
            findings.add("FINANCIAL_EFFECT_MISMATCH", eid, scope="safety", arrangement_id=(actual or expected).get("agreement_id"))
    actual_holds = money["holds"]
    if set(actual_holds) != set(expected_holds) or any(
            any(actual_holds[hid].get(key) != value for key, value in expected.items())
            for hid, expected in expected_holds.items() if hid in actual_holds):
        findings.add("CONTRACT_FUNDING_HOLDS_MISMATCH", scope="safety")

    # Campaign accounting includes abandoned agreements and rejected corrections.
    campaign = []
    payment_kinds = {"PROVIDER_PAYMENT", "COORDINATOR_PAYMENT", "CANCELLATION_PAYMENT"}
    cost_kinds = {"BASE_COST", "REWORK_COST", "COORDINATION_COST"}
    used_providers = {item["provider_id"] for item in capacity if any(
        row["status"] in {"COMMITTED", "FULFILLED"} for row in item["reservations"].values())}
    for pid, role in money["roles"].items():
        if pid in {"COST_SINK", "OUTSIDE_ACCOUNT"}:
            continue
        incoming = sum(e["amount_minor"] for e in money["entries"] if e["to_party"] == pid and e["kind"] in payment_kinds)
        expense = sum(e["amount_minor"] for e in money["entries"] if e["from_party"] == pid and e["kind"] in cost_kinds)
        purchases = sum(e["amount_minor"] for e in money["entries"] if e["from_party"] == pid and e["kind"] in payment_kinds)
        withdrawn = sum(e["amount_minor"] for e in money["entries"] if e["from_party"] == pid and e["kind"] == "WITHDRAWAL")
        active_policies = []
        for agreement in agreements.values():
            policy = versions[agreement["policy_revision"]]["payload"]
            if agreement["kind"] != "TRADE":
                continue
            selected = {item["party_id"] for item in agreement["independent_terms"]["providers"]}
            if role != "provider" or pid in selected:
                active_policies.append(_party(policy, pid)[0])
        threshold = max([max(p.get("min_profit_minor", 0), p.get("outside_profit_minor", 0)) for p in active_policies] or [0])
        participates = role == "provider" and (expense > 0 or incoming > 0 or pid in used_providers) or role == "coordinator" and (expense > 0 or incoming > 0)
        covers = incoming - expense >= threshold if participates else None
        if participates and not covers:
            findings.add("REALIZED_PARTICIPATION_NOT_COVERED", pid, scope="economic")
        campaign.append({"party_id": pid, "role": role, "initial_balance_minor": money["initial"][pid],
                         "final_balance_minor": money["balances"][pid], "funds_still_held_minor": money["held"][pid],
                         "revenue_minor": incoming, "incurred_cost_minor": expense,
                         "purchase_payments_minor": purchases, "withdrawn_minor": withdrawn,
                         "realized_profit_minor": incoming - expense if role in {"provider", "coordinator"} else None,
                         "participation_threshold_minor": threshold if participates else None,
                         "participation_covered": covers})
    buyer = original["buyer"]
    buyer_paid = sum(row["purchase_payments_minor"] for row in campaign if row["party_id"] == buyer["party_id"])
    trade_settled = any(a["kind"] == "TRADE" and a["status"] == "SETTLED" for a in agreements.values())
    buyer_values = [versions[a["policy_revision"]]["payload"]["buyer"] for a in agreements.values()
                    if a["kind"] == "TRADE" and a["status"] == "SETTLED"]
    realized_buyer = "NOT_ESTABLISHED"
    if buyer_values:
        policy = buyer_values[-1]
        low, high = policy["value_min_minor"] - buyer_paid, policy["value_max_minor"] - buyer_paid
        realized_buyer = ("FAILED" if high < policy["outside_utility_minor"] or buyer_paid > policy["max_price_minor"]
                          else "DEMONSTRATED" if low >= policy["outside_utility_minor"] else "NOT_ESTABLISHED")
        if realized_buyer == "FAILED":
            findings.add("REALIZED_BUYER_OUTSIDE_OPTION", buyer["party_id"], scope="economic")
    else:
        low = high = None
    for row in rows:
        own = [e for e in money["entries"] if e["agreement_id"] == row["agreement_id"]]
        row["incurred_cost_minor"] = sum(e["amount_minor"] for e in own if e["kind"] in cost_kinds)
        row["correction_cost_minor"] = sum(e["amount_minor"] for e in own if e["kind"] == "REWORK_COST")
        row["payments_minor"] = sum(e["amount_minor"] for e in own if e["kind"] in payment_kinds)
        row["realized_feasibility"] = ("FAILED" if row["kind"] == "TECHNICAL" or row["status"] == "CANCELLED"
                                      else "DEMONSTRATED" if row["status"] == "SETTLED" and realized_buyer == "DEMONSTRATED"
                                      and not findings.failed("economic", "safety", "integrity", "outcome")
                                      and not findings.missing("economic", "safety", "integrity", "outcome") else "NOT_ESTABLISHED")
    for pid, record in proposals.items():
        if any(row["proposal_id"] == pid for row in rows):
            continue
        ds = record.get("independent_decisions", [])
        ex_ante = ("FAILED" if any(d["verdict"] == "REJECTED" for d in ds)
                   else "DEMONSTRATED" if ds and all(d["verdict"] == "ACCEPTED" for d in ds) else "NOT_ESTABLISHED")
        rows.append({"proposal_id": pid, "agreement_id": None, "kind": "PROPOSAL", "status": record["status"],
                     "proposed_terms": record["payload"], "participant_decisions": ds,
                     "independent_terms": record.get("independent_terms"), "ex_ante_feasibility": ex_ante,
                     "realized_feasibility": "FAILED" if ex_ante == "FAILED" else "NOT_ESTABLISHED",
                     "acceptance_ids": [], "incurred_cost_minor": 0, "correction_cost_minor": 0, "payments_minor": 0})
    return {"arrangements": sorted(rows, key=lambda row: row["proposal_id"]), "trade_settled": trade_settled,
            "realized_buyer": realized_buyer, "currency": "SMU", "scope": "AUTHORED_SYNTHETIC_MODEL",
            "campaign": campaign, "buyer_utility_interval_minor": {"minimum": low, "maximum": high},
            "buyer_total_paid_minor": buyer_paid,
            "total_incurred_cost_minor": sum(row["incurred_cost_minor"] for row in campaign),
            "total_correction_cost_minor": sum(e["amount_minor"] for e in money["entries"] if e["kind"] == "REWORK_COST"),
            "total_transfers_minor": sum(e["amount_minor"] for e in money["entries"] if e["kind"] in payment_kinds),
            "initial_total_minor": sum(money["initial"].values()), "final_total_minor": sum(money["balances"].values()),
            "real_contracts_payments_or_demand": "NOT_ESTABLISHED"}


def _obligation_results(contract: dict | None, producer: dict | None, receiver: dict | None,
                        findings: Findings, *, incomplete: bool, not_run: bool) -> list[dict]:
    result = []
    for order in (contract or {}).get("obligations", []):
        oid = order["obligation_id"]
        produced = [row for row in (producer or {}).get("records", {}).values() if row["obligation_id"] == oid]
        receipts = [row for row in (receiver or {}).get("receipts", {}).values() if row["obligation_id"] == oid]
        decisions = [row for row in (receiver or {}).get("decisions", {}).values() if row["obligation_id"] == oid]
        required = order["quantity"] if order["status"] == "ACTIVE" else 0
        semantic_count = sum(key[0] == oid for key in (receiver or {}).get("accepted_units", {}))
        timely_count = sum(key[0] == oid for key in (receiver or {}).get("timely_units", {}))
        scoped_failures = [row for row in findings.failures if row.get("obligation_id") == oid]
        scoped_missing = [row for row in findings.unresolved if row.get("obligation_id") == oid]
        if findings.failed("integrity", "safety") or findings.missing("integrity") or scoped_failures or scoped_missing:
            qualified_count = 0
        else:
            qualified_count = timely_count
        if not_run or incomplete and receiver is None or findings.missing("integrity") or scoped_missing:
            outcome = "UNRESOLVED"
        elif scoped_failures:
            outcome = "LATE" if oid in (receiver or {}).get("late_obligations", set()) else "INCORRECT"
        elif order["status"] == "CANCELLED":
            outcome = "CANCELLED" if not semantic_count else "INCORRECT"
        elif qualified_count == required:
            outcome = "COMPLETED"
        elif qualified_count:
            outcome = "PARTIAL"
        else:
            outcome = "UNFULFILLED"
        def observed_labels(delivery_id):
            document = (receiver or {}).get("inspections", {}).get(delivery_id, {}).get("product")
            return len(document["labels"]) if type(document) is dict and type(document.get("labels")) is list else 0
        rejected = [row for row in decisions if row["decision"] == "REJECTED"]
        result.append({"obligation_id": oid, "recipient": order["recipient"], "revision": order["revision"],
                       "quantity": order["quantity"], "required_quantity": required,
                       "deadline_tick": order["deadline_tick"], "status": order["status"], "outcome": outcome,
                       "produced_quantity": sum(row["generated_units"] or 0 for row in produced),
                       "production_attempts": len(produced), "delivery_attempts": len(receipts),
                       "received_quantity": sum(observed_labels(row["delivery_id"]) for row in receipts),
                       "rejected_quantity": sum(observed_labels(row["delivery_id"]) for row in rejected),
                       "rejected_requested_quantity": sum(row["quantity"] for row in rejected),
                       "rejection_count": len(rejected), "recipient_accepted_quantity": semantic_count,
                       "timely_semantic_quantity": timely_count, "accepted_quantity": qualified_count,
                       "missing_quantity": max(0, required - qualified_count),
                       "late_quantity": max(0, semantic_count - timely_count),
                       "reason_codes": sorted({row["code"] for row in scoped_failures + scoped_missing})})
    return result


def verify_run(run_dir: str | Path, authority_dir: str | Path, *,
               expected_reference_sha256: str | None = None) -> dict:
    """Read retained authority and durable execution afresh; never writes evidence.

    ``expected_reference_sha256`` must come from trusted custody, separately from
    candidate files.  Supplying the digest computed from an untrusted rewritten
    package does not establish original authority.  The host/controller custody
    assumptions are explicit in the returned record and threat model.
    """
    began, cpu_began = time.monotonic_ns(), time.process_time_ns()
    findings = Findings()
    contract = policies = reference = capacity_inputs = controller = None
    producer = receiver = participants = accounting = None
    capacity, evidence_hashes, required_db_paths = [], {}, set()
    not_run, completed_read = False, False
    root, authority = Path(run_dir), Path(authority_dir)
    try:
        root, authority = _safe_path(root), _safe_path(authority)
        if authority == root / "candidate" or root / "candidate" in authority.parents:
            findings.add("AUTHORITY_IN_CANDIDATE_WORKSPACE")
        contract, policies, reference, capacity_inputs = _reference_check(root, authority, expected_reference_sha256, findings)
        controller = _controller(strict_load(root / "controller.json"))
        evidence_hashes = _seal_check(root, authority, contract, controller, findings)
        not_run = controller["state"] == "NOT_RUN"
        if contract is None or policies is None or reference is None or capacity_inputs is None:
            findings.add("AUTHORITY_UNAVAILABLE_FOR_VERIFICATION", unknown=True)
        else:
            _source_state(contract, findings)
            if (controller["run_id"] != contract["run_id"] or controller["contract_sha256"] != digest(contract)
                    or controller["policies_sha256"] != digest(policies)
                    or controller["fixture_id"] != contract["fixture_id"] or controller["cohort"] != contract["cohort"]
                    or controller["started_monotonic_ns"] < contract["start_ns"]
                    or controller["fault_schedule"] != contract["fault_schedule"]):
                findings.add("CONTROLLER_AUTHORITY_BINDING")
            if controller["clock_tick"] > contract["observation_cutoff_tick"]:
                findings.add("OBSERVATION_CUTOFF_EXCEEDED", scope="outcome")
            observed_faults = controller["faults_observed"]
            if len({digest(item) for item in observed_faults}) != len(observed_faults) or any(
                    item not in contract["fault_schedule"] for item in observed_faults):
                findings.add("UNREGISTERED_FAULT_OBSERVATION")
            if not_run:
                if evidence_hashes or controller["capacity_databases"] or controller["db_snapshots"]:
                    findings.add("NOT_RUN_WITH_EXECUTION_EVIDENCE")
                completed_read = True
            else:
                if (controller["isolation"].get("applied") is not True
                        or controller["isolation"].get("mechanism") != "SECCOMP_BPF"
                        or set(controller["isolation"].get("probe", {})) != PROBE_NAMES
                        or any(controller["isolation"]["probe"].get(key) is not True for key in PROBE_NAMES)):
                    findings.add("CANDIDATE_ISOLATION_NOT_ESTABLISHED", unknown=True)
                if controller["state"] != "COMPLETE" or controller["errors"]:
                    findings.add("EXECUTION_INCOMPLETE", scope="outcome", unknown=True)
                expected_inputs = {provider["provider_id"] + "." + window["window_id"]
                                   for provider in contract["providers"] for window in provider["windows"]}
                if set(capacity_inputs) != expected_inputs:
                    findings.add("CAPACITY_INPUT_INVENTORY")
                expected_databases = []
                for provider in contract["providers"]:
                    for window in provider["windows"]:
                        key = provider["provider_id"] + "." + window["window_id"]
                        path = "evidence/capacity/" + key + ".sqlite"
                        expected_databases.append({"provider_id": provider["provider_id"], "window_id": window["window_id"],
                                                   "route": "primary" if provider["role"] == "primary" else "backup", "path": path})
                        required_db_paths.add(path)
                        if key in capacity_inputs:
                            capacity.append(_capacity_database(root, contract, provider, window, capacity_inputs[key], controller, findings))
                if sorted(controller["capacity_databases"], key=lambda row: row["path"]) != sorted(expected_databases, key=lambda row: row["path"]):
                    findings.add("CAPACITY_DATABASE_INVENTORY")
                required_db_paths |= {"evidence/participants.sqlite", "evidence/producer.sqlite", "evidence/receiver.sqlite"}
                if set(controller["db_snapshots"]) != required_db_paths:
                    findings.add("DATABASE_SNAPSHOT_INVENTORY", unknown=True)
                for path in required_db_paths:
                    if path not in evidence_hashes:
                        findings.add("DATABASE_EVIDENCE_MISSING", path, unknown=True)
                    actual = _logical_database_hash(_evidence_path(root, path))
                    if controller["db_snapshots"].get(path) != actual:
                        findings.add("DATABASE_FINALIZATION_CHANGED", path)
                participants = _participants_data(root, contract, policies, findings)
                _controller_effects(contract, policies, controller, participants, findings)
                # Distinct agreements may replace undelivered abandoned work
                # after cancellation.  Both capacity consumption and sunk costs
                # remain.  They may never concurrently own the same obligation.
                live_by_order = {}
                for item in capacity:
                    for key, row in item["reservations"].items():
                        agreement = next((a for aid, a in participants["agreements"].items()
                                          if key == aid + "." + row["order_id"]), None)
                        if agreement is None:
                            findings.add("CAPACITY_AGREEMENT_MISSING", key, scope="safety")
                            continue
                        allocation = next((a for a in participants["proposals"][agreement["proposal_id"]]["payload"]["allocations"]
                                           if row["order_id"].startswith(a["lot_id"] + ".A")), None)
                        if (allocation is None or allocation["provider_id"] != item["provider_id"]
                                or allocation["window_id"] != item["window_id"]
                                or _authorization_expected(contract, participants["versions"], participants["proposals"],
                                                           agreement, item["provider_id"], "produce", row["created_tick"]) != "AUTHORIZED"):
                            findings.add("UNAUTHORIZED_CAPACITY_ALLOCATION", key, scope="safety")
                        if agreement["cancelled_tick"] is not None and row["status"] in {"RESERVED", "COMMITTED"}:
                            findings.add("CANCELLED_CAPACITY_NOT_RELEASED", key, scope="safety")
                        terminal = (row["updated_tick"] if row["status"] in {"RELEASED", "EXPIRED"}
                                    else agreement["cancelled_tick"] if agreement["cancelled_tick"] is not None
                                    else contract["observation_cutoff_tick"] + 1)
                        prior = live_by_order.setdefault(row["order_id"], [])
                        for other, other_terminal in prior:
                            if max(row["created_tick"], other["created_tick"]) < min(terminal, other_terminal):
                                findings.add("CROSS_PROVIDER_CONCURRENT_CAPACITY", row["order_id"], scope="safety")
                        prior.append((row, terminal))
                producer = _producer_data(root, contract, controller, capacity, participants, findings)
                receiver = _receiver_data(root, contract, controller, producer, participants, findings)
                accounting = _financial_semantics(contract, policies, participants, producer, receiver, capacity, findings)
                completed_read = True
        for relative, before in evidence_hashes.items():
            if _hash_file(_evidence_path(root, relative)) != before:
                findings.add("EVIDENCE_CHANGED_DURING_VERIFICATION", relative)
        if controller is not None and digest(strict_load(root / "controller.json")) != digest(controller):
            findings.add("EVIDENCE_CHANGED_DURING_VERIFICATION", "controller.json")
        if reference is not None and digest(strict_load(authority / "reference.json")) != digest(reference):
            findings.add("EVIDENCE_CHANGED_DURING_VERIFICATION", "reference.json")
    except HarnessError as exc:
        findings.add("VERIFICATION_EVIDENCE_MISSING" if exc.code == "MISSING_FILE" else "VERIFICATION_REFUSED",
                     exc.code + (":" + str(exc.detail) if getattr(exc, "detail", "") else ""),
                     unknown=exc.code == "MISSING_FILE")
    except (OSError, sqlite3.Error) as exc:
        findings.add("VERIFICATION_IO_INCOMPLETE", type(exc).__name__, unknown=True)
    except Exception as exc:
        # A verifier defect is never converted to success.  The stable code and
        # exception class make the incomplete attempt inspectable without
        # exposing arbitrary local exception contents.
        findings.add("VERIFIER_FAILURE", type(exc).__name__, unknown=True)
    incomplete = not completed_read or findings.missing("integrity", "outcome")
    obligations = _obligation_results(contract, producer, receiver, findings, incomplete=incomplete, not_run=not_run)
    required = sum(row["required_quantity"] for row in obligations)
    accepted = sum(row["accepted_quantity"] for row in obligations)
    if not_run:
        outcome = feasibility = safety = "NOT_ESTABLISHED"
    else:
        if findings.failed("integrity", "safety", "outcome"):
            outcome = "FAILED"
        elif incomplete:
            outcome = "NOT_ESTABLISHED"
        else:
            outcome = "DEMONSTRATED" if required > 0 and accepted == required else "FAILED"
        safety = ("FAILED" if findings.failed("safety", "integrity") else
                  "NOT_ESTABLISHED" if incomplete else "DEMONSTRATED")
        if controller and controller["method"] in {"outside", "no_action", "ai"}:
            feasibility = "NOT_ESTABLISHED"
        elif findings.failed("integrity", "safety", "economic"):
            feasibility = "FAILED"
        elif incomplete or accounting is None:
            feasibility = "NOT_ESTABLISHED"
        elif contract["mode"] == "technical_control":
            feasibility = "FAILED"
        elif accounting["trade_settled"] and accounting["realized_buyer"] == "DEMONSTRATED" and outcome == "DEMONSTRATED":
            feasibility = "DEMONSTRATED"
        elif any(row["ex_ante_feasibility"] == "NOT_ESTABLISHED" for row in accounting["arrangements"]):
            feasibility = "NOT_ESTABLISHED"
        elif accounting["arrangements"]:
            feasibility = "FAILED"
        else:
            upper = sum(window["capacity"] for provider in contract["providers"]
                        if provider["dependency"] not in contract["blocked_dependencies"]
                        and provider["permissions"]["production"] and (provider["role"] == "primary" or provider["permissions"]["disclosure"])
                        for window in provider["windows"] if window["start"] <= contract["deadline_tick"])
            feasibility = "FAILED" if upper < required else "NOT_ESTABLISHED"
    authority_codes = {"AUTHORITY_MISSING", "AUTHORITY_INVALID", "REFERENCE_PIN_MISSING", "REFERENCE_PIN_MISMATCH",
                       "AUTHORITY_BINDING", "SOURCE_INCOMPLETE", "SOURCE_OBLIGATION_MISMATCH", "AUTHORITY_IN_CANDIDATE_WORKSPACE"}
    authority_status = ("FAILED" if any(row["code"] in authority_codes for row in findings.failures) else
                        "NOT_ESTABLISHED" if not contract or not reference or any(row["code"] in authority_codes for row in findings.unresolved)
                        else "ESTABLISHED_FOR_SYNTHETIC_EXERCISE")
    if authority_status == "NOT_ESTABLISHED":
        outcome = feasibility = safety = "NOT_ESTABLISHED"
    totals = {name: sum(row[name] for row in obligations) for name in (
        "required_quantity", "produced_quantity", "production_attempts", "delivery_attempts", "received_quantity", "rejected_quantity",
        "rejected_requested_quantity", "rejection_count", "recipient_accepted_quantity", "timely_semantic_quantity",
        "accepted_quantity", "missing_quantity", "late_quantity")}
    totals["accepted_obligations"] = sum(row["outcome"] == "COMPLETED" for row in obligations)
    totals["required_obligations"] = sum(row["status"] == "ACTIVE" for row in obligations)
    totals["duplicate_acceptances"] = sum(row["code"] == "DUPLICATE_RECIPIENT_ACCEPTANCE" for row in findings.failures)
    totals["unsafe_or_unsupported_commitments"] = sum(row["scope"] == "safety" for row in findings.failures)
    result = {"schema": "continuity-economy/verification/v1", "verifier_version": VERSION,
              "run_id": (contract or controller or {}).get("run_id"),
              "contract_sha256": digest(contract) if contract else None,
              "reference_sha256": digest(reference) if reference else None,
              "authority_status": authority_status, "verification_status": "INCOMPLETE" if incomplete else "COMPLETE",
              "assessment": {"test_assertion": "NOT_RUN" if not_run else "NOT_EVALUATED",
                             "target_verdict": (controller or {}).get("target_verdict", "NOT_ESTABLISHED"),
                             "evidence_stage": "NOT_RUN" if not_run else "LOCAL_DIGITAL_PRODUCT_EXECUTION" if completed_read else "VERIFICATION_ATTEMPT",
                             "claim_status": outcome},
              "claims": {"outcome": outcome, "service_feasibility": feasibility, "method_advantage": "NOT_ESTABLISHED"},
              "safety_status": safety, "per_obligation": obligations,
              "per_arrangement": (accounting or {}).get("arrangements", []), "totals": totals,
              "accounting": {key: value for key, value in (accounting or {}).items() if key != "arrangements"},
              "failures": findings.failures, "unresolved": findings.unresolved,
              "resources": (controller or {}).get("resources", {}),
              "verification_resources": {"wall_ns": time.monotonic_ns() - began, "cpu_ns": time.process_time_ns() - cpu_began,
                                          "evidence_files_read": len(evidence_hashes)},
              "accounting_gaps": ["PREPARATION_LABOR_NOT_MEASURED", "INTEGRATION_LABOR_NOT_MEASURED",
                                  "ADAPTATION_LABOR_NOT_MEASURED", "VERIFICATION_LABOR_NOT_MEASURED", "MONETARY_RATES_NOT_MEASURED",
                                  "REPORTING_AND_FINAL_SEAL_OVERHEAD_NOT_MEASURED"],
              "evidence_sha256": evidence_hashes, "implementation": (controller or {}).get("implementation", {}),
              "fault_schedule": (controller or {}).get("fault_schedule", []),
              "faults_observed": (controller or {}).get("faults_observed", []),
              "untriggered_faults": [row for row in (controller or {}).get("fault_schedule", [])
                                     if row not in (controller or {}).get("faults_observed", [])],
              "commercial_value": "NOT_ESTABLISHED", "real_customer_authenticity": "NOT_ESTABLISHED",
              "trust_assumptions": ["TRUSTED_HOST_KERNEL_CONTROLLER_CLOCK", "TRUSTED_RETAINED_SYNTHETIC_AUTHORITY",
                                    "SHARED_AUTHORSHIP_NOT_THIRD_PARTY_CERTIFICATION", "SEMANTIC_CONTENT_ONLY_NOT_PHYSICAL_DELIVERY"]}
    return result

