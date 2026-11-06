"""Trusted disposable-process controller for the registered digital experiment.

Process framing, seccomp admission and the transactional capacity service reuse
continuity_harness at 396227d8da2f55f674f479de16089c7ce28ef290 unchanged.
Participant consent, production and receiving are separate durable processes.
This controller is trusted host machinery, not a third-party certification body.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import platform
import resource
import sqlite3
import subprocess
import sys
import time

from continuity_harness.rpc import ProcessChannel, ServiceClient
from .schema import (HarnessError, canonical, digest, object_fields, integer,
                     identifier, strict_load, validate_contract, validate_policies,
                     candidate_view, capacity_order, lots)
from .policy_schema import validate_proposal_shape
from continuity_harness.schema import ERROR_MESSAGES as SCHEMA_MESSAGES
from .participants import MESSAGES as PARTICIPANT_MESSAGES
from .producer import MESSAGES as PRODUCER_MESSAGES
from .receiver import MESSAGES as RECEIVER_MESSAGES

ROOT = Path(__file__).resolve().parents[1]
PROBES = {"authority_open_denied", "workspace_open_denied", "network_denied",
          "spawn_denied", "process_inspection_denied"}
MESSAGES = {
    "UNKNOWN_METHOD": ("This candidate method is unsupported.", "Cette méthode candidate n’est pas prise en charge."),
    "UNKNOWN_PROVIDER": ("The contract does not authorize this provider identity.", "Le contrat n’autorise pas cette identité de fournisseur."),
    "UNKNOWN_WINDOW": ("The provider has no authorized capacity window with this identity.", "Le fournisseur n’a aucune fenêtre de capacité autorisée portant cette identité."),
    "EVIDENCE_EXISTS": ("Existing evidence is retained and cannot be overwritten.", "Les preuves existantes sont conservées et ne peuvent être remplacées."),
    "DATABASE_STATE_CHANGED": ("Durable database content changed after its retained snapshot.", "Le contenu durable de la base a changé après son instantané conservé."),
    "DATABASE_FINALIZATION_ERROR": ("The database could not be finalized as verified closed evidence.", "La base n’a pas pu être finalisée comme preuve fermée et vérifiée."),
    "DATABASE_SIDECAR_PRESENT": ("Database sidecar files prevent complete finalization.", "Des fichiers auxiliaires de base de données empêchent une finalisation complète."),
    "FAULT_TARGET_INVALID": ("The recorded fault does not identify a supported target or value.", "La défaillance enregistrée ne désigne pas une cible ou une valeur prise en charge."),
    "FAULT_PRECONDITION": ("The required state for this recorded fault was not established.", "L’état requis pour cette défaillance enregistrée n’a pas été établi."),
    "FAULT_CAPABILITY_UNAVAILABLE": ("This recorded fault cannot be executed by the available controller.", "Le contrôleur disponible ne peut exécuter cette défaillance enregistrée."),
    "FAULT_HOOK_MISSING": ("The required deterministic transition barrier was not observed.", "La barrière déterministe requise pour la transition n’a pas été observée."),
    "OBSERVATION_CUTOFF": ("The frozen observation cutoff has been exceeded; the exercise is incomplete.", "La limite d’observation figée est dépassée ; l’exercice est incomplet."),
    "EXERCISE_TIMEOUT": ("The frozen elapsed-time limit has been exceeded; the exercise is incomplete.", "La limite de durée figée est dépassée ; l’exercice est incomplet."),
    "ALLOCATION_NOT_FOUND": ("The agreement does not authorize this lot.", "L’accord n’autorise pas ce lot."),
    "PERMISSION_MISSING": ("Current permission does not authorize this action.", "L’autorisation actuelle ne permet pas cette action."),
    "DEPENDENCY_UNAVAILABLE": ("A required shared dependency is unavailable.", "Une dépendance partagée requise est indisponible."),
    "INCOMPLETE_SOURCE": ("Required source completeness has not been established.", "L’exhaustivité requise de la source n’a pas été établie."),
    "CAPACITY_NOT_RESERVED": ("Production requires a live authorized capacity reservation.", "La production exige une réservation de capacité autorisée et active."),
    "PRODUCTION_NOT_ESTABLISHED": ("Durable materialization of the product has not been established.", "La matérialisation durable du produit n’a pas été établie."),
    "PRODUCT_MISSING": ("The materialized product file is missing.", "Le fichier du produit matérialisé est absent."),
    "PRODUCT_CHANGED": ("The actual product bytes differ from the durable production record.", "Les octets réels du produit diffèrent de l’enregistrement durable de production."),
    "DELIVERY_CONTENT_CONFLICT": ("The same delivery identifier already refers to different content.", "Le même identifiant de remise désigne déjà un contenu différent."),
    "ACCEPTANCE_NOT_ESTABLISHED": ("Complete timely recipient acceptance has not been established.", "L’acceptation complète du destinataire dans le délai n’a pas été établie."),
    "DUPLICATE_ACCEPTANCE": ("The same required units were counted more than once.", "Les mêmes unités requises ont été comptées plus d’une fois."),
    "ACCRUED_ACCEPTANCE": ("Recipient acceptance has accrued; retain the agreement, escrow and liabilities until an authorized resolution.", "Une acceptation du destinataire est acquise ; conserver l’accord, le séquestre et les responsabilités jusqu’à une résolution autorisée."),
    "REQUEST_BUDGET_EXHAUSTED": ("The frozen request budget is exhausted; the exercise is incomplete.", "Le budget de requêtes figé est épuisé ; l’exercice est incomplet."),
    "ISOLATION_UNAVAILABLE": ("Required candidate isolation and all five denial probes were not established.", "L’isolation requise du candidat et les cinq essais de refus n’ont pas été établis."),
    "TELEMETRY_BUDGET_EXHAUSTED": ("The bounded candidate telemetry budget is exhausted.", "Le budget borné de télémétrie du candidat est épuisé."),
    "CANDIDATE_ERROR": ("The candidate did not complete a valid execution exchange.", "Le candidat n’a pas achevé un échange d’exécution valide."),
    "RESTART_BUDGET_EXHAUSTED": ("The declared restart limit has been exceeded.", "La limite déclarée de redémarrages est dépassée."),
    "DATABASE_CHECKPOINT_INCOMPLETE": ("A complete durable database checkpoint was not established.", "Un point de contrôle complet et durable de la base n’a pas été établi."),
    "WORKER_EXIT_UNEXPECTED": ("An owned worker exited unexpectedly; execution is not qualified.", "Un processus de l’exercice s’est arrêté inopinément ; l’exécution n’est pas qualifiée."),
    "WORKER_CLOSURE_FAILED": ("One or more owned workers could not be closed normally.", "Un ou plusieurs processus de l’exercice n’ont pas pu être fermés normalement."),
    "DEADLINE_EXCEEDED": ("The frozen obligation deadline or capacity window has expired.", "L’échéance figée de l’engagement ou la fenêtre de capacité est dépassée."),
    "ACK_UNKNOWN": ("The acknowledgment was lost; reconcile the durable outcome before retrying effects.", "L’accusé de réception a été perdu ; rapprocher le résultat durable avant de répéter les effets."),
    "PROCESS_TIMEOUT": ("A local process did not respond within its declared limit.", "Un processus local n’a pas répondu dans la limite déclarée."),
    "PROCESS_WRITE_TIMEOUT": ("A local process could not receive the request within its declared limit.", "Un processus local n’a pas pu recevoir la requête dans la limite déclarée."),
    "PROCESS_EXITED": ("A required local process exited before returning its result.", "Un processus local requis s’est arrêté avant de renvoyer son résultat."),
    "RPC_FRAME_INVALID": ("A process message violates the supported structured protocol.", "Un message de processus enfreint le protocole structuré pris en charge."),
    "RPC_ID_MISMATCH": ("The response is not bound to the pending request.", "La réponse n’est pas liée à la requête en attente."),
}


def localized_error(code):
    # Text sharing is permitted; no service's generation or decision function is
    # used as the fresh verifier's oracle. Technical locations remain separate.
    pair = MESSAGES.get(code) or PARTICIPANT_MESSAGES.get(code) or PRODUCER_MESSAGES.get(code) or RECEIVER_MESSAGES.get(code) or SCHEMA_MESSAGES.get(code)
    if pair is None:
        pair = ("The local operation could not be established; consult the stable machine code and retained evidence.",
                "L’opération locale n’a pas pu être établie ; consulter le code machine stable et les preuves conservées.")
    return {"en": pair[0], "fr": pair[1]}


def write_bytes(path, data):
    """Exclusive durable publication; no existing evidence is overwritten."""
    path = Path(path)
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def write_json(path, value):
    write_bytes(path, canonical(value) + b"\n")


def fresh_directory(path):
    path = Path(path).absolute()
    for ancestor in (path, *path.parents):
        if ancestor.is_symlink():
            raise HarnessError("UNSAFE_PATH", str(ancestor))
    path.mkdir(parents=True, exist_ok=False)
    return path


def implementation_identity():
    """Hash the implementation and registered inputs, including reused code."""
    source = {}
    paths = list((ROOT / "continuity_economy").glob("*.py"))
    paths += list((ROOT / "continuity_harness").glob("*.py"))
    paths += list((ROOT / "experiments/economy-v0.2").rglob("*.json"))
    for path in sorted(paths):
        if path.is_file():
            source[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    def git(*args):
        result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
        return result.stdout.strip() if result.returncode == 0 else "UNAVAILABLE"
    return {"version": "0.2.0", "git_commit": git("rev-parse", "HEAD"),
            "dirty": bool(git("status", "--porcelain")), "source_sha256": source,
            "reused_capacity_baseline": "396227d8da2f55f674f479de16089c7ce28ef290",
            "environment": {"python": sys.version, "platform": platform.platform(),
                "sqlite_version": sqlite3.sqlite_version,
                "argv": list(getattr(sys, "orig_argv", [sys.executable, *sys.argv])),
                "working_directory": str(Path.cwd())}}


def logical_digest(connection):
    result = hashlib.sha256()
    for line in connection.iterdump():
        result.update(line.encode("utf-8") + b"\n")
    return result.hexdigest()


def database_digest(path):
    connection = sqlite3.connect(Path(path).as_uri() + "?mode=ro", uri=True)
    try:
        connection.execute("BEGIN")
        result = logical_digest(connection)
        connection.rollback()
        return result
    finally:
        connection.close()


def finalized_database(source, target, retained_digest):
    """Back up the actual committed database, then close/fsync before sealing.

    This includes committed WAL content. A pre-close full logical digest prevents
    silently dropping tables, content BLOBs or transactions during finalization.
    The artifact itself has journal_mode DELETE and no persistent sidecars.
    """
    source, target = Path(source), Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        raise HarnessError("EVIDENCE_EXISTS", str(target))
    temporary = target.with_suffix(".closing")
    if temporary.exists():
        raise HarnessError("EVIDENCE_EXISTS", str(temporary))
    original = sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)
    copied = sqlite3.connect(temporary)
    try:
        original.execute("BEGIN")
        if logical_digest(original) != retained_digest:
            raise HarnessError("DATABASE_STATE_CHANGED", str(source))
        original.backup(copied)
        mode = copied.execute("PRAGMA journal_mode=DELETE").fetchone()[0]
        copied.commit()
        if str(mode).lower() != "delete" or copied.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise HarnessError("DATABASE_FINALIZATION_ERROR", str(source))
        if logical_digest(copied) != retained_digest:
            raise HarnessError("DATABASE_STATE_CHANGED", str(target))
        original.rollback()
    finally:
        copied.close()
        original.close()
    with temporary.open("rb") as stream:
        os.fsync(stream.fileno())
    for suffix in ("-wal", "-shm", "-journal"):
        if Path(str(temporary) + suffix).exists():
            raise HarnessError("DATABASE_SIDECAR_PRESENT", str(temporary))
    os.replace(temporary, target)
    fd = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class LocalClient(ProcessChannel):
    """Same bounded RPC envelope as the qualified capacity ServiceClient."""
    def __init__(self, module, arguments, log, timeout_ms):
        super().__init__([sys.executable, "-m", module, *map(str, arguments)], ROOT, log, timeout_ms)
        self.counter = 0

    start_request = ServiceClient.start_request
    call = ServiceClient.call


class RestartCandidate(Exception):
    pass


class KilledAtHook(Exception):
    pass


class Controller:
    def __init__(self, contract, policies, method, run_dir, authority_dir):
        if method not in ("conventional", "harness", "outside", "ai"):
            raise HarnessError("UNKNOWN_METHOD", str(method))
        self.started_ns = time.monotonic_ns()
        self.usage_children = resource.getrusage(resource.RUSAGE_CHILDREN)
        self.usage_self = resource.getrusage(resource.RUSAGE_SELF)
        self.contract = deepcopy(validate_contract(contract))
        self.policies = deepcopy(validate_policies(policies))
        # A fixture uses start_ns=0. Freeze the real local monotonic origin before
        # any service starts; positive supplied origins support boundary tests.
        if self.contract["start_ns"] == 0:
            self.contract["start_ns"] = self.started_ns
        self.contract_digest = digest(self.contract)
        run_path, authority_path = Path(run_dir).absolute(), Path(authority_dir).absolute()
        if run_path == authority_path or run_path in authority_path.parents or authority_path in run_path.parents:
            raise HarnessError("UNSAFE_PATH", "authority and execution directories must be disjoint")
        self.method = method
        self.run_dir = fresh_directory(run_path)
        self.authority_dir = fresh_directory(authority_path)
        self.runtime_dir = self.run_dir / "runtime"
        self.evidence_dir = self.run_dir / "evidence"
        self.workspace = self.run_dir / "candidate"
        self.logs = self.run_dir / "logs"
        for p in (self.runtime_dir, self.evidence_dir, self.workspace, self.logs):
            p.mkdir()
        for name in ("capacity", "products", "inbox", "capacity-artifacts"):
            (self.runtime_dir / name).mkdir()
        self.view = candidate_view(self.contract, self.policies)
        write_json(self.workspace / "view.json", self.view)
        write_json(self.authority_dir / "contract.json", self.contract)
        write_json(self.authority_dir / "policies.json", self.policies)
        self.capacity_inputs = self.make_capacity_inputs()
        write_json(self.authority_dir / "capacity-inputs.json", self.capacity_inputs)
        self.reference = {"schema": "continuity-economy/reference/v1", "run_id": self.contract["run_id"],
            "contract_sha256": self.contract_digest, "policies_sha256": digest(self.policies),
            "source_sha256": self.contract["source_sha256"], "cutoff_sequence": self.contract["cutoff_sequence"],
            "source_complete": self.contract["source_complete"], "capacity_inputs_sha256": digest(self.capacity_inputs)}
        self.reference_sha256 = digest(self.reference)
        write_json(self.authority_dir / "reference.json", self.reference)
        self.tick = self.requests = self.retries = self.worker_restarts = self.candidate_restarts = 0
        self.children, self.services, self.capacity = [], {}, {}
        self.expected_kills, self.closed_pids, self.fault_done = set(), set(), set()
        self.fault_occurrences, self.pending_production, self.reservations = {}, {}, {}
        self.blocked_dependencies = set(self.contract["blocked_dependencies"])
        self.effective_permissions = {p["provider_id"]: deepcopy(p["permissions"]) for p in self.contract["providers"]}
        self.effective_capacities = {p["provider_id"] + "." + w["window_id"]: w["capacity"]
                                     for p in self.contract["providers"] for w in p["windows"]}
        self.candidate = None
        self.record = {"schema": "continuity-economy/controller/v1", "run_id": self.contract["run_id"],
            "contract_sha256": self.contract_digest, "policies_sha256": digest(self.policies),
            "method": method, "fixture_id": self.contract["fixture_id"], "cohort": self.contract["cohort"],
            "state": "INCOMPLETE", "started_monotonic_ns": self.started_ns, "finished_monotonic_ns": self.started_ns,
            "started_utc": datetime.now(timezone.utc).isoformat(), "implementation": implementation_identity(),
            "isolation": {"mechanism": "SECCOMP_BPF", "applied": False, "probe": {}},
            "fault_schedule": deepcopy(self.contract["fault_schedule"]), "faults_observed": [],
            "events": [], "errors": [], "target_verdict": "NOT_ESTABLISHED", "resources": {},
            "clock_tick": 0, "capacity_databases": [], "db_snapshots": {}}
        self.event("AUTHORITY_RETAINED", {"reference_sha256": self.reference_sha256,
            "seed": self.contract["seed"], "authority_kind": "SYNTHETIC_EXERCISE"})

    def make_capacity_inputs(self):
        c = self.contract
        orders = sorted([capacity_order(c, lot, attempt) for lot in lots(c)
                         for attempt in range(1, c["max_attempts"] + 1)], key=lambda o: o["order_id"])
        journal = [{"sequence": i, "type": "ACCEPT", **order} for i, order in enumerate(orders, 1)]
        ghost = {**orders[0], "order_id": "CANCELLED-SNAPSHOT-GHOST", "quantity": 1}
        journal.append({"sequence": len(journal)+1, "type": "ACCEPT", **ghost})
        journal.append({"sequence": len(journal)+1, "type": "CANCEL", "order_id": ghost["order_id"]})
        stale = [{**orders[0], "spec_sha256": digest({"stale": orders[0]["spec_sha256"]})}, ghost]
        result = {}
        for provider in c["providers"]:
            for window in provider["windows"]:
                route = "primary" if provider["role"] == "primary" else "backup"
                result[provider["provider_id"] + "." + window["window_id"]] = {
                    "provider_id": provider["provider_id"], "window_id": window["window_id"], "route": route,
                    "init": {"run_id": c["run_id"], "contract_sha256": self.contract_digest,
                        "capacities": {"primary": window["capacity"] if route == "primary" else 0,
                                       "backup": window["capacity"] if route == "backup" else 0},
                        "allowed_orders": orders, "snapshot": stale, "window_start": window["start"],
                        "window_end": window["end"], "source_sha256": digest(journal)},
                    "journal": journal, "cutoff": len(journal)}
        return result

    def event(self, event, detail=None):
        self.record["events"].append({"event": event, "tick": self.tick,
                                      "monotonic_ns": time.monotonic_ns(), "detail": detail or {}})

    @staticmethod
    def require_ok(response):
        if response.get("ok") is not True:
            raise HarnessError(response.get("code", "SERVICE_REFUSED"), str(response.get("detail", "")))
        return response["result"]

    def call(self, name, op, args=None, **kwargs):
        return self.require_ok(self.services[name].call(op, args or {}, **kwargs))

    def new_service(self, name, restart=False):
        db = self.runtime_dir / (name + ".sqlite")
        arguments = ["--db", db, "--contract", self.authority_dir / "contract.json"]
        if name == "participants":
            arguments += ["--policies", self.authority_dir / "policies.json"]
        elif name == "producer":
            arguments += ["--artifacts", self.runtime_dir / "products"]
        else:
            arguments += ["--inbox", self.runtime_dir / "inbox"]
        label = str(sum(1 for child in self.children if getattr(child, "economy_name", None) == name))
        client = LocalClient("continuity_economy." + name, arguments,
            self.logs / (name + "-" + label + ".stderr"), self.contract["bounds"]["service_timeout_ms"])
        client.economy_name = name
        self.children.append(client)
        self.services[name] = client
        self.call(name, "snapshot")
        self.event("SERVICE_STARTED", {"service": name, "pid": client.process.pid, "restart": restart})
        return client

    def initialize(self):
        for name in ("participants", "producer", "receiver"):
            self.new_service(name)
        for key, data in self.capacity_inputs.items():
            artifacts = self.runtime_dir / "capacity-artifacts" / key
            artifacts.mkdir()
            client = ServiceClient(ROOT, self.runtime_dir / "capacity" / (key + ".sqlite"),
                                   artifacts, self.logs / ("capacity-" + key + ".stderr"))
            client.timeout_ms = self.contract["bounds"]["service_timeout_ms"]
            self.children.append(client)
            self.capacity[key] = client
            self.require_ok(client.call("init", data["init"]))
            self.record["capacity_databases"].append({"provider_id": data["provider_id"],
                "window_id": data["window_id"], "route": data["route"], "path": "evidence/capacity/" + key + ".sqlite"})
            self.event("CAPACITY_SERVICE_STARTED", {"provider_id": data["provider_id"],
                "window_id": data["window_id"], "pid": client.process.pid})
        for dependency in sorted(self.blocked_dependencies):
            self.disable_dependency(dependency)
        self.apply_faults("initialize", {})

    def disable_dependency(self, dependency):
        self.blocked_dependencies.add(dependency)
        affected = []
        for provider in self.contract["providers"]:
            if provider["dependency"] == dependency:
                for window in provider["windows"]:
                    key = provider["provider_id"] + "." + window["window_id"]
                    self.require_ok(self.capacity[key].call("disable_route", {
                        "route": self.capacity_inputs[key]["route"], "now_tick": self.tick}))
                    affected.append(key)
        self.event("DEPENDENCY_DISABLED", {"dependency": dependency, "affected": affected})

    def mark_fault(self, fault, detail=None):
        self.fault_done.add(fault["event"])
        self.record["faults_observed"].append(deepcopy(fault))
        self.event(fault["event"], {"schedule": fault, **(detail or {})})

    def applicable_faults(self, op, args):
        applicable = []
        provider_id = args.get("provider_id")
        if "agreement_id" in args and "lot_id" in args:
            try:
                _, allocation, _ = self.allocation(args["agreement_id"], args["lot_id"])
                provider_id = allocation["provider_id"]
            except HarnessError:
                pass
        for fault in self.contract["fault_schedule"]:
            if fault["event"] in self.fault_done or fault["trigger"] != op:
                continue
            if fault["target"] not in ("ANY", provider_id) and op not in ("initialize", "propose", "decide", "inspect", "transfer"):
                continue
            name = fault["event"]
            self.fault_occurrences[name] = self.fault_occurrences.get(name, 0) + 1
            if self.fault_occurrences[name] == fault["occurrence"]:
                applicable.append(fault)
        return applicable

    def apply_faults(self, op, args):
        faults = self.applicable_faults(op, args)
        for fault in faults:
            name = fault["event"]
            if name in ("BACKUP_FAIL_BEFORE_RESERVE", "SHARED_DEPENDENCY_FAILURE"):
                provider = next((p for p in self.contract["providers"] if p["provider_id"] == fault["target"]), None)
                if provider is None:
                    raise HarnessError("FAULT_TARGET_INVALID", name)
                self.disable_dependency(provider["dependency"])
                self.mark_fault(fault, {"dependency": provider["dependency"]})
            elif name == "PERMISSION_REVOKE_BEFORE_TRANSFER":
                pid = fault["target"]
                if pid not in self.effective_permissions:
                    raise HarnessError("FAULT_TARGET_INVALID", name)
                self.effective_permissions[pid]["disclosure"] = False
                self.mark_fault(fault, {"provider_id": pid, "permission": "disclosure", "effective_tick": self.tick})
            elif name == "CONSENT_REVOKE_BEFORE_PRODUCTION":
                revocations = [r for r in self.contract["revocations"] if r["party_id"] == fault["target"] and r["action"] in ("produce", "consent")]
                if not revocations:
                    raise HarnessError("FAULT_TARGET_INVALID", "revocation must be frozen in contract")
                self.tick = max(self.tick, min(r["tick"] for r in revocations))
                self.mark_fault(fault, {"effective_tick": self.tick})
            elif name == "LATE_ACCEPTANCE":
                self.tick = max(self.tick, self.contract["deadline_tick"] + max(1, fault["value"]))
                self.mark_fault(fault, {"effective_tick": self.tick})
            elif name in ("POLICY_CHANGE_AFTER_PROPOSE", "FUNDING_WITHDRAWAL_AFTER_PROPOSE"):
                # These are applied after a durable proposal, below.
                pass
            elif name not in ("PRODUCTION_CRASH_HALF_WRITE", "REJECT_FIRST_CONTENT",
                               "ACK_LOST_AFTER_ACCEPTANCE", "CANDIDATE_RESTART_AFTER_ACCEPTANCE", "CAPACITY_COMPETITION"):
                raise HarnessError("FAULT_CAPABILITY_UNAVAILABLE", name)
        return faults

    def next_tick(self):
        self.tick += 1
        if self.tick > self.contract["observation_cutoff_tick"]:
            raise HarnessError("OBSERVATION_CUTOFF", str(self.tick))
        if time.monotonic_ns() - self.contract["start_ns"] > self.contract["wall_deadline_ms"] * 1_000_000:
            raise HarnessError("EXERCISE_TIMEOUT")

    def allocation(self, agreement_id, lot_id):
        identifier(agreement_id, "agreement_id"); identifier(lot_id, "lot_id")
        snapshot = self.call("participants", "status")
        agreement = next((a for a in snapshot["agreements"] if a["agreement_id"] == agreement_id), None)
        if agreement is None:
            raise HarnessError("AGREEMENT_NOT_FOUND", agreement_id)
        proposal = next(p["payload"] for p in snapshot["proposals"] if p["proposal_id"] == agreement["proposal_id"])
        allocation = next((a for a in proposal["allocations"] if a["lot_id"] == lot_id), None)
        if allocation is None:
            raise HarnessError("ALLOCATION_NOT_FOUND", lot_id)
        return agreement, allocation, proposal

    def route(self, allocation, action):
        provider = next((p for p in self.contract["providers"] if p["provider_id"] == allocation["provider_id"]), None)
        if provider is None:raise HarnessError("UNKNOWN_PROVIDER", allocation["provider_id"])
        window = next((w for w in provider["windows"] if w["window_id"] == allocation["window_id"]), None)
        if window is None:raise HarnessError("UNKNOWN_WINDOW", allocation["window_id"])
        permissions = self.effective_permissions[provider["provider_id"]]
        if not permissions["production"] or (action == "transfer" and provider["role"] != "primary" and not permissions["disclosure"]):
            raise HarnessError("PERMISSION_MISSING", provider["provider_id"])
        if provider["dependency"] in self.blocked_dependencies:
            raise HarnessError("DEPENDENCY_UNAVAILABLE", provider["provider_id"])
        return provider, window, provider["provider_id"] + "." + window["window_id"]

    def authorize(self, agreement_id, party_id, action, action_id):
        if not self.contract["source_complete"]:
            raise HarnessError("INCOMPLETE_SOURCE")
        result = self.call("participants", "authorize", {"agreement_id": agreement_id,
            "party_id": party_id, "action": action, "action_id": action_id, "tick": self.tick})
        if result.get("verdict") != "AUTHORIZED":
            raise HarnessError(result.get("code", "CONSENT_MISSING"), party_id)
        return result

    def reserve(self, args, faults=()):
        object_fields(args, {"agreement_id", "lot_id", "attempt"}, path="reserve")
        attempt = integer(args["attempt"], "attempt", 1, self.contract["max_attempts"])
        aid, lid = args["agreement_id"], args["lot_id"]
        agreement, allocation, _ = self.allocation(aid, lid)
        provider, window, slot = self.route(allocation, "produce")
        if self.tick < window["start"]:
            self.tick = window["start"]
            self.event("WINDOW_ADVANCED", {"provider_id": provider["provider_id"], "window_id": window["window_id"]})
        deadline = next(o["deadline_tick"] for o in self.contract["obligations"] if o["obligation_id"] == allocation["obligation_id"])
        if self.tick > self.contract["observation_cutoff_tick"]:
            raise HarnessError("OBSERVATION_CUTOFF", str(self.tick))
        if self.tick > deadline or self.tick >= window["end"]:
            raise HarnessError("DEADLINE_EXCEEDED", lid)
        key = f"{aid}.{lid}.A{attempt}"
        lookup = self.capacity[slot].call("lookup", {"key": key})
        if not lookup.get("ok") and lookup.get("code") != "RESERVATION_NOT_FOUND":
            self.require_ok(lookup)
        old = lookup.get("result", {})
        if old.get("status") in ("COMMITTED", "FULFILLED"):
            self.event("CAPACITY_RECONCILED", {"key": key, "status": old["status"]})
            return old
        self.authorize(aid, provider["provider_id"], "produce", key + ".reserve")
        if key in self.reservations:
            request = {**self.reservations[key], "now_tick": self.tick}
        else:
            order = capacity_order(self.contract, allocation, attempt)
            request = {k: v for k, v in order.items() if k != "deadline_tick"}
            request.update(run_id=self.contract["run_id"], contract_sha256=self.contract_digest,
                route=self.capacity_inputs[slot]["route"], key=key, window_start=window["start"],
                window_end=window["end"], expires_tick=min(self.tick+self.contract["lease_ticks"], window["end"]), now_tick=self.tick)
            self.reservations[key] = request
        competition = next((f for f in faults if f["event"] == "CAPACITY_COMPETITION"), None)
        if competition:
            return self.compete_capacity(agreement, allocation, attempt, request, slot, window, competition)
        result = self.require_ok(self.capacity[slot].call("reserve", request))
        self.event("CAPACITY_RESERVED", {"key": key, "slot": slot, "status": result.get("status")})
        return result

    def compete_capacity(self, agreement, allocation, attempt, request, slot, window, fault):
        """Two authorized lots race through explicit durable-transition barriers.

        The authored disruption first withdraws capacity to fault.value. Both
        demands belong to an already accepted arrangement; no extra buyer,
        disclosure, supplier or source of funds is fabricated for the race.
        """
        if fault["value"] > self.effective_capacities[slot]:
            raise HarnessError("FAULT_TARGET_INVALID", "competition must withdraw capacity")
        _, _, proposal = self.allocation(agreement["agreement_id"], allocation["lot_id"])
        other = next((a for a in proposal["allocations"] if a["provider_id"] == allocation["provider_id"]
                      and a["window_id"] == allocation["window_id"] and a["lot_id"] != allocation["lot_id"]), None)
        if other is None:
            raise HarnessError("FAULT_PRECONDITION", "two accepted lots in the same slot are required")
        other_key = f'{agreement["agreement_id"]}.{other["lot_id"]}.A{attempt}'
        self.authorize(agreement["agreement_id"], other["provider_id"], "produce", other_key + ".reserve")
        order = capacity_order(self.contract, other, attempt)
        second = {**request, **{k: v for k, v in order.items() if k != "deadline_tick"}, "key": other_key}
        self.reservations[other_key] = second
        capacity_change = self.require_ok(self.capacity[slot].call("capacity", {
            "route": request["route"], "new_capacity": fault["value"], "now_tick": self.tick}))
        self.effective_capacities[slot] = fault["value"]
        self.event("CAPACITY_WITHDRAWN", {"slot": slot, **capacity_change})
        requests = [request, second]
        priority = [0, 1] if self.contract["seed"] % 2 == 0 else [1, 0]
        clients, ids = [], []
        for index in range(2):
            client = ServiceClient(ROOT, self.runtime_dir / "capacity" / (slot + ".sqlite"),
                self.runtime_dir / "capacity-artifacts" / slot,
                self.logs / ("capacity-competition-" + str(index) + ".stderr"))
            client.timeout_ms = self.contract["bounds"]["service_timeout_ms"]
            clients.append(client)
            self.children.append(client)
            ids.append(client.start_request("reserve", requests[index], ["reserve.before_begin", "reserve.after_begin"]))
        def hook(index, expected):
            message = clients[index].receive()
            if message.get("id") != ids[index] or message.get("hook") != expected or message.get("event") != "hook":
                raise HarnessError("FAULT_HOOK_MISSING", str(message))
        for index in range(2):
            hook(index, "reserve.before_begin")
        first, last = priority
        clients[first].send({"continue": True})
        hook(first, "reserve.after_begin")
        clients[last].send({"continue": True})
        self.event("CAPACITY_RACE_BARRIER", {"slot": slot, "seed": self.contract["seed"],
            "keys": [r["key"] for r in requests], "priority": priority,
            "first_writer_holds_transaction": True, "both_requests_outstanding": True})
        clients[first].send({"continue": True})
        answers = [None, None]
        answers[first] = clients[first].receive()
        hook(last, "reserve.after_begin")
        clients[last].send({"continue": True})
        answers[last] = clients[last].receive()
        for index, client in enumerate(clients):
            if answers[index].get("id") != ids[index]:
                raise HarnessError("RPC_ID_MISMATCH", ids[index])
            client.close()
            self.closed_pids.add(client.process.pid)
        self.mark_fault(fault, {"slot": slot, "keys": [r["key"] for r in requests], "priority": priority,
            "responses": answers})
        return self.require_ok(answers[0])

    def produce(self, args, faults):
        object_fields(args, {"agreement_id", "lot_id", "attempt", "supersedes"}, path="produce")
        aid, lid = args["agreement_id"], args["lot_id"]
        attempt = integer(args["attempt"], "attempt", 1, self.contract["max_attempts"])
        agreement, allocation, _ = self.allocation(aid, lid)
        provider, window, slot = self.route(allocation, "produce")
        pid = f"{aid}.{lid}.A{attempt}"
        expected_supersedes = None if attempt == 1 else f"{aid}.{lid}.A1.D"
        if args["supersedes"] != expected_supersedes:
            raise HarnessError("INVALID_CORRECTION", pid)
        if attempt == 2:
            prior = self.call("receiver", "status", {"delivery_id": expected_supersedes})
            if prior.get("status") != "REJECTED":
                raise HarnessError("INVALID_CORRECTION", "a retained rejection is required")
        known = next((p for p in self.call("producer", "snapshot")["productions"] if p["production_id"] == pid), None)
        if known and known.get("status") == "MATERIALIZED":
            result = known
            self.event("PRODUCTION_RECONCILED", {"production_id": pid})
        else:
            self.authorize(aid, provider["provider_id"], "produce", pid + ".produce")
            allocation_state = self.require_ok(self.capacity[slot].call("lookup", {"key": pid}))
            if allocation_state.get("status") not in ("RESERVED", "COMMITTED"):
                raise HarnessError("CAPACITY_NOT_RESERVED", pid)
            self.require_ok(self.capacity[slot].call("commit", {"key": pid, "now_tick": self.tick}))
            self.call("participants", "charge_production", {"agreement_id": aid, "production_id": pid,
                "lot_id": lid, "attempt": attempt, "tick": self.tick})
            if pid not in self.pending_production:
                defect = "none"
                for fault in faults:
                    if fault["event"] == "REJECT_FIRST_CONTENT":
                        defect = "wrong_content"
                        self.mark_fault(fault, {"production_id": pid, "defect": defect})
                self.pending_production[pid] = {"production_id": pid, "arrangement_id": aid,
                    "provider_id": provider["provider_id"], "delivery_id": pid + ".D",
                    "obligation_id": allocation["obligation_id"], "capacity_key": pid, "lot_id": lid,
                    "attempt": attempt, "first_unit": allocation["first_unit"], "last_unit": allocation["last_unit"],
                    "supersedes": expected_supersedes, "defect": defect}
            request = {**self.pending_production[pid], "now_tick": self.tick}
            crash = next((f for f in faults if f["event"] == "PRODUCTION_CRASH_HALF_WRITE"), None)
            if crash:
                def on_hook(message):
                    if message["hook"] != "produce.after_half_write":
                        raise HarnessError("FAULT_HOOK_MISSING", str(message))
                    self.mark_fault(crash, {"production_id": pid, "hook": message["hook"]})
                    self.kill_service("producer")
                    raise KilledAtHook()
                try:
                    result = self.call("producer", "produce", request, hooks=["produce.after_half_write"], on_hook=on_hook)
                except KilledAtHook:
                    self.new_service("producer", restart=True)
                    self.worker_restarts += 1
                    self.retries += 1
                    self.next_tick()
                    request["now_tick"] = self.tick
                    self.event("PRODUCTION_RETRY", {"production_id": pid, "same_payload": True})
                    result = self.call("producer", "produce", request)
            else:
                result = self.call("producer", "produce", request)
        if result.get("status") != "MATERIALIZED" or result.get("observation") is None:
            raise HarnessError("PRODUCTION_NOT_ESTABLISHED", pid)
        # This old service receipt establishes consumed production capacity only;
        # digital delivery and independent recipient acceptance are separate.
        self.require_ok(self.capacity[slot].call("fulfill", {"key": pid, "now_tick": self.tick}))
        self.event("PRODUCT_MATERIALIZED", {"production_id": pid, "payload_sha256": result["payload_sha256"],
            "byte_count": result["byte_count"], "quantity": result["quantity"]})
        return result

    def transfer(self, args):
        object_fields(args, {"production_id"}, path="transfer")
        pid = identifier(args["production_id"], "production_id")
        produced = self.call("producer", "status", {"production_id": pid})
        if produced.get("status") != "MATERIALIZED":
            raise HarnessError("PRODUCTION_NOT_ESTABLISHED", pid)
        did = produced["delivery_id"]
        old = next((d for d in self.call("receiver", "snapshot")["deliveries"] if d["delivery_id"] == did), None)
        if old:
            self.event("RECEIPT_RECONCILED", {"delivery_id": did, "status": old["status"]})
            return old
        aid = produced["arrangement_id"]
        _, allocation, _ = self.allocation(aid, produced["lot_id"])
        provider, _, _ = self.route(allocation, "transfer")
        self.authorize(aid, provider["provider_id"], "transfer", did + ".transfer")
        source = self.runtime_dir / "products" / (pid + ".json")
        if source.is_symlink() or not source.is_file():
            raise HarnessError("PRODUCT_MISSING", pid)
        raw = source.read_bytes()
        checksum = hashlib.sha256(raw).hexdigest()
        if checksum != produced["payload_sha256"] or len(raw) != produced["byte_count"]:
            raise HarnessError("PRODUCT_CHANGED", pid)
        target = self.runtime_dir / "inbox" / (did + ".json")
        if target.exists():
            if target.is_symlink() or target.read_bytes() != raw:
                raise HarnessError("DELIVERY_CONTENT_CONFLICT", did)
        else:
            write_bytes(target, raw)
        received = self.call("receiver", "receive", {"delivery_id": did,
            "obligation_id": produced["obligation_id"], "now_tick": self.tick})
        self.event("PRODUCT_TRANSFERRED", {"production_id": pid, "delivery_id": did,
            "produced_sha256": checksum, "received_sha256": received["content_sha256"], "byte_count": len(raw)})
        return received

    def inspect(self, args, faults):
        object_fields(args, {"delivery_id"}, path="inspect")
        did = identifier(args["delivery_id"], "delivery_id")
        receipt = self.call("receiver", "status", {"delivery_id": did})
        if receipt.get("observation") is not None:
            self.retries += 1
            self.event("ACCEPTANCE_RECONCILED", {"delivery_id": did, "status": receipt["status"]})
            return receipt
        pid = did[:-2] if did.endswith(".D") else ""
        produced = self.call("producer", "status", {"production_id": pid})
        self.authorize(produced["arrangement_id"], self.policies["buyer"]["party_id"], "accept", did + ".inspect")
        interruptions = [f for f in faults if f["event"] in ("ACK_LOST_AFTER_ACCEPTANCE", "CANDIDATE_RESTART_AFTER_ACCEPTANCE")]
        if interruptions:
            def on_hook(message):
                if message["hook"] != "inspect.after_observation":
                    raise HarnessError("FAULT_HOOK_MISSING", str(message))
                # Independent receiver transition is durably observable at this
                # hook. The candidate has not received its acknowledgment.
                with sqlite3.connect((self.runtime_dir / "receiver.sqlite").as_uri()+"?mode=ro", uri=True) as db:
                    accepted = db.execute("SELECT decision FROM decisions WHERE delivery_id=?", (did,)).fetchone()
                if accepted is None or accepted[0] != "ACCEPTED":
                    raise HarnessError("FAULT_PRECONDITION", "acceptance did not occur")
                for fault in interruptions:
                    self.mark_fault(fault, {"delivery_id": did, "hook": message["hook"]})
                self.kill_service("receiver")
                if any(f["event"] == "CANDIDATE_RESTART_AFTER_ACCEPTANCE" for f in interruptions):
                    self.expected_kills.add(self.candidate.process.pid)
                    self.candidate.kill()
                    self.event("CANDIDATE_TERMINATED", {"pid": self.candidate.process.pid, "delivery_id": did})
                raise KilledAtHook()
            try:
                result = self.call("receiver", "inspect", {"delivery_id": did, "now_tick": self.tick},
                    hooks=["inspect.after_observation"], on_hook=on_hook)
            except KilledAtHook:
                self.new_service("receiver", restart=True)
                self.worker_restarts += 1
                self.event("ACKNOWLEDGMENT_UNCERTAIN", {"delivery_id": did})
                if any(f["event"] == "CANDIDATE_RESTART_AFTER_ACCEPTANCE" for f in interruptions):
                    raise RestartCandidate()
                raise HarnessError("ACK_UNKNOWN", did)
        else:
            result = self.call("receiver", "inspect", {"delivery_id": did, "now_tick": self.tick})
        self.event("RECIPIENT_INSPECTED", {"delivery_id": did, "status": result["status"],
            "accepted_units": result["accepted_units"], "timely": result["timely"]})
        return result

    def settle(self, args):
        object_fields(args, {"agreement_id"}, path="settle")
        aid = identifier(args["agreement_id"], "agreement_id")
        status = self.call("participants", "status")
        agreement = next((a for a in status["agreements"] if a["agreement_id"] == aid), None)
        if agreement is None:
            raise HarnessError("AGREEMENT_NOT_FOUND", aid)
        proposal = next(p["payload"] for p in status["proposals"] if p["proposal_id"] == agreement["proposal_id"])
        received = self.call("receiver", "snapshot")["deliveries"]
        acceptance_ids, covered = [], {}
        for allocation in proposal["allocations"]:
            choices = [d for d in received if d["delivery_id"].startswith(aid + "." + allocation["lot_id"] + ".A")
                       and d["status"] == "ACCEPTED" and d.get("timely") is True
                       and d.get("accepted_units") == allocation["last_unit"]-allocation["first_unit"]+1
                       and d.get("first_unit") == allocation["first_unit"] and d.get("last_unit") == allocation["last_unit"]]
            if len(choices) != 1:
                raise HarnessError("ACCEPTANCE_NOT_ESTABLISHED", allocation["lot_id"])
            accepted = choices[0]
            if accepted.get("observation") is None:
                raise HarnessError("ACCEPTANCE_NOT_ESTABLISHED", accepted["delivery_id"])
            acceptance_ids.append(accepted["delivery_id"])
            units = covered.setdefault(allocation["obligation_id"], set())
            addition = set(range(allocation["first_unit"], allocation["last_unit"]+1))
            if units & addition:
                raise HarnessError("DUPLICATE_ACCEPTANCE", allocation["lot_id"])
            units.update(addition)
        for obligation in self.contract["obligations"]:
            expected = set(range(1, obligation["quantity"]+1)) if obligation["status"] == "ACTIVE" else set()
            if covered.get(obligation["obligation_id"], set()) != expected:
                raise HarnessError("ACCEPTANCE_NOT_ESTABLISHED", obligation["obligation_id"])
        result = self.call("participants", "settle", {"agreement_id": aid,
            "acceptance_ids": sorted(acceptance_ids), "tick": self.tick})
        self.event("ARRANGEMENT_SETTLED", {"agreement_id": aid, "acceptance_ids": sorted(acceptance_ids)})
        return result

    def cancel(self, args):
        object_fields(args, {"agreement_id", "reason"}, path="cancel")
        aid = identifier(args["agreement_id"], "agreement_id")
        identifier(args["reason"], "reason")
        # The participant service cannot inspect receiver state. Its trusted
        # broker must protect accrued acceptance before releasing any capacity
        # or escrow. Partial settlement is not an authorized v0.2 operation.
        received = self.call("receiver", "snapshot")["deliveries"]
        if any(d["status"] == "ACCEPTED" and d["delivery_id"].startswith(aid + ".") for d in received):
            raise HarnessError("ACCRUED_ACCEPTANCE", aid)
        for slot, client in self.capacity.items():
            snapshot = self.require_ok(client.call("snapshot", {}))
            for row in snapshot["reservations"]:
                if row["key"].startswith(aid + ".") and row["status"] in ("RESERVED", "COMMITTED"):
                    self.require_ok(client.call("release", {"key": row["key"], "now_tick": self.tick}))
                    self.event("CAPACITY_RELEASED", {"key": row["key"], "slot": slot})
        result = self.call("participants", "cancel", {**args, "tick": self.tick})
        self.event("ARRANGEMENT_CANCELLED", args)
        return result

    def broker(self, op, args):
        if type(op) is not str or op not in self.contract["permitted_actions"] or type(args) is not dict:
            raise HarnessError("ACTION_NOT_ALLOWED", str(op))
        self.requests += 1
        if self.requests > self.contract["bounds"]["max_requests"]:
            raise HarnessError("REQUEST_BUDGET_EXHAUSTED")
        self.next_tick()
        self.event("BROKER_REQUEST", {"op": op, "args": args})
        # Structural admission precedes any scheduled or requested mutation.
        fields = {"status": set(), "propose": {"proposal"}, "decide": {"proposal_id"},
            "technical": {"proposal_id"}, "restore": {"provider_id", "window_id"},
            "reserve": {"agreement_id", "lot_id", "attempt"},
            "produce": {"agreement_id", "lot_id", "attempt", "supersedes"},
            "transfer": {"production_id"}, "inspect": {"delivery_id"},
            "settle": {"agreement_id"}, "cancel": {"agreement_id", "reason"}}
        object_fields(args, fields[op], path="broker." + op)
        for name, value in args.items():
            if name == "proposal":
                validate_proposal_shape(value)
            elif name == "attempt":
                integer(value, name, 1, self.contract["max_attempts"])
            elif name != "supersedes" or value is not None:
                identifier(value, name)
        faults = self.apply_faults(op, args)
        if op == "status":
            object_fields(args, set(), path="status")
            catalog = self.call("participants", "status")
            return {"contract": self.contract, "policies": catalog["current_policies"], "lots": lots(self.contract),
                "catalog": catalog, "receiver": self.call("receiver", "snapshot"), "producer": self.call("producer", "snapshot"),
                "tick": self.tick, "blocked_dependencies": sorted(self.blocked_dependencies),
                "effective_permissions": deepcopy(self.effective_permissions),
                "effective_capacities": deepcopy(self.effective_capacities)}
        if op == "propose":
            object_fields(args, {"proposal"}, path="propose")
            result = self.call("participants", "propose", {**args, "tick": self.tick})
            for fault in faults:
                if fault["event"] == "POLICY_CHANGE_AFTER_PROPOSE":
                    policy = self.call("participants", "status")["current_policies"]
                    policy["revision"] += 1
                    if fault["target"] == policy["buyer"]["party_id"]:
                        policy["buyer"]["max_price_minor"] = fault["value"]
                    elif fault["target"] == policy["coordinator"]["party_id"]:
                        policy["coordinator"]["operating_cost_minor"] = fault["value"]
                    else:
                        target = next((p for p in policy["providers"] if p["party_id"] == fault["target"]), None)
                        if target is None: raise HarnessError("FAULT_TARGET_INVALID", fault["event"])
                        target["unit_cost_minor"] = fault["value"]
                    self.next_tick()
                    self.call("participants", "replace_policies", {"policies": policy, "tick": self.tick})
                    self.mark_fault(fault, {"new_revision": policy["revision"]})
                elif fault["event"] == "FUNDING_WITHDRAWAL_AFTER_PROPOSE":
                    self.next_tick()
                    self.call("participants", "withdraw", {"party_id": fault["target"], "amount_minor": fault["value"],
                        "event_id": "frozen-funding-withdrawal", "tick": self.tick})
                    self.mark_fault(fault)
            return result
        if op == "decide":
            object_fields(args, {"proposal_id"}, path="decide")
            return self.call("participants", "decide", {**args, "tick": self.tick})
        if op == "technical":
            object_fields(args, {"proposal_id"}, path="technical")
            if self.contract["mode"] != "technical_control":
                raise HarnessError("TECHNICAL_CONTROL_FORBIDDEN")
            return self.call("participants", "grant_technical", {**args, "tick": self.tick})
        if op == "restore":
            object_fields(args, {"provider_id", "window_id"}, path="restore")
            provider, _, key = self.route(args, "produce")
            if provider["role"] != "primary":
                raise HarnessError("ACTION_NOT_ALLOWED", "restore requires the primary role")
            snapshot = self.require_ok(self.capacity[key].call("snapshot", {}))
            if snapshot["metadata"].get("recovery_cutoff") is not None:
                return {"status": "ALREADY_RECOVERED"}
            start = time.monotonic_ns()
            self.require_ok(self.capacity[key].call("expire", {"now_tick": self.tick}))
            result = self.require_ok(self.capacity[key].call("restore", {
                "events": self.capacity_inputs[key]["journal"], "cutoff": self.capacity_inputs[key]["cutoff"]}))
            self.event("PRIMARY_RESTORED", {"provider_id": provider["provider_id"], "window_id": args["window_id"],
                "recovery_ns": time.monotonic_ns()-start, "discrepancies": result["discrepancies"]})
            return result
        if op == "reserve": return self.reserve(args, faults)
        if op == "produce": return self.produce(args, faults)
        if op == "transfer": return self.transfer(args)
        if op == "inspect": return self.inspect(args, faults)
        if op == "settle": return self.settle(args)
        if op == "cancel": return self.cancel(args)
        raise HarnessError("ACTION_NOT_ALLOWED", op)

    def kill_service(self, name):
        client = self.services[name]
        self.expected_kills.add(client.process.pid)
        client.kill()
        self.event("SERVICE_TERMINATED", {"service": name, "pid": client.process.pid})
        client.close()
        self.closed_pids.add(client.process.pid)

    def start_candidate(self, restart=False):
        candidate = ProcessChannel([sys.executable, "-m", "continuity_economy.candidate", "--method", self.method,
            "--authority-probe", str(self.authority_dir / "contract.json"),
            "--workspace-probe", str(self.workspace / "view.json")], ROOT,
            self.logs / ("candidate-" + str(self.candidate_restarts) + ".stderr"),
            self.contract["bounds"]["service_timeout_ms"])
        self.candidate = candidate
        self.children.append(candidate)
        message = candidate.receive()
        object_fields(message, {"event", "isolation"}, path="candidate.sandbox")
        isolation = object_fields(message["isolation"], {"mechanism", "applied", "probe"})
        object_fields(isolation["probe"], PROBES)
        if message["event"] != "sandbox" or isolation["mechanism"] != "SECCOMP_BPF" or isolation["applied"] is not True or any(isolation["probe"][p] is not True for p in PROBES):
            raise HarnessError("ISOLATION_UNAVAILABLE")
        self.record["isolation"] = isolation
        self.event("CANDIDATE_STARTED", {"pid": candidate.process.pid, "restart": restart,
            "isolation": isolation})
        candidate.send({"view": self.view, "restart": restart})

    def execute_candidate(self):
        self.start_candidate()
        telemetry_count = 0
        while True:
            message = self.candidate.receive()
            if message.get("event") == "telemetry":
                object_fields(message, {"event", "kind", "report"}, path="candidate.telemetry")
                if message["kind"] != "planning" or type(message["report"]) is not dict:
                    raise HarnessError("RPC_FRAME_INVALID", "planning telemetry")
                telemetry_count += 1
                if telemetry_count > self.contract["bounds"]["max_proposals"] + 3:
                    raise HarnessError("TELEMETRY_BUDGET_EXHAUSTED")
                self.event("CANDIDATE_PLANNING", {"pid": self.candidate.process.pid,
                    "measurement_kind": "CANDIDATE_REPORTED", "report": message["report"]})
                continue
            if message.get("event") == "done":
                object_fields(message, {"event", "result"})
                result = object_fields(message["result"], {"verdict", "reason", "searches", "interventions"})
                identifier(result["verdict"], "verdict")
                self.record["target_verdict"] = result["verdict"]
                self.event("CANDIDATE_DONE", result)
                return
            if message.get("event") == "error":
                raise HarnessError(message.get("code", "CANDIDATE_ERROR"), str(message.get("detail", "")))
            object_fields(message, {"event", "id", "op", "args"}, path="candidate.tool")
            if message["event"] != "tool":
                raise HarnessError("RPC_FRAME_INVALID")
            identifier(message["id"], "request.id")
            try:
                result = self.broker(message["op"], message["args"])
                response = {"id": message["id"], "ok": True, "result": result}
            except RestartCandidate:
                old = self.candidate
                old.close()
                self.closed_pids.add(old.process.pid)
                self.candidate_restarts += 1
                if self.candidate_restarts > 2:
                    raise HarnessError("RESTART_BUDGET_EXHAUSTED")
                self.next_tick()
                self.start_candidate(restart=True)
                continue
            except HarnessError as error:
                if error.code in {"OBSERVATION_CUTOFF", "EXERCISE_TIMEOUT", "REQUEST_BUDGET_EXHAUSTED",
                                  "PROCESS_TIMEOUT", "PROCESS_WRITE_TIMEOUT", "PROCESS_EXITED",
                                  "RPC_FRAME_INVALID", "RPC_ID_MISMATCH"}:
                    raise
                self.event("BROKER_REFUSED", {"op": message["op"], "code": error.code, "detail": error.detail})
                response = {"id": message["id"], "ok": False, "code": error.code,
                    "detail": localized_error(error.code)}
            self.candidate.send(response)

    def database_paths(self):
        result = {"evidence/" + name + ".sqlite": self.runtime_dir / (name + ".sqlite") for name in self.services}
        result.update({"evidence/capacity/" + key + ".sqlite": self.runtime_dir / "capacity" / (key + ".sqlite") for key in self.capacity})
        return result

    def capture(self):
        # All writers are idle at this explicit RPC boundary. Full database
        # logical dumps include the producer payload and imported recipient units.
        for relative, path in self.database_paths().items():
            self.record["db_snapshots"][relative] = database_digest(path)
        for name in sorted(self.services):
            write_json(self.runtime_dir / (name + "-final-state.json"), self.call(name, "snapshot"))
        for name, client in list(self.services.items()) + list(self.capacity.items()):
            checkpoint = self.require_ok(client.call("checkpoint", {}))
            if checkpoint.get("status") != "CHECKPOINTED" or checkpoint.get("sqlite") != [0, 0, 0]:
                raise HarnessError("DATABASE_CHECKPOINT_INCOMPLETE", name)
            self.event("DATABASE_CHECKPOINT", {"database": name, **checkpoint})

    def close_children(self):
        errors = []
        for client in self.children:
            if client.process.pid not in self.closed_pids:
                try:
                    client.close()
                except (OSError, ValueError, subprocess.SubprocessError) as error:
                    errors.append(type(error).__name__)
                finally:
                    self.closed_pids.add(client.process.pid)
        unexpected = [c.process.pid for c in self.children if c.process.poll() != 0 and c.process.pid not in self.expected_kills]
        if unexpected:
            raise HarnessError("WORKER_EXIT_UNEXPECTED", str(unexpected))
        if errors:
            raise HarnessError("WORKER_CLOSURE_FAILED", str(errors))

    def finalize(self):
        for relative, source in self.database_paths().items():
            finalized_database(source, self.run_dir / relative, self.record["db_snapshots"][relative])
        for directory in ("products", "inbox", "capacity-artifacts"):
            original = self.runtime_dir / directory
            for source in sorted(original.rglob("*.json")):
                if source.is_symlink() or not source.is_file():
                    raise HarnessError("UNSAFE_PATH", str(source))
                target = self.evidence_dir / directory / source.relative_to(original)
                target.parent.mkdir(parents=True, exist_ok=True)
                write_bytes(target, source.read_bytes())
        self.event("EVIDENCE_FINALIZED", {"databases": len(self.record["db_snapshots"]),
            "snapshot_method": "SQLITE_BACKUP_DELETE_FULL_LOGICAL_DIGEST"})

    def error(self, error):
        bounded = getattr(error, "code", "") in {"OBSERVATION_CUTOFF", "EXERCISE_TIMEOUT", "REQUEST_BUDGET_EXHAUSTED"}
        self.record["state"] = "INCOMPLETE" if bounded else "ERROR"
        self.record["target_verdict"] = "NOT_ESTABLISHED" if bounded else "ERROR"
        code = getattr(error, "code", "CONTROLLER_ERROR")
        detail = {"code": code, "detail": str(error)[:1000], "message": localized_error(code)}
        self.record["errors"].append(detail)
        self.event("EXECUTION_ERROR", detail)
        if bounded and self.candidate is not None and self.candidate.process.poll() is None:
            # End the bounded experiment instead of leaving a candidate waiting
            # for a response past the frozen observation/resource limit.
            self.expected_kills.add(self.candidate.process.pid)
            self.candidate.kill()
            self.candidate.close()
            self.closed_pids.add(self.candidate.process.pid)
            self.event("CANDIDATE_BOUNDED_STOP", {"pid": self.candidate.process.pid, "code": detail["code"]})

    def run(self):
        captured = False
        try:
            if self.method == "ai":
                self.record["state"] = "NOT_RUN"
                self.record["target_verdict"] = "NOT_RUN"
                self.event("AI_NOT_RUN", {"reason": "NO_AUTHORIZED_LOCAL_AI_CAPABILITY", "required": "locally authorized executable adapter and measured inference resources"})
            else:
                self.initialize()
                self.execute_candidate()
                self.capture()
                captured = True
        except (HarnessError, OSError, ValueError, KeyError, TypeError, sqlite3.Error, subprocess.SubprocessError) as error:
            self.error(error)
            # Preserve incomplete committed evidence wherever its state can be
            # captured safely. This never changes an ERROR into COMPLETE.
            try:
                self.capture()
                captured = True
            except (HarnessError, OSError, ValueError, KeyError, TypeError, sqlite3.Error):
                pass
        finally:
            try:
                self.close_children()
            except (HarnessError, OSError, ValueError, subprocess.SubprocessError) as error:
                self.error(error)
            if captured:
                try:
                    self.finalize()
                    if not self.record["errors"]:
                        self.record["state"] = "COMPLETE"
                except (HarnessError, OSError, ValueError, KeyError, sqlite3.Error) as error:
                    self.error(error)
            finished = time.monotonic_ns()
            self.record["finished_monotonic_ns"] = finished
            self.record["clock_tick"] = self.tick
            child_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
            own_usage = resource.getrusage(resource.RUSAGE_SELF)
            self.record["resources"] = {
                "wall_ns": finished-self.started_ns,
                "cpu_user_ns": int((child_usage.ru_utime-self.usage_children.ru_utime)*1_000_000_000),
                "cpu_system_ns": int((child_usage.ru_stime-self.usage_children.ru_stime)*1_000_000_000),
                "controller_cpu_user_ns": int((own_usage.ru_utime-self.usage_self.ru_utime)*1_000_000_000),
                "controller_cpu_system_ns": int((own_usage.ru_stime-self.usage_self.ru_stime)*1_000_000_000),
                "peak_rss_bytes": None, "storage_bytes": sum(p.stat().st_size for p in self.run_dir.rglob("*") if p.is_file()),
                "requests": self.requests, "retries": self.retries, "worker_restarts": self.worker_restarts,
                "service_requests": sum(getattr(c, "counter", 0) for c in self.children),
                "child_processes": len(self.children),
                "candidate_restarts": self.candidate_restarts, "human_interventions": 0,
                "authority_storage_bytes_before_seal": sum(p.stat().st_size for p in self.authority_dir.rglob("*") if p.is_file()),
                "preparation_labor_seconds": None, "integration_labor_seconds": None,
                "adaptation_labor_seconds": None, "verification_labor_seconds": None, "monetary_cost": None,
                "measurement_scope": "controller and child processes through closed evidence finalization; excludes final controller record, execution seal, result and Passport publication overhead; child CPU may include concurrent exercises launched by this same controller process",
                "storage_scope": "files present in run directory before final controller record and authority execution seal; excludes later result and Passport files; authority_storage_bytes_before_seal is reported separately"}
            write_json(self.run_dir / "controller.json", self.record)
            files = {p.relative_to(self.run_dir).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(self.evidence_dir.rglob("*")) if p.is_file()}
            write_json(self.authority_dir / "execution.json", {"schema": "continuity-economy/execution-seal/v1",
                "run_id": self.contract["run_id"], "contract_sha256": self.contract_digest,
                "controller_sha256": digest(self.record), "files": files})
        return self.record
