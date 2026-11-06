"""Materialize bounded digital label jobs in a disposable local process.

The content is a semantic JSON product, not a rendered or print-ready label.
Each production intent, generation, retry and exported byte string is retained.
The receiving service implements its own content checks and does not import this
module.  The trusted controller supplies authorization and capacity decisions.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import time

from continuity_harness.schema import (
    HarnessError, MAX_JSON_BYTES, canonical, digest, identifier, integer,
    object_fields, read_bytes, strict_loads, ERROR_MESSAGES,
)
from .schema import validate_contract

FORMAT = "continuity-economy/label-job/v1"
SCHEMA = "continuity-economy/producer/v1"
REQUEST_FIELDS = {"production_id", "arrangement_id", "provider_id", "delivery_id", "obligation_id",
                  "capacity_key", "lot_id", "attempt", "first_unit", "last_unit", "supersedes", "now_tick"}
DEFECTS = {"none", "wrong_content", "missing_unit", "duplicate_unit", "stale_revision",
           "wrong_recipient", "wrong_serial", "truncated", "corrupt"}
HOOKS = {"produce.after_intent", "produce.before_begin", "produce.after_begin",
         "produce.before_commit", "produce.after_commit", "produce.after_half_write",
         "produce.after_fsync", "produce.after_replace", "produce.after_observation"}
MESSAGES = {
    "PRODUCT_SIZE_LIMIT": ("An authorized digital lot exceeds the supported byte bound; no production state was created.", "Un lot numérique autorisé dépasse la limite d’octets prise en charge ; aucun état de production n’a été créé."),
    "CONTRACT_MISMATCH": ("The durable service belongs to a different retained contract.", "Le service durable appartient à un autre contrat conservé."),
    "UNSUPPORTED_PRODUCT": ("This digital product feature is unsupported.", "Cette fonction du produit numérique n’est pas prise en charge."),
    "UNKNOWN_OBLIGATION": ("The obligation is absent from the retained contract.", "L’obligation est absente du contrat conservé."),
    "CANCELLED_OBLIGATION": ("The retained obligation is cancelled.", "L’obligation conservée est annulée."),
    "IDEMPOTENCY_CONFLICT": ("The production identifier already binds different terms.", "L’identifiant de production est déjà lié à d’autres conditions."),
    "DELIVERY_ID_CONFLICT": ("The delivery identifier already belongs to another production.", "L’identifiant de remise appartient déjà à une autre production."),
    "PRODUCTION_BINDING_MISMATCH": ("Production, capacity and fixed-lot identities do not agree.", "Les identités de production, de capacité et de lot fixe ne concordent pas."),
    "INVALID_CORRECTION": ("Only the same arrangement and lot's rejected first delivery may be corrected as attempt two.", "Seule la première remise refusée de la même solution et du même lot peut être corrigée à la deuxième tentative."),
    "ARTIFACT_CONFLICT": ("An existing output has different bytes; it was not overwritten.", "Un résultat existant contient d’autres octets ; il n’a pas été écrasé."),
    "UNKNOWN_PRODUCTION": ("The requested production does not exist.", "La production demandée n’existe pas."),
    "DEADLINE_EXPIRED": ("The declared production deadline has expired.", "L’échéance de production déclarée est dépassée."),
    "INVALID_HOOK": ("The requested transition hook is unsupported.", "Le point de transition demandé n’est pas pris en charge."),
    "UNSUPPORTED_OPERATION": ("The production operation is unsupported.", "L’opération de production n’est pas prise en charge."),
    "CHECKPOINT_BUSY": ("Active database access prevents durable finalization.", "Un accès actif à la base empêche la finalisation durable."),
    "RESOURCE_LIMIT": ("The bounded production count has been reached.", "La limite du nombre de productions est atteinte."),
    "SERVICE_ERROR": ("The production operation did not complete.", "L’opération de production n’a pas abouti."),
    "SERVICE_START_FAILED": ("The production service could not start.", "Le service de production n’a pas pu démarrer."),
    "CLI_ARGUMENT": ("Invalid production service command arguments.", "Arguments de commande du service de production invalides."),
}


def fail(code, location=""):
    raise HarnessError(code, location)


def explanation(error):
    en, fr = MESSAGES.get(error.code, ERROR_MESSAGES.get(error.code, MESSAGES["SERVICE_ERROR"]))
    return {"code": error.code, "detail": {"en": en, "fr": fr}, "location": error.detail}


def checked_path(value):
    path = Path(value).absolute()
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        fail("UNSAFE_PATH", path.name)
    return path


def retained_contract(value):
    """Admit the full neutral contract before creating files or durable state.

    This schema validation contains no product generator or acceptance oracle.
    Copy the retained value so an in-process caller cannot later alter authority.
    """
    contract = strict_loads(read_bytes(value)) if isinstance(value, (str, Path)) else value
    return deepcopy(validate_contract(contract))


def generate_product(contract, obligation, request):
    """Producer-only materialization. Acceptance never calls this function."""
    spec = obligation["spec"]
    labels = []
    for ordinal in range(request["first_unit"], request["last_unit"] + 1):
        labels.append({"ordinal": ordinal, "serial": spec["serial_prefix"] + f"{ordinal:06d}",
                       "sku": spec["sku"], "name_en": spec["name_en"], "name_fr": spec["name_fr"],
                       "instructions_en": spec["instructions_en"], "instructions_fr": spec["instructions_fr"],
                       "lot": spec["lot"]})
    product = {"schema": FORMAT, "run_id": contract["run_id"], "contract_id": contract["contract_id"],
               "contract_sha256": digest(contract), "obligation_id": obligation["obligation_id"],
               "revision": obligation["revision"], "recipient": obligation["recipient"],
               **{key: request[key] for key in ("production_id", "arrangement_id", "provider_id", "delivery_id",
                                               "capacity_key", "lot_id", "attempt",
                                               "first_unit", "last_unit", "supersedes")}, "labels": labels}
    defect = request.get("defect", "none")
    if defect == "wrong_content":
        labels[0]["instructions_en"] = "Incorrect handling instruction."
    elif defect == "missing_unit":
        labels.pop()
    elif defect == "duplicate_unit":
        labels.append(dict(labels[0]))
    elif defect == "stale_revision":
        product["revision"] = max(0, obligation["revision"] - 1)
    elif defect == "wrong_recipient":
        product["recipient"] = "UNAUTHORIZED-RECIPIENT"
    elif defect == "wrong_serial":
        labels[0]["serial"] += "-WRONG"
    raw = canonical(product)
    if defect == "truncated":
        raw = raw[:max(1, len(raw) // 2)]
    elif defect == "corrupt":
        raw = b"{invalid-digital-product"
    return raw, len(labels)


class Producer:
    def __init__(self, database, artifacts, contract):
        self.contract = retained_contract(contract)
        self.contract_sha256 = digest(self.contract)
        self.obligations = {o["obligation_id"]: o for o in self.contract["obligations"]}
        self.artifacts = checked_path(artifacts)
        self.database = checked_path(database)
        self.artifacts.mkdir(parents=True, exist_ok=True)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.database, timeout=10, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA busy_timeout=10000")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS productions(
              production_id TEXT PRIMARY KEY,request_sha256 TEXT NOT NULL,request_json TEXT NOT NULL,
              arrangement_id TEXT NOT NULL,provider_id TEXT NOT NULL,delivery_id TEXT NOT NULL UNIQUE,
              capacity_key TEXT NOT NULL UNIQUE,lot_id TEXT NOT NULL,attempt INTEGER NOT NULL,
              obligation_id TEXT NOT NULL,first_unit INTEGER NOT NULL,last_unit INTEGER NOT NULL,
              quantity INTEGER NOT NULL,supersedes TEXT,defect TEXT NOT NULL,
              started_tick INTEGER NOT NULL,started_ns INTEGER NOT NULL,
              artifact_name TEXT NOT NULL,payload_sha256 TEXT,byte_count INTEGER,
              generated_units INTEGER,payload BLOB,status TEXT NOT NULL,
              UNIQUE(arrangement_id,obligation_id,first_unit,last_unit,attempt));
            CREATE TABLE IF NOT EXISTS attempts(
              sequence INTEGER PRIMARY KEY AUTOINCREMENT,production_id TEXT NOT NULL,
              requested_tick INTEGER NOT NULL,requested_ns INTEGER NOT NULL,kind TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS observations(
              production_id TEXT PRIMARY KEY,completed_tick INTEGER NOT NULL,completed_ns INTEGER NOT NULL,
              payload_sha256 TEXT NOT NULL,byte_count INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS events(
              sequence INTEGER PRIMARY KEY AUTOINCREMENT,event TEXT NOT NULL,production_id TEXT,
              tick INTEGER NOT NULL,observed_ns INTEGER NOT NULL,detail TEXT NOT NULL);
        """)
        self.hook = lambda name: None
        existing = self.db.execute("SELECT value FROM metadata WHERE key='contract_sha256'").fetchone()
        if existing and strict_loads(existing[0]) != self.contract_sha256:
            self.db.close()
            fail("CONTRACT_MISMATCH")
        if not existing:
            self.db.execute("BEGIN IMMEDIATE")
            for key, value in {"schema": SCHEMA, "run_id": self.contract["run_id"], "contract_sha256": self.contract_sha256}.items():
                self.db.execute("INSERT INTO metadata VALUES(?,?)", (key, canonical(value).decode()))
            self.db.commit()

    def close(self):
        self.db.close()

    def event(self, event, production_id, tick, detail):
        self.db.execute("INSERT INTO events(event,production_id,tick,observed_ns,detail) VALUES(?,?,?,?,?)",
                        (event, production_id, tick, time.monotonic_ns(), canonical(detail).decode()))

    def request(self, args):
        object_fields(args, REQUEST_FIELDS, {"defect"}, path="produce")
        request = dict(args)
        for key in ("production_id", "arrangement_id", "provider_id", "delivery_id", "obligation_id", "capacity_key", "lot_id"):
            identifier(request[key], "produce." + key)
        if request["supersedes"] is not None:
            identifier(request["supersedes"], "produce.supersedes")
            if request["supersedes"] == request["delivery_id"]:
                fail("IDEMPOTENCY_CONFLICT", "self correction")
        integer(request["now_tick"], "produce.now_tick", 0, 1_000_000_000)
        obligation = self.obligations.get(request["obligation_id"])
        if obligation is None:
            fail("UNKNOWN_OBLIGATION", request["obligation_id"])
        if obligation["status"] != "ACTIVE":
            fail("CANCELLED_OBLIGATION", request["obligation_id"])
        integer(request["first_unit"], "produce.first_unit", 1, obligation["quantity"])
        integer(request["last_unit"], "produce.last_unit", request["first_unit"], obligation["quantity"])
        integer(request["attempt"], "produce.attempt", 1, self.contract["max_attempts"])
        lot_size = self.contract["lot_size"] if self.contract["allow_split"] else obligation["quantity"]
        index = (request["first_unit"] - 1) // lot_size + 1
        lot_id = request["obligation_id"] + f".L{index:03d}"
        key = request["arrangement_id"] + "." + lot_id + ".A" + str(request["attempt"])
        if (request["first_unit"] != (index - 1) * lot_size + 1 or
                request["last_unit"] != min(index * lot_size, obligation["quantity"]) or
                request["lot_id"] != lot_id or request["capacity_key"] != key or
                request["production_id"] != key or request["delivery_id"] != key + ".D"):
            fail("PRODUCTION_BINDING_MISMATCH", request["production_id"])
        predecessor = request["arrangement_id"] + "." + lot_id + ".A1.D"
        if (request["attempt"] == 1 and request["supersedes"] is not None) or \
                (request["attempt"] == 2 and request["supersedes"] != predecessor):
            fail("INVALID_CORRECTION", request["production_id"])
        request["defect"] = request.get("defect", "none")
        if type(request["defect"]) is not str or request["defect"] not in DEFECTS:
            fail("UNSUPPORTED_PRODUCT", "produce.defect")
        return request, obligation

    def produce(self, args):
        request, obligation = self.request(args)
        pid, tick = request["production_id"], request["now_tick"]
        terms = {k: v for k, v in request.items() if k != "now_tick"}
        fingerprint = digest(terms)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            old = self.db.execute("SELECT * FROM productions WHERE production_id=?", (pid,)).fetchone()
            if old and old["request_sha256"] != fingerprint:
                fail("IDEMPOTENCY_CONFLICT", pid)
            other = self.db.execute("SELECT production_id FROM productions WHERE delivery_id=?", (request["delivery_id"],)).fetchone()
            if other and other[0] != pid:
                fail("DELIVERY_ID_CONFLICT", request["delivery_id"])
            if not old:
                if tick > obligation["deadline_tick"]:
                    fail("DEADLINE_EXPIRED", pid)
                if self.db.execute("SELECT count(*) FROM productions").fetchone()[0] >= 256:
                    fail("RESOURCE_LIMIT", "productions")
                self.db.execute("""INSERT INTO productions(
                    production_id,request_sha256,request_json,arrangement_id,provider_id,delivery_id,capacity_key,lot_id,attempt,
                    obligation_id,first_unit,last_unit,quantity,supersedes,defect,started_tick,started_ns,artifact_name,status)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (pid, fingerprint, canonical(terms).decode(), request["arrangement_id"], request["provider_id"],
                     request["delivery_id"], request["capacity_key"], request["lot_id"], request["attempt"],
                     request["obligation_id"], request["first_unit"], request["last_unit"],
                     request["last_unit"] - request["first_unit"] + 1, request["supersedes"], request["defect"],
                     tick, time.monotonic_ns(), pid + ".json", "STARTED"))
                self.event("PRODUCTION_INTENT", pid, tick, {"quantity": request["last_unit"] - request["first_unit"] + 1})
            kind = "REPLAY" if old and old["payload"] is not None else "GENERATION_REQUEST"
            self.db.execute("INSERT INTO attempts(production_id,requested_tick,requested_ns,kind) VALUES(?,?,?,?)",
                            (pid, tick, time.monotonic_ns(), kind))
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise
        self.hook("produce.after_intent")
        self.hook("produce.before_begin")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.hook("produce.after_begin")
            row = self.db.execute("SELECT * FROM productions WHERE production_id=?", (pid,)).fetchone()
            if row["payload"] is None:
                raw, generated = generate_product(self.contract, obligation, request)
                sha = hashlib.sha256(raw).hexdigest()
                self.db.execute("UPDATE productions SET payload=?,payload_sha256=?,byte_count=?,generated_units=?,status='GENERATED' WHERE production_id=?",
                                (raw, sha, len(raw), generated, pid))
                self.event("CONTENT_GENERATED", pid, tick, {"generated_units": generated, "bytes": len(raw), "sha256": sha})
            self.hook("produce.before_commit")
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise
        self.hook("produce.after_commit")
        row = self.db.execute("SELECT * FROM productions WHERE production_id=?", (pid,)).fetchone()
        self.export(row, tick)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            observed = self.db.execute("SELECT * FROM observations WHERE production_id=?", (pid,)).fetchone()
            if observed is None:
                self.db.execute("INSERT INTO observations VALUES(?,?,?,?,?)",
                                (pid, tick, time.monotonic_ns(), row["payload_sha256"], row["byte_count"]))
                self.db.execute("UPDATE productions SET status='MATERIALIZED' WHERE production_id=?", (pid,))
                self.event("PRODUCTION_MATERIALIZED", pid, tick, {"sha256": row["payload_sha256"]})
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise
        self.hook("produce.after_observation")
        return self.status(pid)

    def export(self, row, tick):
        destination = self.artifacts / row["artifact_name"]
        raw = bytes(row["payload"])
        if destination.exists() or destination.is_symlink():
            if read_bytes(destination) != raw:
                fail("ARTIFACT_CONFLICT", row["artifact_name"])
            self.event("EXPORT_RECONCILED", row["production_id"], tick, {"bytes": len(raw)})
            return
        fd, temporary = tempfile.mkstemp(prefix="." + row["production_id"] + ".", suffix=".part", dir=self.artifacts)
        # Interrupted temporary files are deliberately retained as evidence.
        with os.fdopen(fd, "wb", buffering=0) as stream:
            half = max(1, len(raw) // 2)
            stream.write(raw[:half])
            self.hook("produce.after_half_write")
            stream.write(raw[half:])
            os.fsync(stream.fileno())
            self.hook("produce.after_fsync")
        try:
            os.link(temporary, destination)
        except FileExistsError:
            if read_bytes(destination) != raw:
                fail("ARTIFACT_CONFLICT", row["artifact_name"])
        os.unlink(temporary)
        directory = os.open(self.artifacts, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        self.hook("produce.after_replace")
        self.event("EXPORTED", row["production_id"], tick, {"artifact_name": row["artifact_name"], "bytes": len(raw)})

    def status(self, production_id):
        identifier(production_id, "production_id")
        row = self.db.execute("SELECT * FROM productions WHERE production_id=?", (production_id,)).fetchone()
        if row is None:
            fail("UNKNOWN_PRODUCTION", production_id)
        result = {k: row[k] for k in row.keys() if k not in ("payload", "request_json")}
        observation = self.db.execute("SELECT * FROM observations WHERE production_id=?", (production_id,)).fetchone()
        result["observation"] = dict(observation) if observation else None
        result["request_count"] = self.db.execute("SELECT count(*) FROM attempts WHERE production_id=?", (production_id,)).fetchone()[0]
        return result

    def snapshot(self):
        return {"schema": SCHEMA, "contract_sha256": self.contract_sha256,
                "productions": [self.status(row[0]) for row in self.db.execute("SELECT production_id FROM productions ORDER BY production_id")],
                "attempts": [dict(row) for row in self.db.execute("SELECT * FROM attempts ORDER BY sequence")],
                "event_count": self.db.execute("SELECT count(*) FROM events").fetchone()[0],
                "generated_units": self.db.execute("SELECT coalesce(sum(generated_units),0) FROM productions").fetchone()[0]}

    def dispatch(self, operation, args):
        if operation == "produce":
            return self.produce(args)
        if operation == "status":
            object_fields(args, {"production_id"}, path="status")
            return self.status(args["production_id"])
        if operation == "snapshot":
            object_fields(args, set(), path="snapshot")
            return self.snapshot()
        if operation == "checkpoint":
            object_fields(args, set(), path="checkpoint")
            result = list(self.db.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone())
            if result != [0, 0, 0]:
                fail("CHECKPOINT_BUSY")
            return {"status": "CHECKPOINTED", "sqlite": result}
        fail("UNSUPPORTED_OPERATION", str(operation))


def emit(value):
    sys.stdout.buffer.write(canonical(value) + b"\n")
    sys.stdout.buffer.flush()


def serve(service):
    while True:
        raw = sys.stdin.buffer.readline(MAX_JSON_BYTES + 1)
        if not raw:
            return
        request_id = None
        try:
            frame = strict_loads(raw)
            object_fields(frame, {"id", "op", "args"}, {"hooks"}, path="rpc")
            request_id = frame["id"]
            identifier(request_id, "rpc.id")
            identifier(frame["op"], "rpc.op")
            hooks = frame.get("hooks", [])
            if type(hooks) is not list or len(hooks) > len(HOOKS) or any(type(h) is not str or h not in HOOKS for h in hooks):
                fail("INVALID_HOOK")
            def hook(name):
                if name in hooks:
                    emit({"id": request_id, "event": "hook", "hook": name})
                    if strict_loads(sys.stdin.buffer.readline(MAX_JSON_BYTES + 1)) != {"continue": True}:
                        raise OSError("HOOK_INTERRUPTED")
            service.hook = hook
            emit({"id": request_id, "ok": True, "result": service.dispatch(frame["op"], frame["args"])})
        except HarnessError as error:
            if service.db.in_transaction:
                service.db.rollback()
            emit({"id": request_id, "ok": False, **explanation(error)})
            if len(raw) > MAX_JSON_BYTES:
                return
        except (OSError, sqlite3.Error, ValueError, TypeError, KeyError, OverflowError, RecursionError) as error:
            if service.db.in_transaction:
                service.db.rollback()
            emit({"id": request_id, "ok": False, **explanation(HarnessError("SERVICE_ERROR", type(error).__name__))})


class Parser(argparse.ArgumentParser):
    def error(self, message):
        emit({"id": None, "ok": False, **explanation(HarnessError("CLI_ARGUMENT"))})
        self.exit(2)


def main(argv=None):
    parser = Parser(description="Digital label production / Production de lots d’étiquettes numériques", add_help=False)
    parser.add_argument("-h", "--help", action="help",
                        help="Show complete help and exit / Afficher l’aide complète et quitter")
    parser.add_argument("--db", required=True, help="SQLite path / Chemin SQLite")
    parser.add_argument("--artifacts", required=True, help="Output directory / Répertoire des résultats")
    parser.add_argument("--contract", required=True, help="Retained contract / Contrat conservé")
    options = parser.parse_args(argv)
    service = None
    try:
        service = Producer(options.db, options.artifacts, options.contract)
        serve(service)
        return 0
    except HarnessError as error:
        emit({"id": None, "ok": False, **explanation(error)})
        return 2
    except (OSError, sqlite3.Error):
        emit({"id": None, "ok": False, **explanation(HarnessError("SERVICE_START_FAILED"))})
        return 3
    finally:
        if service is not None:
            service.close()


if __name__ == "__main__":
    raise SystemExit(main())
