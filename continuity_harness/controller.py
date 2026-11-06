"""Trusted local exercise controller with real processes and durable evidence."""

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

from . import __version__
from .fixtures import candidate_view, stale_snapshot
from .rpc import ProcessChannel, ServiceClient
from .schema import (HarnessError, canonical, digest, expected_obligations,
                     object_fields, strict_load, strict_loads, validate_contract, identifier)


ROOT = Path(__file__).resolve().parents[1]


def write_json(path, value):
    path = Path(path)
    data = canonical(value) + b"\n"
    with open(path, "xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def implementation_identity():
    source = {}
    for path in sorted((ROOT / "continuity_harness").glob("*.py")):
        source[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    for path in sorted((ROOT / "experiments/harness-v0.1").glob("*.json")):
        source[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    def git(*args):
        r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else "UNAVAILABLE"
    return {"version": __version__, "git_commit": git("rev-parse", "HEAD"),
            "dirty": bool(git("status", "--porcelain")), "source_sha256": source,
            "environment": {"python": sys.version, "platform": platform.platform(), "sqlite_version": sqlite3.sqlite_version,
                            "argv": list(getattr(sys, "orig_argv", [sys.executable, *sys.argv])),
                            "working_directory": str(Path.cwd())}}


def fresh_directory(path):
    p = Path(path).absolute()
    for ancestor in (p, *p.parents):
        if ancestor.is_symlink():
            raise HarnessError("UNSAFE_PATH", str(ancestor))
    p.mkdir(parents=True, exist_ok=False)
    return p


class RestartCandidate(Exception):
    pass


class Controller:
    def __init__(self, contract, method, run_dir, authority_dir, *, view=None):
        self.contract = deepcopy(validate_contract(contract))
        if method not in ("conventional", "harness", "ablation", "ai"):
            raise HarnessError("UNKNOWN_METHOD", method)
        self.method = method
        self.run_dir = fresh_directory(run_dir)
        self.authority_dir = fresh_directory(authority_dir)
        self.evidence_dir = self.run_dir / "evidence"
        self.evidence_dir.mkdir()
        self.artifacts = self.evidence_dir / "artifacts"
        self.artifacts.mkdir()
        self.workspace = self.run_dir / "candidate"
        self.workspace.mkdir()
        self.logs = self.run_dir / "logs"
        self.logs.mkdir()
        self.runtime_dir = self.run_dir / "runtime"
        self.runtime_dir.mkdir()
        self.db = self.runtime_dir / "service.sqlite"
        self.evidence_db = self.evidence_dir / "service.sqlite"
        self.view = deepcopy(view) if view is not None else candidate_view(self.contract)
        write_json(self.workspace / "view.json", self.view)
        write_json(self.authority_dir / "contract.json", self.contract)
        self.reference = {"schema": "continuity-harness/reference/v1", "run_id": contract["run_id"],
                          "contract_sha256": digest(contract), "source_sha256": contract["source_sha256"],
                          "cutoff_sequence": contract["cutoff_sequence"], "source_complete": contract["source_complete"]}
        write_json(self.authority_dir / "reference.json", self.reference)
        write_json(self.authority_dir / "journal.json", contract["source_events"])
        self.reference_sha256 = digest(self.reference)
        self.service = None
        self.candidate = None
        self.children = []
        self.expected_kills = set()
        self.final_service_snapshot = None
        self.tick = 0
        self.requests = 0
        self.retries = 0
        self.worker_restarts = 0
        self.fault_done = set()
        self.reservations = {}
        self.effective_permissions = deepcopy(contract["permissions"])
        self.blocked_dependencies = set(contract["blocked_dependencies"])
        self.record = {"schema": "continuity-harness/controller/v1", "run_id": contract["run_id"],
                       "contract_sha256": digest(contract), "method": method, "scenario": contract["scenario"],
                       "seed": contract["seed"], "state": "INCOMPLETE", "started_monotonic_ns": 0,
                       "finished_monotonic_ns": 0, "started_utc": "", "implementation": implementation_identity(),
                       "isolation": {"mechanism": "SECCOMP_BPF", "applied": False, "probe": {}},
                       "fault_schedule": contract["fault_schedule"], "faults_observed": [], "events": [],
                       "errors": [], "target_verdict": "NOT_ESTABLISHED", "resources": {}, "recovery_ms": None}

    def event(self, name, detail=None):
        self.record["events"].append({"event": name, "tick": self.tick,
                                       "monotonic_ns": time.monotonic_ns(), "detail": detail or {}})

    def fault(self, name):
        if name in self.fault_done:
            return
        match = next((x for x in self.contract["fault_schedule"] if x["event"] == name), None)
        if match is None:
            raise HarnessError("UNREGISTERED_FAULT", name)
        self.fault_done.add(name)
        self.record["faults_observed"].append(match)
        self.event(name)

    def new_service(self, label):
        client = ServiceClient(ROOT, self.db, self.artifacts, self.logs / f"service-{label}.stderr")
        self.children.append(client)
        self.event("SERVICE_STARTED", {"pid": client.process.pid, "label": label})
        return client

    def require_ok(self, response):
        if not response.get("ok"):
            raise HarnessError(response.get("code", "SERVICE_REFUSED"), str(response.get("detail", "")))
        return response["result"]

    def initialize(self):
        self.service = self.new_service("initial")
        c = self.contract
        self.require_ok(self.service.call("init", {"run_id": c["run_id"], "contract_sha256": digest(c),
                        "capacities": c["capacities"], "allowed_orders": expected_obligations(c),
                        "snapshot": stale_snapshot(c), "window_start": c["window"]["start"],
                        "window_end": c["window"]["end"], "source_sha256": c["source_sha256"]}))
        for route in ("primary", "backup"):
            if c["dependencies"][route] in c["blocked_dependencies"]:
                self.require_ok(self.service.call("disable_route", {"route": route, "now_tick": self.tick}))
                if route == "primary" and any(x["event"] == "PRIMARY_UNAVAILABLE" for x in c["fault_schedule"]):
                    self.fault("PRIMARY_UNAVAILABLE")
                else:
                    self.event("DEPENDENCY_ROUTE_DISABLED", {"route": route})

    def start_candidate(self, restart=False):
        label = "restart" if restart else "initial"
        candidate = ProcessChannel([sys.executable, "-m", "continuity_harness.candidate", "--method", self.method,
                      "--authority-probe", str(self.authority_dir / "contract.json"),
                      "--workspace-probe", str(self.workspace / "view.json")], ROOT,
                      self.logs / f"candidate-{label}.stderr")
        self.children.append(candidate)
        self.candidate = candidate
        sandbox = candidate.receive()
        object_fields(sandbox, {"event", "isolation"}, path="candidate.sandbox")
        isolation = object_fields(sandbox["isolation"], {"mechanism", "applied", "probe"}, path="candidate.isolation")
        probes = {"authority_open_denied", "workspace_open_denied", "network_denied", "spawn_denied", "process_inspection_denied"}
        object_fields(isolation["probe"], probes, path="candidate.probes")
        if sandbox["event"] != "sandbox" or isolation["applied"] is not True or isolation["mechanism"] != "SECCOMP_BPF" or not all(isolation["probe"][p] is True for p in probes):
            raise HarnessError("ISOLATION_UNAVAILABLE", str(sandbox))
        self.record["isolation"] = sandbox["isolation"]
        self.event("CANDIDATE_STARTED", {"pid": candidate.process.pid, "restart": restart})
        candidate.send({"view": self.view, "restart": restart})

    def reserve_arguments(self, request):
        fields = {"order_id", "recipient", "product", "spec_sha256", "quantity", "route", "key"}
        object_fields(request, fields, path="broker.reserve")
        for name in ("order_id", "recipient", "product", "key"):
            identifier(request[name], "broker.reserve." + name)
        c = self.contract
        if request["route"] not in c["allowed_routes"] or c["dependencies"].get(request["route"]) in self.blocked_dependencies:
            raise HarnessError("DEPENDENCY_UNAVAILABLE", str(request["route"]))
        self.authorize_route(request["route"])
        if request["key"] in self.reservations:
            old = self.reservations[request["key"]]
            args = dict(old, now_tick=self.tick)
            for key in fields:
                if args[key] != request[key]:
                    raise HarnessError("IDEMPOTENCY_CONFLICT", key)
            return args
        args = dict(request, run_id=c["run_id"], contract_sha256=digest(c),
                    window_start=c["window"]["start"], window_end=c["window"]["end"],
                    expires_tick=min(self.tick + c["lease_ticks"], c["window"]["end"]), now_tick=self.tick)
        return args

    def revoke_permission(self, name):
        """Trusted controller intervention, never exposed as a candidate tool."""
        if name not in self.effective_permissions:
            raise HarnessError("UNKNOWN_PERMISSION", str(name))
        self.effective_permissions[name] = False
        self.event("PERMISSION_REVOKED", {"permission": name})

    def authorize_route(self, route):
        if not self.effective_permissions["activation"] or (route == "backup" and not self.effective_permissions["sharing"]):
            raise HarnessError("PERMISSION_MISSING", route)

    def authorize_action(self, op, args):
        if op in ("restore", "reserve_batch", "commit", "fulfill") and not self.effective_permissions["activation"]:
            raise HarnessError("PERMISSION_MISSING", op)
        if op in ("commit", "fulfill"):
            reservation = self.reservations.get(args.get("key"))
            if reservation is None:
                raise HarnessError("UNKNOWN_CANDIDATE_KEY")
            route = reservation["route"]
            self.authorize_route(route)
            if route not in self.contract["allowed_routes"] or self.contract["dependencies"][route] in self.blocked_dependencies:
                raise HarnessError("DEPENDENCY_UNAVAILABLE", route)
        if op == "restore" and "primary" not in self.contract["allowed_routes"]:
            raise HarnessError("ROUTE_NOT_AUTHORIZED", "primary")

    def concurrent_reserve(self, arguments):
        # Both requests reach a recorded barrier.  The first-priority transaction
        # holds the SQLite write lock while the second request is released.
        # This makes the declared ordering reproducible without arbitrary sleeps.
        first, second = self.new_service("race-first"), self.new_service("race-second")
        for client, args in zip((first, second), arguments):
            client.start_request("reserve", args, ["reserve.before_begin", "reserve.after_begin"])
        for client in (first, second):
            message = client.receive()
            if message.get("hook") != "reserve.before_begin":
                raise HarnessError("FAULT_HOOK_MISSING", str(message))
        first.send({"continue": True})
        if first.receive().get("hook") != "reserve.after_begin":
            raise HarnessError("FAULT_HOOK_MISSING", "reserve.after_begin")
        second.send({"continue": True})
        self.event("CONCURRENT_RESERVATIONS_OUTSTANDING", {"order_ids": [x["order_id"] for x in arguments]})
        first.send({"continue": True})
        result_first = first.receive()
        if second.receive().get("hook") != "reserve.after_begin":
            raise HarnessError("FAULT_HOOK_MISSING", "second.reserve.after_begin")
        second.send({"continue": True})
        result_second = second.receive()
        first.close()
        second.close()
        self.fault("CONCURRENT_FINAL_CAPACITY")
        return {"ok": True, "result": {"results": [result_first, result_second]}}

    def ambiguous_fulfillment(self, key):
        self.service.start_request("fulfill", {"key": key, "now_tick": self.tick}, ["fulfill.after_commit"])
        message = self.service.receive()
        if message.get("hook") != "fulfill.after_commit":
            raise HarnessError("FAULT_HOOK_MISSING", str(message))
        self.fault("ACK_LOST_AFTER_DURABLE_FULFILLMENT")
        # Simulate a transport retry before the original caller has any outcome.
        retry = self.new_service("uncertain-retry")
        response = retry.call("fulfill", {"key": key, "now_tick": self.tick})
        self.require_ok(response)
        self.retries += 1
        self.event("AMBIGUOUS_RETRY_RESULT", response)
        self.fault("RETRY_WHILE_OUTCOME_UNKNOWN")
        retry.close()
        self.service.kill()
        self.expected_kills.add(self.service.process.pid)
        self.fault("SERVICE_KILLED_AFTER_COMMIT")
        self.candidate.kill()
        self.expected_kills.add(self.candidate.process.pid)
        self.fault("CANDIDATE_KILLED_AFTER_REQUEST")
        self.service.close()
        self.candidate.close()
        self.service = self.new_service("restarted")
        self.worker_restarts += 2
        raise RestartCandidate()

    def broker(self, message):
        object_fields(message, {"op", "args"}, path="broker.message")
        op, args = message["op"], message["args"]
        if type(op) is not str or type(args) is not dict:
            raise HarnessError("INVALID_TYPE", "broker.op/args")
        identifier(op, "broker.op")
        self.requests += 1
        self.tick += 1
        if self.requests > 128:
            raise HarnessError("REQUEST_BUDGET_EXCEEDED")
        self.event("CANDIDATE_REQUEST", {"op": op, "args": args})
        self.authorize_action(op, args)
        if op == "restore":
            object_fields(args, {"events", "cutoff"}, path="broker.restore")
            started = time.monotonic_ns()
            reply = self.service.call(op, args)
            if reply.get("ok"):
                elapsed_ns = time.monotonic_ns() - self.record["started_monotonic_ns"]
                self.record["recovery_ms"] = (elapsed_ns + 999_999) // 1_000_000
                self.event("PRIMARY_RECOVERED", {"operation_ns": time.monotonic_ns() - started})
        elif op in ("orders", "reconcile"):
            object_fields(args, set(), path="broker." + op)
            reply = self.service.call(op, args)
            if op == "reconcile" and "CANDIDATE_KILLED_AFTER_REQUEST" in self.fault_done:
                self.fault("RESTART_RECONCILIATION")
        elif op == "reserve_batch":
            object_fields(args, {"requests"}, path="broker.reserve_batch")
            if type(args["requests"]) is not list or len(args["requests"]) > 1024:
                raise HarnessError("INVALID_TYPE", "broker.requests")
            # Preflight the complete batch before recording or sharing requests.
            reservations = [self.reserve_arguments(x) for x in args["requests"]]
            pending = {}
            for reservation in reservations:
                key = reservation["key"]
                if key in pending and pending[key] != reservation:
                    raise HarnessError("IDEMPOTENCY_CONFLICT", key)
                pending[key] = reservation
            for key, reservation in pending.items():
                self.reservations.setdefault(key, reservation)
            if self.contract["scenario"] == "constrained" and "CONCURRENT_FINAL_CAPACITY" not in self.fault_done and len(reservations) == 2:
                reply = self.concurrent_reserve(reservations)
            else:
                reply = {"ok": True, "result": {"results": [self.service.call("reserve", a) for a in reservations]}}
        elif op in ("lookup", "commit", "fulfill", "release"):
            object_fields(args, {"key"}, path="broker." + op)
            identifier(args["key"], "broker.key")
            if args["key"] not in self.reservations:
                raise HarnessError("UNKNOWN_CANDIDATE_KEY")
            if op == "fulfill" and self.contract["scenario"] == "constrained" and "ACK_LOST_AFTER_DURABLE_FULFILLMENT" not in self.fault_done:
                return self.ambiguous_fulfillment(args["key"])
            request = args if op == "lookup" else dict(args, now_tick=self.tick)
            reply = self.service.call(op, request)
        else:
            raise HarnessError("BROKER_OPERATION_FORBIDDEN", str(op))
        self.event("BROKER_RESULT", {"op": op, "response": reply})
        return reply

    def remaining_execution_ms(self):
        # Business acceptance uses the frozen deadline itself. This additional
        # controller stop budget permits bounded error handling after that time.
        limit = self.record["started_monotonic_ns"] + (self.contract["wall_deadline_ms"] + 10000) * 1_000_000
        remaining = (limit - time.monotonic_ns()) // 1_000_000
        if remaining <= 0:
            raise HarnessError("EXECUTION_DEADLINE_EXCEEDED")
        return min(10000, remaining)

    def execute_candidate(self):
        restart = False
        while True:
            self.start_candidate(restart)
            try:
                while True:
                    self.candidate.timeout_ms = self.remaining_execution_ms()
                    message = self.candidate.receive()
                    if message.get("event") == "done":
                        object_fields(message, {"event", "result"}, path="candidate.done")
                        target = object_fields(message["result"], {"verdict", "reason", "outcomes"}, path="candidate.result")
                        if target["verdict"] not in ("COMPLETED", "PARTIAL", "REFUSED", "ERROR", "NOT_ESTABLISHED", "NOT_RUN") or type(target["outcomes"]) is not list:
                            raise HarnessError("CANDIDATE_PROTOCOL_ERROR", "result")
                        identifier(target["reason"], "candidate.reason")
                        for row in target["outcomes"]:
                            object_fields(row, {"order_id", "state", "code"}, path="candidate.outcome")
                            for key in row:
                                identifier(row[key], "candidate.outcome." + key)
                        self.record["target_verdict"] = message["result"]["verdict"]
                        self.event("CANDIDATE_FINISHED", message["result"])
                        self.candidate.close()
                        if self.candidate.process.returncode != 0:
                            raise HarnessError("CANDIDATE_EXIT_ERROR", str(self.candidate.process.returncode))
                        return
                    if message.get("event") == "error":
                        raise HarnessError(message.get("code", "CANDIDATE_ERROR"), message.get("detail", ""))
                    try:
                        response = self.broker(message)
                    except HarnessError as error:
                        if error.code in {"REQUEST_BUDGET_EXCEEDED", "EXECUTION_DEADLINE_EXCEEDED", "FAULT_HOOK_MISSING", "UNREGISTERED_FAULT"} or error.code.startswith("PROCESS_"):
                            raise
                        response = {"ok": False, "code": error.code, "detail": error.detail}
                        self.event("BROKER_REFUSAL", response)
                    self.candidate.send(response)
            except RestartCandidate:
                if restart:
                    raise HarnessError("RESTART_BUDGET_EXCEEDED")
                restart = True

    def finalize_database(self):
        """Publish a standalone durable ledger after all owned writers exit.

        SQLite backup reads the committed database view, including any required
        WAL; copying the main file alone is not a safe snapshot procedure.
        Runtime files stay separate and are retained for diagnosis. Acceptance
        still inspects the complete finalized database and actual artifacts.
        """
        if any(child.process.poll() is None for child in self.children):
            raise HarnessError("WORKER_STILL_RUNNING", "database finalization")
        if self.final_service_snapshot is None:
            raise HarnessError("DATABASE_STATE_NOT_CAPTURED")
        if self.evidence_db.exists() or self.evidence_db.is_symlink():
            raise HarnessError("OUTPUT_EXISTS", "finalized database")
        # Never open an evidence-path database for SQLite writes. All managed
        # temporary journals belong to the retained runtime directory.
        temporary = self.runtime_dir / "service.sqlite.snapshot.tmp"
        with open(temporary, "xb"):
            pass
        started = time.monotonic_ns()
        def bounded_backup(status, remaining, total):
            if time.monotonic_ns() - started > 10_000_000_000:
                raise HarnessError("DATABASE_SNAPSHOT_TIMEOUT")
        def logical_hash(connection):
            checksum = hashlib.sha256()
            for line in connection.iterdump():
                checksum.update(line.encode("utf-8") + b"\n")
            return checksum.hexdigest()
        source = sqlite3.connect(self.db.as_uri() + "?mode=ro", uri=True, timeout=10)
        target = None
        try:
            source.execute("PRAGMA query_only=ON")
            source.execute("BEGIN")
            source_hash = logical_hash(source)
            target = sqlite3.connect(temporary, timeout=10)
            source.backup(target, pages=64, progress=bounded_backup, sleep=0)
            if target.execute("PRAGMA journal_mode=DELETE").fetchone()[0].lower() != "delete":
                raise HarnessError("DATABASE_SNAPSHOT_JOURNAL_MODE")
            target.execute("PRAGMA synchronous=FULL")
            if target.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise HarnessError("DATABASE_SNAPSHOT_INVALID")
            if logical_hash(target) != source_hash:
                raise HarnessError("DATABASE_SNAPSHOT_MISMATCH")
            cursor = target.cursor()
            cursor.row_factory = sqlite3.Row
            state = {"metadata": {row["key"]: strict_loads(row["value"])
                                  for row in cursor.execute("SELECT * FROM metadata ORDER BY key")}}
            for table, ordering in (("routes", "route"), ("authorized_orders", "order_id"), ("orders", "order_id"),
                                    ("reservations", "key"), ("receipts", "key"), ("history", "sequence")):
                state[table] = [dict(row) for row in cursor.execute("SELECT * FROM " + table + " ORDER BY " + ordering)]
            for row in state["receipts"]:
                row["payload"] = strict_loads(row["payload"])
            for row in state["history"]:
                row["detail"] = strict_loads(row["detail"])
            if state != self.final_service_snapshot:
                raise HarnessError("DATABASE_STATE_CHANGED_DURING_FINALIZATION")
        finally:
            if target is not None:
                target.close()
            source.close()
        with open(temporary, "rb") as stream:
            os.fsync(stream.fileno())
        os.replace(temporary, self.evidence_db)
        for parent in (self.runtime_dir, self.evidence_dir):
            directory = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        for suffix in ("-wal", "-shm", "-journal"):
            if Path(str(self.evidence_db) + suffix).exists():
                raise HarnessError("DATABASE_SNAPSHOT_SIDECAR", suffix)
        self.event("DATABASE_EVIDENCE_FINALIZED", {"strategy": "SQLITE_BACKUP_AFTER_OWNED_WRITERS_EXIT",
                   "source": "runtime/service.sqlite", "evidence": "evidence/service.sqlite",
                   "journal_mode": "DELETE", "logical_snapshot_sha256": source_hash,
                   "preclose_state_sha256": digest(self.final_service_snapshot),
                   "file_sha256": hashlib.sha256(self.evidence_db.read_bytes()).hexdigest(),
                   "all_owned_processes_exited": True,
                   "worker_exits": [{"pid": child.process.pid, "exit_code": child.process.returncode,
                                     "expected_fault_exit": child.process.pid in self.expected_kills}
                                    for child in self.children]})

    def run(self):
        start_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        start_controller_usage = resource.getrusage(resource.RUSAGE_SELF)
        self.record["started_monotonic_ns"] = time.monotonic_ns()
        self.record["started_utc"] = datetime.now(timezone.utc).isoformat()
        ready_to_finalize = False
        try:
            if self.method == "ai":
                self.record["state"] = "NOT_RUN"
                self.record["target_verdict"] = "NOT_RUN"
                self.record["errors"].append({"code": "LOCAL_AI_UNAVAILABLE", "detail": "No authorized local model command was supplied; no API or model download was used."})
            else:
                self.initialize()
                self.execute_candidate()
                self.final_service_snapshot = self.require_ok(self.service.call("snapshot", {}))
                write_json(self.runtime_dir / "final-state.json", self.final_service_snapshot)
                self.event("DATABASE_STATE_CAPTURED", {"sha256": digest(self.final_service_snapshot),
                                                        "source": "runtime/final-state.json"})
                checkpoint = self.require_ok(self.service.call("checkpoint", {}))
                self.event("DATABASE_CHECKPOINT", checkpoint)
                if checkpoint.get("status") != "CHECKPOINTED" or checkpoint.get("sqlite") != [0, 0, 0]:
                    raise HarnessError("DATABASE_CHECKPOINT_INCOMPLETE", str(checkpoint))
                ready_to_finalize = True
        except (HarnessError, OSError, ValueError, KeyError, TypeError, sqlite3.Error, subprocess.SubprocessError) as error:
            self.record["state"] = "ERROR"
            self.record["target_verdict"] = "ERROR"
            self.record["errors"].append({"code": getattr(error, "code", "CONTROLLER_ERROR"), "detail": str(error)[:1000]})
            self.event("EXECUTION_ERROR", self.record["errors"][-1])
        finally:
            for child in self.children:
                try:
                    child.close()
                except (OSError, ValueError, subprocess.SubprocessError):
                    pass
            if ready_to_finalize:
                try:
                    unexpected = [child.process.pid for child in self.children
                                  if child.process.poll() != 0 and child.process.pid not in self.expected_kills]
                    if unexpected:
                        raise HarnessError("WORKER_EXIT_UNEXPECTED", str(unexpected))
                    self.finalize_database()
                    self.record["state"] = "COMPLETE"
                except (HarnessError, OSError, ValueError, sqlite3.Error) as error:
                    self.record["state"] = "ERROR"
                    self.record["target_verdict"] = "ERROR"
                    self.record["errors"].append({"code": getattr(error, "code", "DATABASE_FINALIZATION_ERROR"), "detail": str(error)[:1000]})
                    self.event("EXECUTION_ERROR", self.record["errors"][-1])
            self.record["finished_monotonic_ns"] = time.monotonic_ns()
            end_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
            end_controller_usage = resource.getrusage(resource.RUSAGE_SELF)
            self.record["resources"] = {
                "wall_ns": self.record["finished_monotonic_ns"] - self.record["started_monotonic_ns"],
                "cpu_user_ns": int((end_usage.ru_utime - start_usage.ru_utime) * 1_000_000_000),
                "cpu_system_ns": int((end_usage.ru_stime - start_usage.ru_stime) * 1_000_000_000),
                "controller_cpu_user_ns": int((end_controller_usage.ru_utime - start_controller_usage.ru_utime) * 1_000_000_000),
                "controller_cpu_system_ns": int((end_controller_usage.ru_stime - start_controller_usage.ru_stime) * 1_000_000_000),
                "peak_rss_bytes": None, "storage_bytes": sum(p.stat().st_size for p in self.run_dir.rglob("*") if p.is_file()),
                "requests": self.requests, "retries": self.retries, "worker_restarts": self.worker_restarts,
                "human_interventions": 0, "preparation_labor_seconds": None, "integration_labor_seconds": None,
                "monetary_cost": None}
            write_json(self.run_dir / "controller.json", self.record)
            manifest = {p.relative_to(self.run_dir).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in sorted(self.evidence_dir.rglob("*")) if p.is_file()}
            write_json(self.authority_dir / "execution.json", {"schema": "continuity-harness/execution-seal/v1",
                         "run_id": self.contract["run_id"], "contract_sha256": digest(self.contract),
                         "controller_sha256": digest(self.record), "evidence_manifest": manifest})
        return {"run_dir": str(self.run_dir), "authority_dir": str(self.authority_dir),
                "reference_sha256": self.reference_sha256, "controller": self.record}


def run_exercise(contract, method, run_dir, authority_dir, *, candidate_visible=None):
    return Controller(contract, method, run_dir, authority_dir, view=candidate_visible).run()
