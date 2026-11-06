"""Fresh acceptance against retained authority and durable local effects.

This module deliberately does not import the candidate, controller, historical
engine, or service replay.  It reads final files and a read-only SQLite snapshot,
replays ledger transitions independently, and never trusts a saved Passport.
The trusted host/controller, authored source-completeness declaration and clock
remain assumptions; neither a digest nor this verifier authenticates customers.
"""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
import re
import sqlite3
from typing import Any

from .schema import (
    HarnessError, MAX_EVENTS, MAX_INTEGER, MAX_JSON_BYTES, MAX_NS, MAX_ORDERS,
    MAX_UNITS, MAX_TICKS, canonical, digest, identifier, integer,
    object_fields, read_bytes, sha256, strict_load, strict_loads,
    validate_artifact, validate_contract, validate_reference,
)


VERSION = "0.1.0"
MAX_DATABASE_BYTES = 67_108_864
MAX_HISTORY = 50_000
ACTIVE = {"RESERVED", "COMMITTED", "FULFILLED"}
RESERVATION_FIELDS = {
    "key", "run_id", "contract_sha256", "order_id", "recipient", "product",
    "spec_sha256", "quantity", "route", "window_start", "window_end",
    "expires_tick", "status", "request_sha256", "created_tick", "updated_tick",
}
ORDER_FIELDS = {"order_id", "recipient", "product", "spec_sha256", "quantity", "deadline_tick"}


REASONS = {
    "AUTHORITY_MISSING": ("The retained authority is missing.", "L’autorité conservée est absente."),
    "REFERENCE_PIN_MISSING": ("No independently retained reference digest was supplied.", "Aucune empreinte de référence conservée séparément n’a été fournie."),
    "REFERENCE_PIN_MISMATCH": ("The reference differs from the independently retained digest.", "La référence diffère de l’empreinte conservée séparément."),
    "AUTHORITY_INVALID": ("The retained authority is malformed or unsupported.", "L’autorité conservée est mal formée ou non prise en charge."),
    "CONTRACT_BINDING": ("The retained reference does not bind this contract and source.", "La référence conservée ne correspond pas à ce contrat et à cette source."),
    "SOURCE_INCOMPLETE": ("Required source-completeness evidence is absent.", "La preuve requise d’exhaustivité de la source est absente."),
    "SOURCE_JOURNAL_MISSING": ("The protected source journal is missing.", "Le journal source protégé est absent."),
    "SOURCE_JOURNAL_MISMATCH": ("The protected journal differs from the retained source.", "Le journal protégé diffère de la source conservée."),
    "NO_OBLIGATIONS_IN_SCOPE": ("No outstanding obligation is available for this exercise.", "Aucune obligation restante n’est disponible pour cet exercice."),
    "CONTROLLER_MISSING": ("The completed controller record is missing.", "Le compte rendu achevé du contrôleur est absent."),
    "CONTROLLER_INVALID": ("The controller record is malformed or unsupported.", "Le compte rendu du contrôleur est mal formé ou non pris en charge."),
    "CONTROLLER_BINDING": ("The controller record belongs to another contract or run.", "Le compte rendu du contrôleur appartient à un autre contrat ou exercice."),
    "EXECUTION_INCOMPLETE": ("The exercise did not finish normally.", "L’exercice ne s’est pas terminé normalement."),
    "NOT_RUN": ("This method was not run.", "Cette méthode n’a pas été exécutée."),
    "ISOLATION_NOT_ESTABLISHED": ("The required candidate isolation was not established.", "L’isolation requise du candidat n’a pas été établie."),
    "FAULT_SCHEDULE_CHANGED": ("The executed fault schedule differs from the frozen schedule.", "Le calendrier des défaillances exécuté diffère du calendrier figé."),
    "FAULT_NOT_OBSERVED": ("A scheduled fault was not observed.", "Une défaillance prévue n’a pas été observée."),
    "EXECUTION_SEAL_MISSING": ("The separately retained execution seal is missing.", "Le sceau d’exécution conservé séparément est absent."),
    "EXECUTION_SEAL_INVALID": ("The execution seal is malformed or unsupported.", "Le sceau d’exécution est mal formé ou non pris en charge."),
    "EXECUTION_SEAL_BINDING": ("The execution seal does not bind this run and controller.", "Le sceau d’exécution ne correspond pas à cet exercice et à ce contrôleur."),
    "EVIDENCE_MISSING": ("A required sealed evidence file is missing.", "Un fichier de preuve scellé requis est absent."),
    "EVIDENCE_CHANGED": ("Current evidence differs from the separately retained execution seal.", "Les preuves actuelles diffèrent du sceau d’exécution conservé séparément."),
    "EVIDENCE_CHANGED_DURING_VERIFICATION": ("Evidence changed during fresh verification.", "Les preuves ont changé pendant la vérification actualisée."),
    "UNSEALED_EVIDENCE": ("An evidence file is not covered by the execution seal.", "Un fichier de preuve n’est pas couvert par le sceau d’exécution."),
    "UNSAFE_EVIDENCE_PATH": ("An evidence path is unsafe or contains a symbolic link.", "Un chemin de preuve n’est pas sûr ou contient un lien symbolique."),
    "DATABASE_MISSING": ("The durable service database is missing.", "La base de données durable du service est absente."),
    "DATABASE_NOT_CHECKPOINTED": ("The final database still has an unapplied journal.", "La base de données finale contient encore un journal non intégré."),
    "DATABASE_INVALID": ("The durable database is malformed or inconsistent.", "La base de données durable est mal formée ou incohérente."),
    "DATABASE_BINDING": ("The database belongs to another contract or run.", "La base de données appartient à un autre contrat ou exercice."),
    "AUTHORIZED_ORDERS_CHANGED": ("Service admission differs from the retained obligations.", "Les obligations admises par le service diffèrent des obligations conservées."),
    "PRIMARY_NOT_RECOVERED": ("The primary order database was not correctly reconstructed.", "La base de commandes principale n’a pas été correctement reconstruite."),
    "ARTIFACT_INVALID": ("A fulfillment artifact is malformed or unsupported.", "Une pièce de réalisation est mal formée ou non prise en charge."),
    "ARTIFACT_BINDING": ("An artifact belongs to another contract, run, or obligation.", "Une pièce appartient à un autre contrat, exercice ou obligation."),
    "UNKNOWN_OBLIGATION": ("Completed work has no outstanding authorized obligation.", "Le travail réalisé ne correspond à aucune obligation autorisée restante."),
    "WRONG_RECIPIENT": ("The output names the wrong recipient.", "Le résultat désigne le mauvais destinataire."),
    "WRONG_PRODUCT": ("The output names the wrong product.", "Le résultat désigne le mauvais produit."),
    "WRONG_SPECIFICATION": ("The output uses the wrong final specification.", "Le résultat utilise une spécification finale incorrecte."),
    "WRONG_QUANTITY": ("The output quantity does not match the final obligation.", "La quantité du résultat ne correspond pas à l’obligation finale."),
    "DUPLICATE_FULFILLMENT": ("The same obligation has multiple completed outputs.", "La même obligation possède plusieurs résultats réalisés."),
    "RECEIPT_MISMATCH": ("The artifact does not match a durable committed receipt.", "La pièce ne correspond pas à un reçu engagé durablement."),
    "ARTIFACT_MISSING": ("A durable receipt has no complete exported artifact.", "Un reçu durable ne possède aucune pièce exportée complète."),
    "NO_DURABLE_OUTPUT": ("No accepted durable output exists for this obligation.", "Aucun résultat durable accepté n’existe pour cette obligation."),
    "RESERVATION_MISSING": ("Completed work has no matching fulfilled allocation.", "Le travail réalisé ne possède aucune allocation réalisée correspondante."),
    "RESERVATION_BINDING": ("An allocation changes the authorized obligation or run.", "Une allocation modifie l’obligation autorisée ou l’exercice."),
    "UNAUTHORIZED_ROUTE": ("The route is outside the frozen authorization.", "La voie dépasse l’autorisation figée."),
    "UNAUTHORIZED_ACTIVATION": ("Execution occurred without activation permission.", "L’exécution a eu lieu sans autorisation d’activation."),
    "UNAUTHORIZED_SHARING": ("The backup route was used without sharing permission.", "La voie de secours a été utilisée sans autorisation de partage."),
    "FAILED_DEPENDENCY": ("The route depends on a declared failed dependency.", "La voie dépend d’une dépendance déclarée défaillante."),
    "LATE_COMPLETION": ("Completion exceeded the logical deadline or capacity window.", "La réalisation dépasse l’échéance logique ou la fenêtre de capacité."),
    "WALL_DEADLINE_EXCEEDED": ("Measured completion exceeded the wall-clock deadline.", "La durée mesurée de réalisation dépasse l’échéance réelle."),
    "DURABLE_OBSERVATION_MISSING": ("No matching post-export observation establishes durable completion time.", "Aucune observation correspondante après exportation n’établit la durée de réalisation durable."),
    "CLOCK_OUTSIDE_RUN": ("An observed time lies outside the recorded exercise.", "Une heure observée se situe hors de l’exercice enregistré."),
    "RECOVERY_TIME_MISSING": ("A measured recovery time was not recorded.", "Aucune durée de reprise mesurée n’a été enregistrée."),
    "RECOVERY_OBJECTIVE_EXCEEDED": ("Measured recovery exceeded its frozen objective.", "La reprise mesurée dépasse son objectif figé."),
    "LEDGER_HISTORY_INVALID": ("The durable allocation history is incomplete or inconsistent.", "L’historique durable des allocations est incomplet ou incohérent."),
    "ILLEGAL_TRANSITION": ("An allocation made an illegal durable transition.", "Une allocation a effectué une transition durable interdite."),
    "CAPACITY_EXCEEDED": ("Simultaneous allocated capacity exceeded its declared limit.", "La capacité allouée simultanément dépasse sa limite déclarée."),
    "CAPACITY_AUTHORITY_CHANGED": ("Capacity was increased beyond the frozen resources.", "La capacité a été augmentée au-delà des ressources figées."),
    "WITHDRAWN_ROUTE_USED": ("New work used a withdrawn route.", "Un nouveau travail utilise une voie retirée."),
    "ALL_OBLIGATIONS_NOT_COMPLETED": ("The complete customer promise was not fulfilled.", "La promesse complète au client n’a pas été tenue."),
    "VERIFICATION_ERROR": ("Fresh verification did not complete; no favorable conclusion is available.", "La vérification actualisée n’a pas abouti ; aucune conclusion favorable n’est disponible."),
}

# A missed business goal is reported separately from a safety violation.
SAFETY_CODES = {
    "ARTIFACT_BINDING", "UNKNOWN_OBLIGATION", "WRONG_RECIPIENT", "WRONG_PRODUCT",
    "WRONG_SPECIFICATION", "WRONG_QUANTITY", "DUPLICATE_FULFILLMENT", "RESERVATION_BINDING",
    "UNAUTHORIZED_ROUTE", "UNAUTHORIZED_ACTIVATION", "UNAUTHORIZED_SHARING", "FAILED_DEPENDENCY",
    "ILLEGAL_TRANSITION", "CAPACITY_EXCEEDED", "CAPACITY_AUTHORITY_CHANGED", "WITHDRAWN_ROUTE_USED",
}


class _Findings:
    def __init__(self) -> None:
        self.failures: list[dict] = []
        self.unresolved: list[dict] = []
        self._seen = set()

    def add(self, code: str, detail: str = "", order_id: str | None = None, unknown: bool = False) -> None:
        identity = (code, detail, order_id, unknown)
        if identity in self._seen:
            return
        self._seen.add(identity)
        row = {"code": code, "detail": detail}
        if order_id is not None:
            row["order_id"] = order_id
        (self.unresolved if unknown else self.failures).append(row)


def _safe_root(path: Path) -> Path:
    absolute = path.absolute()
    for candidate in (absolute, *absolute.parents):
        if candidate.is_symlink():
            raise HarnessError("UNSAFE_PATH", candidate.name)
    return absolute


def _safe_child(root: Path, relative: str) -> Path:
    if type(relative) is not str or "\\" in relative:
        raise HarnessError("UNSAFE_PATH", "manifest")
    pieces = PurePosixPath(relative)
    if pieces.is_absolute() or not pieces.parts or any(p in ("", ".", "..") or re.fullmatch(r"[A-Za-z0-9_.-]+", p) is None for p in pieces.parts):
        raise HarnessError("UNSAFE_PATH", "manifest")
    if not relative.startswith("evidence/") or pieces.as_posix() != relative:
        raise HarnessError("UNSAFE_PATH", "manifest")
    child = root.joinpath(*pieces.parts)
    _safe_root(child)
    return child


def _file_hash(path: Path) -> str:
    return hashlib.sha256(read_bytes(path, MAX_DATABASE_BYTES)).hexdigest()


def _controller(value: Any) -> dict:
    required = {"schema", "run_id", "contract_sha256", "method", "scenario", "seed", "state",
                "started_monotonic_ns", "finished_monotonic_ns", "started_utc", "implementation",
                "isolation", "fault_schedule", "faults_observed", "events", "errors", "target_verdict",
                "resources", "recovery_ms"}
    c = object_fields(value, required, path="controller")
    if c["schema"] != "continuity-harness/controller/v1":
        raise HarnessError("UNSUPPORTED_VERSION", "controller")
    for key in ("run_id", "method", "scenario", "target_verdict"):
        identifier(c[key], "controller." + key)
    sha256(c["contract_sha256"], "controller.contract_sha256")
    integer(c["seed"], "controller.seed")
    if c["state"] not in ("COMPLETE", "INCOMPLETE", "ERROR", "NOT_RUN"):
        raise HarnessError("INVALID_TYPE", "controller.state")
    integer(c["started_monotonic_ns"], "controller.started_monotonic_ns", 0, MAX_NS)
    integer(c["finished_monotonic_ns"], "controller.finished_monotonic_ns", 0, MAX_NS)
    if c["finished_monotonic_ns"] < c["started_monotonic_ns"]:
        raise HarnessError("INVALID_RANGE", "controller.clock")
    if type(c["started_utc"]) is not str or len(c["started_utc"]) > 64:
        raise HarnessError("INVALID_TYPE", "controller.started_utc")
    implementation = object_fields(c["implementation"], {"version", "git_commit", "dirty", "source_sha256"}, {"environment"}, "controller.implementation")
    if type(implementation["version"]) is not str or type(implementation["git_commit"]) is not str or type(implementation["dirty"]) is not bool:
        raise HarnessError("INVALID_TYPE", "controller.implementation")
    if type(implementation["source_sha256"]) is not dict or len(implementation["source_sha256"]) > 256:
        raise HarnessError("INVALID_TYPE", "controller.implementation.source_sha256")
    for name, checksum in implementation["source_sha256"].items():
        if type(name) is not str or len(name) > 256:
            raise HarnessError("UNSAFE_PATH", "controller.source")
        sha256(checksum, "controller.source")
    if "environment" in implementation:
        environment = object_fields(implementation["environment"], {"python", "platform", "sqlite_version"}, {"argv", "working_directory"}, "controller.implementation.environment")
        if any(type(environment[key]) is not str or len(environment[key]) > 512 for key in ("python", "platform", "sqlite_version")):
            raise HarnessError("INVALID_TYPE", "controller.implementation.environment")
        if "argv" in environment and (type(environment["argv"]) is not list or len(environment["argv"]) > 128 or any(type(arg) is not str or len(arg) > 4096 for arg in environment["argv"])):
            raise HarnessError("INVALID_TYPE", "controller.implementation.environment.argv")
        if "working_directory" in environment and (type(environment["working_directory"]) is not str or len(environment["working_directory"]) > 4096):
            raise HarnessError("INVALID_TYPE", "controller.implementation.environment.working_directory")
    isolation = object_fields(c["isolation"], {"mechanism", "applied", "probe"}, path="controller.isolation")
    if type(isolation["mechanism"]) is not str or type(isolation["applied"]) is not bool:
        raise HarnessError("INVALID_TYPE", "controller.isolation")
    probe_fields = {"authority_open_denied", "workspace_open_denied", "network_denied", "spawn_denied", "process_inspection_denied"}
    probes = object_fields(isolation["probe"], set(), probe_fields, "controller.isolation.probe")
    if any(type(v) is not bool for v in probes.values()):
        raise HarnessError("INVALID_TYPE", "controller.isolation.probe")
    for key in ("fault_schedule", "faults_observed", "events", "errors"):
        if type(c[key]) is not list or len(c[key]) > MAX_HISTORY:
            raise HarnessError("INVALID_TYPE", "controller." + key)
    metrics = object_fields(c["resources"], {"wall_ns", "cpu_user_ns", "cpu_system_ns", "peak_rss_bytes", "storage_bytes", "requests", "retries", "worker_restarts", "human_interventions", "preparation_labor_seconds", "integration_labor_seconds", "monetary_cost"}, {"controller_cpu_user_ns", "controller_cpu_system_ns"}, "controller.resources")
    for key, number in metrics.items():
        if key in {"peak_rss_bytes", "preparation_labor_seconds", "integration_labor_seconds", "monetary_cost"} and number is None:
            continue
        integer(number, "controller.resources." + key, 0, MAX_NS)
    if c["recovery_ms"] is not None:
        integer(c["recovery_ms"], "controller.recovery_ms", 0, MAX_INTEGER)
    return c


def _read_database(path: Path) -> dict:
    _safe_root(path)
    read_bytes(path, MAX_DATABASE_BYTES)
    for suffix in ("-wal", "-journal"):
        journal = Path(str(path) + suffix)
        if journal.exists() and journal.stat().st_size:
            raise HarnessError("DATABASE_NOT_CHECKPOINTED", suffix)
    result = {}
    connection = sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only=ON")
        if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise HarnessError("DATABASE_INVALID", "quick_check")
        for table, limit in (("metadata", 64), ("routes", 2), ("authorized_orders", MAX_ORDERS),
                             ("orders", MAX_ORDERS), ("reservations", MAX_HISTORY),
                             ("receipts", MAX_ORDERS), ("history", MAX_HISTORY)):
            rows = [dict(r) for r in connection.execute("SELECT * FROM " + table + " LIMIT ?", (limit + 1,))]
            if len(rows) > limit:
                raise HarnessError("INVALID_RANGE", table)
            result[table] = rows
        result["metadata"] = {row["key"]: strict_loads(row["value"]) for row in result["metadata"]}
        for row in result["receipts"]:
            row["payload"] = strict_loads(row["payload"])
        for row in result["history"]:
            row["detail"] = strict_loads(row["detail"])
        result["history"].sort(key=lambda row: row["sequence"])
        return result
    finally:
        connection.close()


def _source_rows(contract: dict) -> list[dict]:
    """Reference state of the recovered primary, independent of service replay."""
    state = {}
    for event in contract["source_events"][:contract["cutoff_sequence"]]:
        oid = event["order_id"]
        if event["type"] == "ACCEPT":
            state[oid] = {key: event[key] for key in ORDER_FIELDS}
            state[oid].update(fulfilled=0, state="ACTIVE", source_sequence=event["sequence"])
        else:
            row = state[oid]
            if event["type"] == "CANCEL":
                row["state"] = "CANCELLED"
            elif event["type"] == "FULFILL":
                row["fulfilled"] += event["quantity"]
                if row["fulfilled"] == row["quantity"]:
                    row["state"] = "FULFILLED"
            elif event["type"] == "AMEND":
                for key in ORDER_FIELDS - {"order_id"}:
                    if key in event:
                        row[key] = event[key]
                if row["fulfilled"] == row["quantity"]:
                    row["state"] = "FULFILLED"
            row["source_sequence"] = event["sequence"]
    return [state[k] for k in sorted(state)]


def _reference_obligations(contract: dict) -> dict[str, dict]:
    """Derive acceptance from this verifier's replay, not service admission.

    The controller uses its own obligation helper to initialize the service.
    Sharing that semantic decision here would let a defect in producer
    admission redefine the reference promise in both paths at once.
    """
    result = {}
    for row in _source_rows(contract):
        remaining = row["quantity"] - row["fulfilled"]
        if row["state"] == "ACTIVE" and remaining > 0:
            result[row["order_id"]] = {key: row[key] for key in ORDER_FIELDS} | {"quantity": remaining}
    return result


def _reservation(row: Any, c: dict, expected: dict[str, dict], f: _Findings) -> dict:
    object_fields(row, RESERVATION_FIELDS, path="reservation")
    for name in ("key", "run_id", "order_id", "recipient", "product"):
        identifier(row[name], "reservation." + name)
    for name in ("contract_sha256", "spec_sha256", "request_sha256"):
        sha256(row[name], "reservation." + name)
    for name in ("quantity", "window_start", "window_end", "expires_tick", "created_tick", "updated_tick"):
        integer(row[name], "reservation." + name, 1 if name == "quantity" else 0, MAX_UNITS if name == "quantity" else MAX_TICKS)
    oid = row["order_id"]
    if row["route"] not in ("primary", "backup") or row["status"] not in ACTIVE | {"RELEASED", "EXPIRED"}:
        raise HarnessError("INVALID_TYPE", "reservation.state")
    if row["run_id"] != c["run_id"] or row["contract_sha256"] != digest(c):
        f.add("RESERVATION_BINDING", "run", oid)
    order = expected.get(oid)
    if order is None or any(row[key] != order[key] for key in ORDER_FIELDS - {"deadline_tick"}):
        f.add("RESERVATION_BINDING", "obligation", oid)
    if not c["window"]["start"] <= row["window_start"] < row["window_end"] <= c["window"]["end"]:
        f.add("RESERVATION_BINDING", "window", oid)
    if not row["created_tick"] < row["expires_tick"] <= row["window_end"] or row["updated_tick"] < row["created_tick"]:
        f.add("ILLEGAL_TRANSITION", "clock", oid)
    request = {key: row[key] for key in RESERVATION_FIELDS - {"status", "request_sha256", "created_tick", "updated_tick"}}
    if digest(request) != row["request_sha256"]:
        f.add("RESERVATION_BINDING", "idempotency_request", oid)
    if row["route"] not in c["allowed_routes"]:
        f.add("UNAUTHORIZED_ROUTE", row["route"], oid)
    if not c["permissions"]["activation"]:
        f.add("UNAUTHORIZED_ACTIVATION", "", oid)
    if row["route"] == "backup" and not c["permissions"]["sharing"]:
        f.add("UNAUTHORIZED_SHARING", "", oid)
    if c["dependencies"][row["route"]] in c["blocked_dependencies"]:
        f.add("FAILED_DEPENDENCY", row["route"], oid)
    return row


def _peak(rows: list[dict], route: str, at_tick: int) -> int:
    deltas = {}
    for row in rows:
        if row["route"] != route or row["status"] not in ACTIVE or row["window_end"] <= at_tick:
            continue
        start, end = max(row["window_start"], at_tick), row["window_end"]
        deltas[start] = deltas.get(start, 0) + row["quantity"]
        deltas[end] = deltas.get(end, 0) - row["quantity"]
    total = maximum = 0
    for tick in sorted(deltas):
        total += deltas[tick]
        maximum = max(maximum, total)
    return maximum


def _revoked(controller: dict | None, at_ns: int, route: str) -> str | None:
    if not controller:
        return None
    for event in controller.get("events", []):
        if type(event) is not dict or event.get("event") != "PERMISSION_REVOKED":
            continue
        detail, when = event.get("detail"), event.get("monotonic_ns")
        if type(detail) is dict and type(when) is int and when <= at_ns:
            if detail.get("permission") == "activation":
                return "UNAUTHORIZED_ACTIVATION"
            if detail.get("permission") == "sharing" and route == "backup":
                return "UNAUTHORIZED_SHARING"
    return None


def _completion_observation(controller: dict | None, artifact: dict) -> int | None:
    """Conservative clock bound observed after the service's durable export.

    A transition timestamp inside a receipt is recorded before commit/export.
    A successful fulfill or reconcile response follows file and directory
    fsync in this local service protocol. Bind its *exact* receipt and byte
    hash, then use the trusted controller's observation time as an upper bound.
    These response labels are timing evidence only: actual files, receipts and
    allocation history are still checked independently for acceptance.
    """
    if not controller:
        return None
    observed = []
    expected_hash = hashlib.sha256(canonical(artifact) + b"\n").hexdigest()
    for event in controller["events"]:
        if type(event) is not dict or type(event.get("monotonic_ns")) is not int:
            continue
        detail = event.get("detail")
        if type(detail) is not dict:
            continue
        if event.get("event") == "AMBIGUOUS_RETRY_RESULT":
            response, operation = detail, "fulfill"
        elif event.get("event") == "BROKER_RESULT" and detail.get("op") in ("fulfill", "reconcile"):
            response, operation = detail.get("response"), detail["op"]
        else:
            continue
        if type(response) is not dict or response.get("ok") is not True or type(response.get("result")) is not dict:
            continue
        result = response["result"]
        outputs = result.get("outputs", []) if operation == "reconcile" else [result]
        if type(outputs) is not list:
            continue
        if any(type(output) is dict and output.get("receipt") == artifact
               and output.get("artifact_sha256") == expected_hash
               and output.get("status") == "FULFILLED" for output in outputs):
            observed.append(event["monotonic_ns"])
    return min(observed) if observed else None


def _ledger(database: dict, c: dict, expected: dict[str, dict], f: _Findings, controller: dict | None = None) -> dict:
    metadata = database["metadata"]
    if metadata.get("schema") != "continuity-harness/service/v1" or metadata.get("run_id") != c["run_id"] or metadata.get("contract_sha256") != digest(c):
        f.add("DATABASE_BINDING")
    if metadata.get("window_start") != c["window"]["start"] or metadata.get("window_end") != c["window"]["end"] or metadata.get("source_sha256") != c["source_sha256"]:
        f.add("DATABASE_BINDING", "source_or_window")
    authorized = sorted(database["authorized_orders"], key=lambda row: row.get("order_id", ""))
    if authorized != sorted(expected.values(), key=lambda row: row["order_id"]):
        f.add("AUTHORIZED_ORDERS_CHANGED")
    final = {}
    for raw in database["reservations"]:
        row = _reservation(raw, c, expected, f)
        if row["key"] in final:
            f.add("LEDGER_HISTORY_INVALID", "duplicate_key")
        final[row["key"]] = row
    current = {}
    capacities = dict(c["capacities"])
    availability = {"primary": True, "backup": True}
    max_load = {"primary": 0, "backup": 0}
    previous_tick = 0
    initialized = False
    restored = False
    for index, h in enumerate(database["history"], 1):
        object_fields(h, {"sequence", "operation", "key", "order_id", "route", "tick", "monotonic_ns", "detail"}, path="history")
        if integer(h["sequence"], "history.sequence", 1) != index:
            f.add("LEDGER_HISTORY_INVALID", "sequence")
        tick = integer(h["tick"], "history.tick", 0, MAX_TICKS)
        integer(h["monotonic_ns"], "history.monotonic_ns", 0, MAX_NS)
        if tick < previous_tick:
            f.add("LEDGER_HISTORY_INVALID", "clock")
        previous_tick = max(previous_tick, tick)
        detail = h["detail"]
        if type(detail) is not dict:
            raise HarnessError("INVALID_TYPE", "history.detail")
        op = h["operation"]
        if op == "INIT":
            if initialized or index != 1 or detail.get("capacities") != c["capacities"] or detail.get("window_start") != c["window"]["start"] or detail.get("window_end") != c["window"]["end"] or detail.get("allowed_orders_sha256") != digest(sorted(expected.values(), key=lambda row: row["order_id"])):
                f.add("LEDGER_HISTORY_INVALID", "initialization")
            initialized = True
        elif not initialized:
            f.add("LEDGER_HISTORY_INVALID", "no_initialization")
        elif op == "CAPACITY_CHANGED":
            route = h["route"]
            if route not in capacities:
                raise HarnessError("INVALID_TYPE", "history.route")
            capacity = integer(detail.get("capacity"), "history.capacity", 0, MAX_UNITS)
            if detail.get("previous_capacity") != capacities[route]:
                f.add("LEDGER_HISTORY_INVALID", "capacity_history")
            if capacity > c["capacities"][route]:
                f.add("CAPACITY_AUTHORITY_CHANGED", route)
            capacities[route] = capacity
        elif op == "ROUTE_DISABLED":
            if h["route"] not in availability or detail.get("available") is not False:
                raise HarnessError("INVALID_TYPE", "history.withdrawal")
            availability[h["route"]] = False
        elif op == "RESTORED":
            valid_restore = detail.get("source_sha256") == c["source_sha256"] and detail.get("cutoff") == c["cutoff_sequence"]
            if not valid_restore:
                f.add("PRIMARY_NOT_RECOVERED", "journal")
            restored = valid_restore
        elif op in {"RESERVED", "COMMITTED", "FULFILLED", "RELEASED", "EXPIRED"}:
            row = _reservation(detail.get("reservation"), c, expected, f)
            key = row["key"]
            old = current.get(key)
            if row["status"] != op or h["key"] != key or h["order_id"] != row["order_id"] or h["route"] != row["route"] or row["updated_tick"] != tick:
                f.add("LEDGER_HISTORY_INVALID", "transition_binding", row["order_id"])
            if old is None:
                if op != "RESERVED" or row["created_tick"] != tick or row["expires_tick"] <= tick:
                    f.add("ILLEGAL_TRANSITION", "initial", row["order_id"])
            else:
                legal = {"RESERVED": {"COMMITTED", "RELEASED", "EXPIRED"}, "COMMITTED": {"FULFILLED", "RELEASED"}, "FULFILLED": set(), "RELEASED": set(), "EXPIRED": set()}
                if op not in legal[old["status"]] or any(row[k] != old[k] for k in RESERVATION_FIELDS - {"status", "updated_tick"}):
                    f.add("ILLEGAL_TRANSITION", old["status"] + ":" + op, row["order_id"])
                if old["status"] == "RESERVED" and op != "EXPIRED" and tick >= old["expires_tick"]:
                    f.add("ILLEGAL_TRANSITION", "expired_lease", row["order_id"])
            if op == "EXPIRED" and tick < row["expires_tick"]:
                f.add("ILLEGAL_TRANSITION", "early_expiry", row["order_id"])
            if op in ACTIVE and not availability[row["route"]]:
                f.add("WITHDRAWN_ROUTE_USED", row["route"], row["order_id"])
            if op in ACTIVE and row["route"] == "primary" and not restored:
                f.add("PRIMARY_NOT_RECOVERED", "allocation_before_recovery", row["order_id"])
            revoked = _revoked(controller, h["monotonic_ns"], row["route"])
            if op in ACTIVE and revoked:
                f.add(revoked, "revoked", row["order_id"])
            current[key] = row
        else:
            f.add("LEDGER_HISTORY_INVALID", str(op))
        live_ids = [row["order_id"] for row in current.values() if row["status"] in ACTIVE]
        if len(live_ids) != len(set(live_ids)):
            f.add("DUPLICATE_FULFILLMENT", "multiple_live_allocations")
        for route in capacities:
            load = _peak(list(current.values()), route, tick)
            max_load[route] = max(max_load[route], load)
            if load > capacities[route]:
                f.add("CAPACITY_EXCEEDED", route + ":" + str(tick))
                for row in current.values():
                    if row["route"] == route and row["status"] in ACTIVE and row["window_end"] > tick:
                        f.add("CAPACITY_EXCEEDED", "joint_allocation", row["order_id"])
    if not initialized or current != final:
        f.add("LEDGER_HISTORY_INVALID", "final_state")
    expected_routes = [{"route": route, "capacity": capacities[route], "available": int(availability[route])} for route in sorted(capacities)]
    if sorted(database["routes"], key=lambda row: row.get("route", "")) != expected_routes:
        f.add("LEDGER_HISTORY_INVALID", "routes_final_state")
    if metadata.get("last_tick", -1) < previous_tick:
        f.add("LEDGER_HISTORY_INVALID", "last_tick")
    primary_ok = (restored and sorted(database["orders"], key=lambda row: row.get("order_id", "")) == _source_rows(c)
                  and metadata.get("recovery_cutoff") == c["cutoff_sequence"]
                  and metadata.get("recovery_source_sha256") == c["source_sha256"])
    return {"reservations": final, "max_simultaneous_allocated": max_load,
            "history_transitions": len(database["history"]), "primary_recovery_verified": primary_ok}


def _refusal_for(oid: str, controller: dict | None) -> str | None:
    if not controller:
        return None
    # This only explains a missing output. It is never acceptance evidence.
    stack = [controller.get("events", []), controller.get("errors", [])]
    while stack:
        value = stack.pop()
        if isinstance(value, list):
            stack.extend(value)
        elif isinstance(value, dict):
            if value.get("order_id") == oid and type(value.get("code")) is str:
                return value["code"]
            stack.extend(v for v in value.values() if isinstance(v, (list, dict)))
    return None


def verify_run(run_dir: str | Path, authority_dir: str | Path,
               *, expected_reference_sha256: str | None = None) -> dict:
    """Verify current evidence without editing it or trusting saved assessments.

    ``expected_reference_sha256`` must come from outside candidate-controlled
    evidence. Without it, an internally consistent bundle remains unestablished.
    A successful verification is scoped to authored local software execution.
    """
    f = _Findings()
    c = reference = controller = database = ledger = None
    artifacts: list[dict] = []
    evidence_hashes = {}
    expected = {}
    authority_status = "NOT_ESTABLISHED"
    verification_complete = True
    try:
        root = _safe_root(Path(run_dir))
        authority = _safe_root(Path(authority_dir))
        try:
            reference = validate_reference(strict_load(authority / "reference.json"))
            c = validate_contract(strict_load(authority / "contract.json"))
        except HarnessError as exc:
            f.add("AUTHORITY_MISSING" if exc.code == "MISSING_FILE" else "AUTHORITY_INVALID", exc.code, unknown=exc.code == "MISSING_FILE")
        if c is not None and reference is not None:
            expected = _reference_obligations(c)
            if expected_reference_sha256 is None:
                f.add("REFERENCE_PIN_MISSING", unknown=True)
            else:
                try:
                    sha256(expected_reference_sha256, "expected_reference_sha256")
                    if digest(reference) != expected_reference_sha256:
                        f.add("REFERENCE_PIN_MISMATCH")
                    else:
                        authority_status = "DEMONSTRATED"
                except HarnessError:
                    f.add("REFERENCE_PIN_MISMATCH", "invalid_pin")
            if reference["run_id"] != c["run_id"] or reference["contract_sha256"] != digest(c) or reference["source_sha256"] != c["source_sha256"] or reference["cutoff_sequence"] != c["cutoff_sequence"] or reference["source_complete"] != c["source_complete"]:
                f.add("CONTRACT_BINDING")
            if not c["source_complete"]:
                f.add("SOURCE_INCOMPLETE", unknown=True)
                authority_status = "NOT_ESTABLISHED"
            try:
                journal = strict_load(authority / "journal.json")
                if journal != c["source_events"] or digest(journal) != c["source_sha256"]:
                    f.add("SOURCE_JOURNAL_MISMATCH")
                    authority_status = "FAILED"
            except HarnessError as exc:
                f.add("SOURCE_JOURNAL_MISSING" if exc.code == "MISSING_FILE" else "SOURCE_JOURNAL_MISMATCH", exc.code, unknown=exc.code == "MISSING_FILE")
                authority_status = "NOT_ESTABLISHED" if exc.code == "MISSING_FILE" else "FAILED"
            if not expected:
                f.add("NO_OBLIGATIONS_IN_SCOPE", unknown=True)
            if any(item["code"] in {"REFERENCE_PIN_MISMATCH", "CONTRACT_BINDING"} for item in f.failures):
                authority_status = "FAILED"
        try:
            controller = _controller(strict_load(root / "controller.json"))
        except HarnessError as exc:
            f.add("CONTROLLER_MISSING" if exc.code == "MISSING_FILE" else "CONTROLLER_INVALID", exc.code, unknown=exc.code == "MISSING_FILE")
        if controller:
            if c and (controller["run_id"] != c["run_id"] or controller["contract_sha256"] != digest(c) or controller["scenario"] != c["scenario"] or controller["seed"] != c["seed"]):
                f.add("CONTROLLER_BINDING")
            if controller["state"] != "COMPLETE":
                f.add("NOT_RUN" if controller["state"] == "NOT_RUN" else "EXECUTION_INCOMPLETE", unknown=True)
            if controller["state"] != "NOT_RUN" and (controller["isolation"]["mechanism"] != "SECCOMP_BPF" or not controller["isolation"]["applied"] or not {"authority_open_denied", "workspace_open_denied", "network_denied", "spawn_denied", "process_inspection_denied"} <= set(controller["isolation"]["probe"]) or not all(controller["isolation"]["probe"].values())):
                f.add("ISOLATION_NOT_ESTABLISHED", unknown=True)
            if c:
                if controller["fault_schedule"] != c["fault_schedule"]:
                    f.add("FAULT_SCHEDULE_CHANGED")
                if controller["state"] == "COMPLETE" and any(event not in controller["faults_observed"] for event in c["fault_schedule"]):
                    f.add("FAULT_NOT_OBSERVED", unknown=True)
                if controller["recovery_ms"] is None and controller["state"] != "NOT_RUN" and c["scenario"] == "recovery":
                    f.add("RECOVERY_TIME_MISSING", unknown=True)
                elif controller["recovery_ms"] is not None and controller["recovery_ms"] > c["recovery_objective_ms"]:
                    f.add("RECOVERY_OBJECTIVE_EXCEEDED")
                # Rounded producer milliseconds are presentation metadata, not
                # sufficient evidence at the exact recovery-objective boundary.
                # This trusted observation follows a successful restore response;
                # durable recovered rows/history are checked separately below.
                recovery_events = [event for event in controller["events"]
                                   if type(event) is dict and event.get("event") == "PRIMARY_RECOVERED"]
                if controller["state"] != "NOT_RUN" and (c["scenario"] == "recovery" or controller["recovery_ms"] is not None or recovery_events):
                    observed_recovery = []
                    for event in recovery_events:
                        when = event.get("monotonic_ns")
                        if type(when) is not int:
                            f.add("RECOVERY_TIME_MISSING", "post_recovery_observation", unknown=True)
                        elif not controller["started_monotonic_ns"] <= when <= controller["finished_monotonic_ns"]:
                            f.add("CLOCK_OUTSIDE_RUN", "primary_recovery")
                        else:
                            observed_recovery.append(when)
                    if not observed_recovery:
                        f.add("RECOVERY_TIME_MISSING", "post_recovery_observation", unknown=True)
                    elif min(observed_recovery) - controller["started_monotonic_ns"] > c["recovery_objective_ms"] * 1_000_000:
                        f.add("RECOVERY_OBJECTIVE_EXCEEDED", "post_recovery_upper_bound_ns=" + str(min(observed_recovery) - controller["started_monotonic_ns"]))
        try:
            seal = object_fields(strict_load(authority / "execution.json"), {"schema", "run_id", "contract_sha256", "controller_sha256", "evidence_manifest"}, path="execution_seal")
            if seal["schema"] != "continuity-harness/execution-seal/v1":
                raise HarnessError("UNSUPPORTED_VERSION", "execution_seal")
            identifier(seal["run_id"], "execution_seal.run_id")
            sha256(seal["contract_sha256"], "execution_seal.contract_sha256")
            sha256(seal["controller_sha256"], "execution_seal.controller_sha256")
            manifest = seal["evidence_manifest"]
            if type(manifest) is not dict or len(manifest) > MAX_ORDERS * 4 + 32:
                raise HarnessError("INVALID_TYPE", "execution_seal.evidence_manifest")
            if c and (seal["run_id"] != c["run_id"] or seal["contract_sha256"] != digest(c)):
                f.add("EXECUTION_SEAL_BINDING", "contract")
            if controller and seal["controller_sha256"] != digest(controller):
                f.add("EXECUTION_SEAL_BINDING", "controller")
            for relative, checksum in manifest.items():
                try:
                    sha256(checksum, "execution_seal.evidence_manifest")
                    path = _safe_child(root, relative)
                    actual = _file_hash(path)
                    evidence_hashes[relative] = actual
                    if actual != checksum:
                        f.add("EVIDENCE_CHANGED", relative)
                except HarnessError as exc:
                    f.add("UNSAFE_EVIDENCE_PATH" if exc.code == "UNSAFE_PATH" else "EVIDENCE_MISSING", str(relative), unknown=exc.code == "MISSING_FILE")
            evidence_dir = root / "evidence"
            _safe_root(evidence_dir)
            files = sorted(evidence_dir.rglob("*")) if evidence_dir.is_dir() else []
            for path in files:
                if path.is_symlink():
                    f.add("UNSAFE_EVIDENCE_PATH", path.name)
                elif path.is_file() and path.relative_to(root).as_posix() not in manifest:
                    f.add("UNSEALED_EVIDENCE", path.relative_to(root).as_posix())
            if "evidence/service.sqlite" not in manifest and not (controller and controller["state"] == "NOT_RUN"):
                f.add("EVIDENCE_MISSING", "evidence/service.sqlite", unknown=True)
        except HarnessError as exc:
            f.add("EXECUTION_SEAL_MISSING" if exc.code == "MISSING_FILE" else "EXECUTION_SEAL_INVALID", exc.code, unknown=exc.code == "MISSING_FILE")
        artifact_dir = root / "evidence" / "artifacts"
        _safe_root(artifact_dir)
        if artifact_dir.exists():
            paths = sorted(artifact_dir.glob("*.json"))
            if len(paths) > MAX_ORDERS * 2:
                raise HarnessError("INVALID_RANGE", "artifacts")
            for path in paths:
                try:
                    a = validate_artifact(strict_load(path))
                    if path.name != a["order_id"] + ".json":
                        f.add("ARTIFACT_BINDING", "filename", a["order_id"])
                    artifacts.append(a)
                except HarnessError as exc:
                    f.add("ARTIFACT_INVALID", path.name + ":" + exc.code)
        db_path = root / "evidence" / "service.sqlite"
        if db_path.exists():
            try:
                database = _read_database(db_path)
                if c:
                    ledger = _ledger(database, c, expected, f, controller)
            except HarnessError as exc:
                f.add("DATABASE_NOT_CHECKPOINTED" if exc.code == "DATABASE_NOT_CHECKPOINTED" else "DATABASE_INVALID", exc.code, unknown=exc.code == "DATABASE_NOT_CHECKPOINTED")
            except (sqlite3.Error, KeyError, TypeError, ValueError) as exc:
                f.add("DATABASE_INVALID", type(exc).__name__)
        elif not (controller and controller["state"] == "NOT_RUN"):
            f.add("DATABASE_MISSING", unknown=True)
        # A second fresh hash detects ordinary concurrent mutation during this
        # read. It is not protection against a malicious trusted host.
        for relative, prior in evidence_hashes.items():
            try:
                if _file_hash(_safe_child(root, relative)) != prior:
                    f.add("EVIDENCE_CHANGED_DURING_VERIFICATION", relative)
            except HarnessError:
                f.add("EVIDENCE_CHANGED_DURING_VERIFICATION", relative)
    except Exception as exc:
        verification_complete = False
        f.add("VERIFICATION_ERROR", getattr(exc, "code", type(exc).__name__), unknown=True)

    per_obligation = []
    observed_units = sum(a["quantity"] for a in artifacts)
    accepted = {}
    durable_observations = {}
    receipts = {}
    if database:
        for row in database["receipts"]:
            try:
                object_fields(row, {"key", "order_id", "payload", "sha256", "completed_tick", "completed_monotonic_ns"}, path="receipt")
                payload = validate_artifact(row["payload"])
                if row["sha256"] != hashlib.sha256(canonical(payload) + b"\n").hexdigest() or row["key"] != payload["key"] or row["order_id"] != payload["order_id"] or row["completed_tick"] != payload["completed_tick"] or row["completed_monotonic_ns"] != payload["completed_monotonic_ns"]:
                    f.add("RECEIPT_MISMATCH", "payload", payload["order_id"])
                if payload["order_id"] in receipts:
                    f.add("DUPLICATE_FULFILLMENT", "receipts", payload["order_id"])
                receipts[payload["order_id"]] = payload
            except (HarnessError, KeyError, TypeError) as exc:
                f.add("RECEIPT_MISMATCH", getattr(exc, "code", type(exc).__name__))
    counts = {}
    for a in artifacts:
        oid = a["order_id"]
        counts[oid] = counts.get(oid, 0) + 1
        if counts[oid] > 1:
            f.add("DUPLICATE_FULFILLMENT", "artifacts", oid)
        if c:
            if a["run_id"] != c["run_id"] or a["contract_sha256"] != digest(c):
                f.add("ARTIFACT_BINDING", "run", oid)
            order = expected.get(oid)
            if order is None:
                f.add("UNKNOWN_OBLIGATION", "", oid)
            else:
                for key, code in (("recipient", "WRONG_RECIPIENT"), ("product", "WRONG_PRODUCT"), ("spec_sha256", "WRONG_SPECIFICATION"), ("quantity", "WRONG_QUANTITY")):
                    if a[key] != order[key]:
                        f.add(code, "", oid)
                if a["completed_tick"] > min(c["deadline_tick"], order["deadline_tick"], c["window"]["end"]) or a["completed_tick"] < c["window"]["start"]:
                    f.add("LATE_COMPLETION", "tick", oid)
            if a["route"] not in c["allowed_routes"]:
                f.add("UNAUTHORIZED_ROUTE", a["route"], oid)
            if not c["permissions"]["activation"]:
                f.add("UNAUTHORIZED_ACTIVATION", "", oid)
            if a["route"] == "backup" and not c["permissions"]["sharing"]:
                f.add("UNAUTHORIZED_SHARING", "", oid)
            if c["dependencies"][a["route"]] in c["blocked_dependencies"]:
                f.add("FAILED_DEPENDENCY", a["route"], oid)
        if controller:
            if not controller["started_monotonic_ns"] <= a["completed_monotonic_ns"] <= controller["finished_monotonic_ns"]:
                f.add("CLOCK_OUTSIDE_RUN", "completion", oid)
            if c and a["completed_monotonic_ns"] - controller["started_monotonic_ns"] > c["wall_deadline_ms"] * 1_000_000:
                f.add("WALL_DEADLINE_EXCEEDED", "transition", oid)
            observation = _completion_observation(controller, a)
            if observation is None:
                f.add("DURABLE_OBSERVATION_MISSING", "", oid, unknown=True)
            else:
                durable_observations[oid] = observation
                if not a["completed_monotonic_ns"] <= observation <= controller["finished_monotonic_ns"]:
                    f.add("CLOCK_OUTSIDE_RUN", "durable_observation", oid)
                if c and observation - controller["started_monotonic_ns"] > c["wall_deadline_ms"] * 1_000_000:
                    f.add("WALL_DEADLINE_EXCEEDED", "post_export_upper_bound", oid)
            revoked = _revoked(controller, a["completed_monotonic_ns"], a["route"])
            if revoked:
                f.add(revoked, "revoked", oid)
        if database is not None and receipts.get(oid) != a:
            f.add("RECEIPT_MISMATCH", "artifact", oid)
        reservation = ledger["reservations"].get(a["key"]) if ledger else None
        if ledger is not None and (not reservation or reservation["status"] != "FULFILLED" or reservation["updated_tick"] != a["completed_tick"] or any(reservation[k] != a[k] for k in ("run_id", "contract_sha256", "order_id", "recipient", "product", "spec_sha256", "quantity", "route", "key"))):
            f.add("RESERVATION_MISSING", "", oid)
        if reservation and not reservation["window_start"] <= a["completed_tick"] <= reservation["window_end"]:
            f.add("LATE_COMPLETION", "reserved_window", oid)
        if a["route"] == "primary" and ledger is not None and not ledger["primary_recovery_verified"]:
            f.add("PRIMARY_NOT_RECOVERED", "durable_orders", oid)
        accepted[oid] = a
    for oid in receipts:
        if oid not in counts:
            f.add("ARTIFACT_MISSING", "", oid, unknown=True)

    trusted_evidence = authority_status == "DEMONSTRATED" and controller is not None and ledger is not None and verification_complete
    global_integrity_failures = {"REFERENCE_PIN_MISMATCH", "CONTRACT_BINDING", "AUTHORITY_INVALID", "SOURCE_JOURNAL_MISMATCH", "CONTROLLER_INVALID", "CONTROLLER_BINDING", "EXECUTION_SEAL_BINDING", "EXECUTION_SEAL_INVALID", "EVIDENCE_CHANGED", "EVIDENCE_CHANGED_DURING_VERIFICATION", "UNSEALED_EVIDENCE", "UNSAFE_EVIDENCE_PATH", "DATABASE_BINDING", "DATABASE_INVALID", "AUTHORIZED_ORDERS_CHANGED", "LEDGER_HISTORY_INVALID"}
    if any(row["code"] in global_integrity_failures for row in f.failures) or any(row["code"] in {"EXECUTION_SEAL_MISSING", "EVIDENCE_MISSING", "DATABASE_MISSING", "DATABASE_NOT_CHECKPOINTED", "CONTROLLER_MISSING", "ISOLATION_NOT_ESTABLISHED", "VERIFICATION_ERROR"} for row in f.unresolved):
        trusted_evidence = False
    for oid, order in sorted(expected.items()):
        a = accepted.get(oid)
        known_failures = [row["code"] for row in f.failures if row.get("order_id") == oid]
        own = known_failures + [row["code"] for row in f.unresolved if row.get("order_id") == oid]
        quantity = a["quantity"] if a else 0
        accepted_quantity = order["quantity"] if a and not own and counts.get(oid) == 1 and trusted_evidence else 0
        if accepted_quantity:
            outcome = "COMPLETED"
        elif a and any(code in own for code in ("LATE_COMPLETION", "WALL_DEADLINE_EXCEEDED")):
            outcome = "LATE"
        elif a and known_failures:
            outcome = "INCORRECT"
        elif a or oid in receipts or not trusted_evidence or not controller or controller["state"] != "COMPLETE":
            outcome = "UNRESOLVED"
        else:
            refusal = _refusal_for(oid, controller)
            outcome = "REFUSED" if refusal else "UNFULFILLED"
            if refusal:
                own.append(refusal)
        if not a:
            own.append("NO_DURABLE_OUTPUT")
        per_obligation.append({"order_id": oid, "recipient": order["recipient"], "product": order["product"],
                               "spec_sha256": order["spec_sha256"], "expected_quantity": order["quantity"],
                               "observed_quantity": quantity, "accepted_quantity": accepted_quantity,
                               "outcome": outcome, "reason_codes": sorted(set(own)),
                               "route": a["route"] if a else None,
                               "deadline_tick": min(order["deadline_tick"], c["deadline_tick"]),
                               "completed_tick": a["completed_tick"] if a else None,
                               "transition_ns": a["completed_monotonic_ns"] - controller["started_monotonic_ns"] if a and controller else None,
                               "durable_observed_monotonic_ns": durable_observations.get(oid),
                               "completion_ns": durable_observations[oid] - controller["started_monotonic_ns"] if oid in durable_observations and controller else None})
    all_completed = bool(per_obligation) and all(row["outcome"] == "COMPLETED" for row in per_obligation)
    if controller and controller["state"] == "COMPLETE" and trusted_evidence and any(row["outcome"] in {"REFUSED", "UNFULFILLED", "INCORRECT", "LATE"} for row in per_obligation):
        f.add("ALL_OBLIGATIONS_NOT_COMPLETED")
    if f.failures:
        claim = "FAILED"
    elif f.unresolved or not all_completed:
        claim = "NOT_ESTABLISHED"
    else:
        claim = "DEMONSTRATED"
    safety_failures = [row for row in f.failures if row["code"] in SAFETY_CODES]
    safety_integrity_failures = global_integrity_failures | {"ARTIFACT_INVALID", "RECEIPT_MISMATCH", "RESERVATION_MISSING", "CLOCK_OUTSIDE_RUN"}
    safety = "FAILED" if safety_failures else "DEMONSTRATED" if trusted_evidence and controller and controller["state"] == "COMPLETE" and not any(row["code"] in safety_integrity_failures for row in f.failures) else "NOT_ESTABLISHED"
    test_assertion = "NOT_EVALUATED"
    if controller and controller["state"] == "NOT_RUN":
        test_assertion = "NOT_RUN"
    elif c and controller and c["comparison"]["suite_id"] == "CONTINUITY-HARNESS-001":
        # These are the three controls registered in spec.json before any
        # comparative execution. Their expected outcomes do not become the
        # acceptance oracle: obligation acceptance above is already complete.
        # No quantity, order ID or held-out fixture answer is hard-coded here.
        if c["scenario"] in {"recovery", "alternate"}:
            right_route = all(row["route"] == ("primary" if c["scenario"] == "recovery" else "backup") for row in per_obligation)
            test_assertion = "PASSED" if claim == "DEMONSTRATED" and safety == "DEMONSTRATED" and right_route and controller["target_verdict"] == "COMPLETED" else "FAILED"
        elif c["scenario"] == "constrained" and len(expected) == 2:
            priority = sorted(expected.values(), key=lambda row: (row["deadline_tick"], row["order_id"]))
            by_id = {row["order_id"]: row for row in per_obligation}
            first, second = by_id[priority[0]["order_id"]], by_id[priority[1]["order_id"]]
            expected_shape = (priority[0]["quantity"] <= c["capacities"]["backup"] < sum(row["quantity"] for row in priority))
            observed_shape = (first["outcome"] == "COMPLETED" and first["route"] == "backup" and second["outcome"] == "REFUSED" and "CAPACITY_EXCEEDED" in second["reason_codes"])
            no_other_failure = all(row["code"] == "ALL_OBLIGATIONS_NOT_COMPLETED" for row in f.failures)
            test_assertion = "PASSED" if (expected_shape and observed_shape and safety == "DEMONSTRATED" and claim == "FAILED" and no_other_failure and not f.unresolved and controller["state"] == "COMPLETE" and controller["target_verdict"] == "PARTIAL") else "FAILED"
    return {
        "schema": "continuity-harness/verification/v1", "verifier_version": VERSION,
        "run_id": c["run_id"] if c else (controller["run_id"] if controller else None),
        "contract_sha256": digest(c) if c else None,
        "reference_sha256": digest(reference) if reference else None,
        "authority_status": authority_status,
        "verification_status": "COMPLETE" if verification_complete else "INCOMPLETE",
        "assessment": {"test_assertion": test_assertion, "target_verdict": controller["target_verdict"] if controller else "UNKNOWN",
                       "evidence_stage": "NOT_RUN" if controller and controller["state"] == "NOT_RUN" else "LOCAL_SOFTWARE_EXECUTION" if controller or database is not None or artifacts else "VERIFICATION_ATTEMPT",
                       "claim_status": claim},
        "safety_status": safety, "all_obligations_completed": all_completed,
        "per_obligation": per_obligation,
        "totals": {"expected_obligations": len(expected) if c is not None else None, "accepted_obligations": sum(row["outcome"] == "COMPLETED" for row in per_obligation),
                   "expected_units": sum(row["quantity"] for row in expected.values()) if c is not None else None,
                   "observed_units": observed_units, "accepted_units": sum(row["accepted_quantity"] for row in per_obligation),
                   "missing_units": sum(row["expected_quantity"] - row["accepted_quantity"] for row in per_obligation) if c is not None else None,
                   "late_obligations": sum(row["outcome"] == "LATE" for row in per_obligation),
                   "incorrect_obligations": sum(row["outcome"] == "INCORRECT" for row in per_obligation),
                   "duplicate_obligations": sum(value > 1 for value in counts.values()),
                   "unsupported_obligations": sum(oid not in expected for oid in counts) if c is not None else None},
        "ledger": {key: ledger[key] for key in ("max_simultaneous_allocated", "history_transitions", "primary_recovery_verified")} if ledger else None,
        "failures": f.failures, "unresolved": f.unresolved,
        "evidence_sha256": evidence_hashes,
        "resources": controller["resources"] if controller else None,
        "recovery_ms": controller["recovery_ms"] if controller else None,
        "trust_scope": "TRUSTED_HOST_CONTROLLER_CLOCK_AND_VERIFIER_AUTHORED_SYNTHETIC_SOURCE",
        "commercial_value": "NOT_ESTABLISHED", "real_customer_authenticity": "NOT_ESTABLISHED",
    }
