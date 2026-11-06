"""Disposable local order and fulfillment service for CONTINUITY Harness 0.1.

This is a new implementation, not a modification or qualification of historical
``continuity_omega``. The service uses SQLite transactions and real durable JSON
artifacts. A receipt proves a local software transition, never printed goods.

The trusted controller initializes authorized obligations. Candidate processes
only reach this service through the controller's bounded JSON-lines broker.
The acceptance verifier reads the database/artifacts independently; it must not
import this module's replay or admission decisions as an oracle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import sys
import tempfile
import time


SCHEMA = "continuity-harness/service/v1"
ARTIFACT_SCHEMA = "continuity-harness/artifact/v1"
MAX_LINE = 1_048_576
MAX_ITEMS = 10_000
MAX_VALUE = 1_000_000_000
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
HEX_RE = re.compile(r"^[0-9a-f]{64}$")
ROUTES = {"primary", "backup"}
ORDER_FIELDS = {"order_id", "recipient", "product", "spec_sha256", "quantity", "deadline_tick"}
ACTIVE = ("RESERVED", "COMMITTED", "FULFILLED")
HOOKS = {
    "init.before_commit", "init.after_commit", "restore.before_commit", "restore.after_commit",
    "reserve.before_begin", "reserve.after_begin", "reserve.before_commit", "reserve.after_commit",
    "commit.before_commit", "commit.after_commit", "fulfill.before_commit", "fulfill.after_commit",
    "release.before_commit", "release.after_commit", "expire.before_commit", "expire.after_commit",
    "capacity.before_commit", "capacity.after_commit", "disable_route.before_commit", "disable_route.after_commit",
    "export.after_half_write", "export.after_temp", "export.after_replace",
}


class Refusal(ValueError):
    """A stable machine code plus complete explanations in both languages."""

    def __init__(self, code, en, fr):
        super().__init__(en)
        self.code = code
        self.detail = {"en": en, "fr": fr}


def refuse(code, en, fr):
    raise Refusal(code, en, fr)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            refuse("DUPLICATE_JSON_KEY", "Duplicate JSON key.", "Clé JSON en double.")
        result[key] = value
    return result


def decode(data):
    if len(data) > MAX_LINE:
        refuse("INPUT_TOO_LARGE", "The request exceeds the byte limit.", "La requête dépasse la limite en octets.")
    try:
        return json.loads(data, object_pairs_hook=_pairs,
                          parse_constant=lambda _: refuse("NONFINITE_VALUE", "Non-finite JSON number.", "Nombre JSON non fini."))
    except Refusal:
        raise
    except (ValueError, UnicodeError, RecursionError):
        refuse("MALFORMED_JSON", "Malformed JSON request.", "Requête JSON mal formée.")


def fields(value, required, optional=()):
    if type(value) is not dict:
        refuse("INVALID_STRUCTURE", "An object is required.", "Un objet est requis.")
    missing = set(required) - set(value)
    unknown = set(value) - set(required) - set(optional)
    if missing or unknown:
        refuse("INVALID_FIELDS", "Missing or unsupported fields: " + ", ".join(sorted(missing | unknown)),
               "Champs absents ou non pris en charge : " + ", ".join(sorted(missing | unknown)))


def integer(value, name, minimum=0, maximum=MAX_VALUE):
    if type(value) is not int or not minimum <= value <= maximum:
        refuse("INVALID_INTEGER", name + " must be an exact integer in range.",
               name + " doit être un entier exact dans la plage permise.")
    return value


def identifier(value, name):
    if type(value) is not str or not ID_RE.fullmatch(value):
        refuse("INVALID_IDENTIFIER", "Invalid identifier: " + name, "Identifiant invalide : " + name)
    return value


def hexadecimal(value, name):
    if type(value) is not str or not HEX_RE.fullmatch(value):
        refuse("INVALID_DIGEST", "Invalid SHA-256: " + name, "SHA-256 invalide : " + name)
    return value


def route_name(value):
    if type(value) is not str or value not in ROUTES:
        refuse("INVALID_ROUTE", "Unsupported route.", "Voie non prise en charge.")
    return value


def order_record(value):
    fields(value, ORDER_FIELDS)
    for key in ("order_id", "recipient", "product"):
        identifier(value[key], key)
    hexadecimal(value["spec_sha256"], "spec_sha256")
    integer(value["quantity"], "quantity", 1)
    integer(value["deadline_tick"], "deadline_tick", 1)
    return dict(value)


def order_list(value):
    if type(value) is not list or len(value) > MAX_ITEMS:
        refuse("INVALID_ORDERS", "A bounded order list is required.", "Une liste bornée de commandes est requise.")
    result = [order_record(item) for item in value]
    if len({row["order_id"] for row in result}) != len(result):
        refuse("DUPLICATE_ORDER", "Duplicate order identifier.", "Identifiant de commande en double.")
    return result


def replay_events(events, cutoff):
    """Service recovery implementation; the verifier has its own replay."""
    integer(cutoff, "cutoff", 1, MAX_ITEMS)
    if type(events) is not list or len(events) != cutoff:
        refuse("INCOMPLETE_SOURCE", "The journal does not cover the exact cutoff.",
               "Le journal ne couvre pas exactement le point de reprise.")
    state = {}
    for sequence, event in enumerate(events, 1):
        if type(event) is not dict:
            refuse("INVALID_EVENT", "Invalid journal event.", "Événement du journal invalide.")
        kind = event.get("type")
        base = {"sequence", "type", "order_id"}
        if kind == "ACCEPT":
            fields(event, base | (ORDER_FIELDS - {"order_id"}))
        elif kind == "AMEND":
            fields(event, base, ORDER_FIELDS - {"order_id"})
            if set(event) == base:
                refuse("EMPTY_AMENDMENT", "An amendment changes no field.", "Une modification ne change aucun champ.")
        elif kind == "CANCEL":
            fields(event, base)
        elif kind == "FULFILL":
            fields(event, base | {"quantity"})
        else:
            refuse("INVALID_EVENT_TYPE", "Unsupported event type.", "Type d’événement non pris en charge.")
        if integer(event["sequence"], "sequence", 1, MAX_ITEMS) != sequence:
            refuse("EVENT_SEQUENCE", "Journal sequence is missing, duplicated or reordered.",
                   "La séquence du journal est absente, répétée ou désordonnée.")
        oid = identifier(event["order_id"], "order_id")
        if kind == "ACCEPT":
            if oid in state:
                refuse("DUPLICATE_ACCEPTANCE", "Order accepted twice.", "Commande acceptée deux fois.")
            record = order_record({key: event[key] for key in ORDER_FIELDS})
            state[oid] = {**record, "fulfilled": 0, "state": "ACTIVE", "source_sequence": sequence}
            continue
        if oid not in state or state[oid]["state"] != "ACTIVE":
            refuse("INACTIVE_ORDER", "Event has no active accepted order.", "L’événement n’a aucune commande acceptée active.")
        record = state[oid]
        if kind == "CANCEL":
            record["state"] = "CANCELLED"
        elif kind == "FULFILL":
            quantity = integer(event["quantity"], "quantity", 1)
            if record["fulfilled"] + quantity > record["quantity"]:
                refuse("OVER_FULFILLMENT", "Historical fulfillment exceeds the order.", "La réalisation historique dépasse la commande.")
            record["fulfilled"] += quantity
            if record["fulfilled"] == record["quantity"]:
                record["state"] = "FULFILLED"
        else:
            proposed = {key: event.get(key, record[key]) for key in ORDER_FIELDS}
            order_record(proposed)
            if proposed["quantity"] < record["fulfilled"]:
                refuse("ERASED_FULFILLMENT", "Amendment erases completed work.", "La modification efface du travail réalisé.")
            record.update(proposed)
            if record["quantity"] == record["fulfilled"]:
                record["state"] = "FULFILLED"
        record["source_sequence"] = sequence
    return [state[key] for key in sorted(state)]


def outstanding(rows):
    return [{**{key: row[key] for key in ORDER_FIELDS}, "quantity": row["quantity"] - row["fulfilled"]}
            for row in rows if row["state"] == "ACTIVE" and row["quantity"] > row["fulfilled"]]


DDL = """
CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS routes (route TEXT PRIMARY KEY, capacity INTEGER NOT NULL CHECK(capacity>=0),
                                  available INTEGER NOT NULL CHECK(available IN (0,1)));
CREATE TABLE IF NOT EXISTS authorized_orders (
 order_id TEXT PRIMARY KEY, recipient TEXT NOT NULL, product TEXT NOT NULL, spec_sha256 TEXT NOT NULL,
 quantity INTEGER NOT NULL CHECK(quantity>0), deadline_tick INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS orders (
 order_id TEXT PRIMARY KEY, recipient TEXT NOT NULL, product TEXT NOT NULL, spec_sha256 TEXT NOT NULL,
 quantity INTEGER NOT NULL CHECK(quantity>0), fulfilled INTEGER NOT NULL DEFAULT 0,
 state TEXT NOT NULL, deadline_tick INTEGER NOT NULL, source_sequence INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS reservations (
 key TEXT PRIMARY KEY, run_id TEXT NOT NULL, contract_sha256 TEXT NOT NULL, order_id TEXT NOT NULL,
 recipient TEXT NOT NULL, product TEXT NOT NULL, spec_sha256 TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity>0),
 route TEXT NOT NULL REFERENCES routes(route), window_start INTEGER NOT NULL, window_end INTEGER NOT NULL,
 expires_tick INTEGER NOT NULL, status TEXT NOT NULL CHECK(status IN ('RESERVED','COMMITTED','FULFILLED','RELEASED','EXPIRED')),
 request_sha256 TEXT NOT NULL, created_tick INTEGER NOT NULL, updated_tick INTEGER NOT NULL,
 CHECK(window_start<window_end));
CREATE UNIQUE INDEX IF NOT EXISTS one_live_obligation ON reservations(order_id)
 WHERE status IN ('RESERVED','COMMITTED','FULFILLED');
CREATE TABLE IF NOT EXISTS receipts (
 key TEXT PRIMARY KEY REFERENCES reservations(key), order_id TEXT UNIQUE NOT NULL,
 payload TEXT NOT NULL, sha256 TEXT NOT NULL, completed_tick INTEGER NOT NULL, completed_monotonic_ns INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS history (
 sequence INTEGER PRIMARY KEY AUTOINCREMENT, operation TEXT NOT NULL, key TEXT, order_id TEXT, route TEXT,
 tick INTEGER NOT NULL, monotonic_ns INTEGER NOT NULL, detail TEXT NOT NULL);
"""


def checked_path(value):
    path = Path(value).absolute()
    for part in (path, *path.parents):
        if part.is_symlink():
            refuse("UNSAFE_PATH", "Symbolic links are not service paths.", "Les liens symboliques ne sont pas des chemins du service.")
    return path


class Service:
    def __init__(self, database, artifacts, hook=None):
        self.path = checked_path(database)
        self.artifacts = checked_path(artifacts)
        if self.path.exists() and not self.path.is_file():
            refuse("UNSAFE_PATH", "The database must be a regular file.", "La base doit être un fichier ordinaire.")
        if self.artifacts.exists() and not self.artifacts.is_dir():
            refuse("UNSAFE_PATH", "The artifact path must be a directory.", "Le chemin des pièces doit être un répertoire.")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.artifacts.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA busy_timeout=10000")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript(DDL)
        self.hook = hook or (lambda name: None)

    def close(self):
        self.db.close()

    def _meta(self, key, default=None):
        row = self.db.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def _set_meta(self, key, value):
        self.db.execute("INSERT INTO metadata VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                        (key, canonical(value).decode()))

    def _require_init(self):
        if self._meta("schema") != SCHEMA:
            refuse("NOT_INITIALIZED", "Service initialization is required.", "L’initialisation du service est requise.")

    def _history(self, operation, tick, row=None, detail=None):
        row = row or {}
        self.db.execute("INSERT INTO history(operation,key,order_id,route,tick,monotonic_ns,detail) VALUES (?,?,?,?,?,?,?)",
                        (operation, row.get("key"), row.get("order_id"), row.get("route"), tick, time.monotonic_ns(),
                         canonical(detail if detail is not None else {"reservation": dict(row)}).decode()))

    def _reservation(self, key):
        row = self.db.execute("SELECT * FROM reservations WHERE key=?", (key,)).fetchone()
        if row is None:
            refuse("RESERVATION_NOT_FOUND", "Reservation not found.", "Réservation introuvable.")
        return dict(row)

    def _result(self, key):
        row = self._reservation(key)
        result = {"key": key, "status": row["status"], "reservation": row}
        receipt = self.db.execute("SELECT * FROM receipts WHERE key=?", (key,)).fetchone()
        if receipt:
            result.update(receipt=json.loads(receipt["payload"]), artifact_sha256=receipt["sha256"],
                          artifact_path=receipt["order_id"] + ".json")
        return result

    def _advance(self, now):
        previous = self._meta("last_tick", 0)
        if now < previous:
            refuse("CLOCK_REGRESSION", "The trusted exercise clock moved backwards.", "L’horloge de l’exercice a reculé.")
        self._set_meta("last_tick", now)
        expired = []
        for old in self.db.execute("SELECT * FROM reservations WHERE status='RESERVED' AND expires_tick<=? ORDER BY key", (now,)).fetchall():
            self.db.execute("UPDATE reservations SET status='EXPIRED',updated_tick=? WHERE key=?", (now, old["key"]))
            row = self._reservation(old["key"])
            self._history("EXPIRED", now, row)
            expired.append(old["key"])
        return expired

    def _transaction(self, operation, function, now=None):
        self.hook(operation + ".before_begin")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.hook(operation + ".after_begin")
            if now is not None:
                self._advance(now)
            try:
                result = function()
            except Refusal:
                # All operation-specific checks precede their writes. The only
                # state here is the trusted clock/lease expiry, which remains
                # valid even when the requested business action is refused.
                self.db.commit()
                raise
            self.hook(operation + ".before_commit")
            self.db.commit()
        except BaseException:
            if self.db.in_transaction:
                self.db.rollback()
            raise
        self.hook(operation + ".after_commit")
        return result

    def _peak(self, route, now, extra=None):
        rows = [dict(row) for row in self.db.execute(
            "SELECT * FROM reservations WHERE route=? AND status IN ('RESERVED','COMMITTED','FULFILLED')", (route,))]
        if extra is not None:
            rows.append(extra)
        changes = []
        for row in rows:
            if row["window_end"] > now:
                changes.extend(((max(row["window_start"], now), row["quantity"]),
                                (row["window_end"], -row["quantity"])))
        load = peak = 0
        for _, delta in sorted(changes, key=lambda pair: (pair[0], pair[1])):
            load += delta
            peak = max(peak, load)
        return peak

    def _available(self, route):
        row = self.db.execute("SELECT * FROM routes WHERE route=?", (route,)).fetchone()
        if row is None or not row["available"]:
            refuse("ROUTE_UNAVAILABLE", "The route is withdrawn or unavailable.", "La voie est retirée ou indisponible.")
        return dict(row)

    def _primary_ready(self, authorized):
        row = self.db.execute("SELECT * FROM orders WHERE order_id=?", (authorized["order_id"],)).fetchone()
        if (self._meta("recovery_cutoff") is None or row is None or row["state"] != "ACTIVE"
                or row["quantity"] - row["fulfilled"] != authorized["quantity"]
                or any(row[field] != authorized[field] for field in ORDER_FIELDS - {"quantity"})
                or (self._meta("source_sha256") and self._meta("recovery_source_sha256") != self._meta("source_sha256"))):
            refuse("PRIMARY_NOT_RECOVERED", "The primary database has not reconstructed this authorized obligation.",
                   "La base primaire n’a pas reconstitué cette obligation autorisée.")

    def _export(self, key):
        row = self.db.execute("SELECT * FROM receipts WHERE key=?", (key,)).fetchone()
        if row is None:
            refuse("RECEIPT_NOT_FOUND", "No durable fulfillment receipt exists.", "Aucun reçu durable de réalisation n’existe.")
        target = checked_path(self.artifacts / (row["order_id"] + ".json"))
        data = row["payload"].encode("utf-8") + b"\n"
        if target.exists():
            if not target.is_file() or target.read_bytes() != data:
                refuse("ARTIFACT_CONFLICT", "Existing artifact differs; preserve it for inspection.",
                       "La pièce existante diffère ; elle est conservée pour inspection.")
            # An earlier worker may have died after rename but before directory
            # synchronization. A successful retry must re-establish both sync
            # boundaries before its reply is usable as a durability observation.
            with target.open("rb") as existing:
                os.fsync(existing.fileno())
            directory = os.open(self.artifacts, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
            return self._result(key)
        descriptor, temporary = tempfile.mkstemp(prefix="." + row["order_id"] + ".", suffix=".tmp", dir=self.artifacts)
        try:
            with os.fdopen(descriptor, "wb") as output:
                midpoint = len(data) // 2
                output.write(data[:midpoint])
                output.flush()
                self.hook("export.after_half_write")
                output.write(data[midpoint:])
                output.flush()
                os.fsync(output.fileno())
            self.hook("export.after_temp")
            os.replace(temporary, target)
            directory = os.open(self.artifacts, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
            self.hook("export.after_replace")
        finally:
            # A kill leaves a partial temporary file, never a favorable final
            # artifact. Reconciliation exports only the committed receipt.
            if os.path.exists(temporary):
                os.unlink(temporary)
        return self._result(key)

    def dispatch(self, operation, args):
        if type(operation) is not str:
            refuse("INVALID_OPERATION", "An operation name is required.", "Un nom d’opération est requis.")
        if operation == "ping":
            fields(args, set())
            return {"schema": SCHEMA, "pid": os.getpid(), "initialized": self._meta("schema") == SCHEMA}
        if operation == "init":
            fields(args, {"run_id", "contract_sha256", "capacities", "allowed_orders", "snapshot", "window_start", "window_end"}, {"source_sha256"})
            identifier(args["run_id"], "run_id")
            hexadecimal(args["contract_sha256"], "contract_sha256")
            if "source_sha256" in args:
                hexadecimal(args["source_sha256"], "source_sha256")
            fields(args["capacities"], ROUTES)
            for route, capacity in args["capacities"].items():
                integer(capacity, route + ".capacity")
            allowed = order_list(args["allowed_orders"])
            snapshot = order_list(args["snapshot"])
            start, end = integer(args["window_start"], "window_start"), integer(args["window_end"], "window_end", 1)
            if start >= end:
                refuse("INVALID_WINDOW", "Empty or reversed capacity window.", "Fenêtre de capacité vide ou inversée.")
            def initialize():
                previous = self._meta("init_sha256")
                if previous:
                    if previous != digest(args):
                        refuse("INIT_CONFLICT", "Initialization conflicts with retained state.", "L’initialisation contredit l’état conservé.")
                    return {"status": "ALREADY_INITIALIZED"}
                for key, value in {"schema": SCHEMA, "run_id": args["run_id"], "contract_sha256": args["contract_sha256"],
                                   "init_sha256": digest(args), "last_tick": 0, "window_start": start, "window_end": end,
                                   "source_sha256": args.get("source_sha256")}.items():
                    self._set_meta(key, value)
                self.db.executemany("INSERT INTO routes VALUES (?,?,1)", sorted(args["capacities"].items()))
                self.db.executemany("INSERT INTO authorized_orders VALUES (?,?,?,?,?,?)",
                    [(o["order_id"], o["recipient"], o["product"], o["spec_sha256"], o["quantity"], o["deadline_tick"]) for o in allowed])
                self.db.executemany("INSERT INTO orders VALUES (?,?,?,?,?,0,'ACTIVE',?,0)",
                    [(o["order_id"], o["recipient"], o["product"], o["spec_sha256"], o["quantity"], o["deadline_tick"]) for o in snapshot])
                self._history("INIT", 0, detail={"capacities": args["capacities"], "window_start": start, "window_end": end,
                                               "allowed_orders_sha256": digest(sorted(allowed, key=lambda o: o["order_id"]))})
                return {"status": "INITIALIZED"}
            return self._transaction("init", initialize)
        self._require_init()
        if operation == "restore":
            fields(args, {"events", "cutoff"})
            rows = replay_events(args["events"], args["cutoff"])
            recovered = outstanding(rows)
            def restore():
                self._available("primary")
                authorized = [dict(o) for o in self.db.execute("SELECT * FROM authorized_orders ORDER BY order_id")]
                if recovered != authorized or (self._meta("source_sha256") and digest(args["events"]) != self._meta("source_sha256")):
                    refuse("SOURCE_MISMATCH", "The journal does not match the authorized source or obligations.",
                           "Le journal ne correspond pas à la source ou aux obligations autorisées.")
                old = {o["order_id"]: dict(o) for o in self.db.execute("SELECT * FROM orders")}
                new = {o["order_id"]: o for o in rows}
                discrepancies = []
                for oid in sorted(set(old) | set(new)):
                    if oid not in old:
                        code = "MISSING_ORDER"
                    elif oid not in new:
                        code = "UNSUPPORTED_ORDER"
                    elif new[oid]["state"] == "CANCELLED" and old[oid]["state"] != "CANCELLED":
                        code = "RESURRECTED_CANCELLATION"
                    elif any(old[oid][key] != new[oid][key] for key in ORDER_FIELDS | {"fulfilled", "state"}):
                        code = "STALE_ORDER"
                    else:
                        continue
                    discrepancies.append({"order_id": oid, "code": code})
                self.db.execute("DELETE FROM orders")
                self.db.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?)",
                    [(o["order_id"], o["recipient"], o["product"], o["spec_sha256"], o["quantity"], o["fulfilled"], o["state"], o["deadline_tick"], o["source_sequence"]) for o in rows])
                self._set_meta("recovery_cutoff", args["cutoff"])
                self._set_meta("recovery_source_sha256", digest(args["events"]))
                self._history("RESTORED", self._meta("last_tick"), detail={"source_sha256": digest(args["events"]), "cutoff": args["cutoff"], "discrepancies": discrepancies})
                return {"status": "RESTORED", "orders": recovered, "all_orders": rows,
                        "discrepancies": discrepancies, "source_sha256": digest(args["events"]), "cutoff": args["cutoff"]}
            return self._transaction("restore", restore)
        if operation == "orders":
            fields(args, set())
            rows = [dict(row) for row in self.db.execute("SELECT * FROM orders ORDER BY order_id")]
            return {"orders": outstanding(rows), "all_orders": rows}
        if operation in {"disable_route", "withdraw"}:
            fields(args, {"route"}, {"now_tick"})
            route = route_name(args["route"])
            now = integer(args.get("now_tick", self._meta("last_tick")), "now_tick")
            def disable():
                self.db.execute("UPDATE routes SET available=0 WHERE route=?", (route,))
                self._history("ROUTE_DISABLED", now, {"route": route}, {"available": False})
                return {"status": "ROUTE_DISABLED", "route": route}
            return self._transaction("disable_route", disable, now)
        if operation == "reserve":
            required = {"run_id", "contract_sha256", "order_id", "recipient", "product", "spec_sha256", "quantity", "route", "key", "window_start", "window_end", "expires_tick", "now_tick"}
            fields(args, required)
            for key in ("run_id", "order_id", "recipient", "product", "key"):
                identifier(args[key], key)
            for key in ("contract_sha256", "spec_sha256"):
                hexadecimal(args[key], key)
            route = route_name(args["route"])
            for key in ("quantity", "window_end", "expires_tick"):
                integer(args[key], key, 1)
            for key in ("window_start", "now_tick"):
                integer(args[key], key)
            now = args["now_tick"]
            if args["window_start"] >= args["window_end"] or args["expires_tick"] > args["window_end"]:
                refuse("INVALID_WINDOW", "Invalid reservation or expiry window.", "Fenêtre de réservation ou d’expiration invalide.")
            request_hash = digest({key: value for key, value in args.items() if key != "now_tick"})
            def reserve():
                if args["run_id"] != self._meta("run_id") or args["contract_sha256"] != self._meta("contract_sha256"):
                    refuse("RUN_BINDING", "Request belongs to another contract or run.", "La requête appartient à un autre contrat ou exercice.")
                previous = self.db.execute("SELECT * FROM reservations WHERE key=?", (args["key"],)).fetchone()
                if previous:
                    if previous["request_sha256"] != request_hash:
                        refuse("IDEMPOTENCY_CONFLICT", "The key was already used for another request.", "La clé a déjà servi à une autre requête.")
                    return self._result(args["key"])
                if args["expires_tick"] <= now or args["window_end"] <= now:
                    refuse("RESERVATION_EXPIRED", "The reservation is already expired.", "La réservation a déjà expiré.")
                if args["window_start"] < self._meta("window_start") or args["window_end"] > self._meta("window_end"):
                    refuse("OUTSIDE_WINDOW", "Reservation exceeds the authorized window.", "La réservation dépasse la fenêtre autorisée.")
                authorized = self.db.execute("SELECT * FROM authorized_orders WHERE order_id=?", (args["order_id"],)).fetchone()
                if not authorized or any(args[field] != authorized[field] for field in ORDER_FIELDS - {"deadline_tick"}):
                    refuse("UNAUTHORIZED_OBLIGATION", "Request changes or invents an authorized obligation.",
                           "La requête modifie ou invente une obligation autorisée.")
                if now > authorized["deadline_tick"]:
                    refuse("DEADLINE_EXCEEDED", "The obligation deadline has passed.", "L’échéance de l’obligation est dépassée.")
                live = self.db.execute("SELECT key,status FROM reservations WHERE order_id=? AND status IN ('RESERVED','COMMITTED','FULFILLED')", (args["order_id"],)).fetchone()
                if live:
                    refuse("OBLIGATION_IN_FLIGHT" if live["status"] != "FULFILLED" else "ALREADY_FULFILLED",
                           "The obligation already has an active allocation or completed output.",
                           "L’obligation possède déjà une allocation active ou un résultat réalisé.")
                provider = self._available(route)
                if route == "primary":
                    self._primary_ready(authorized)
                if self._peak(route, now, args) > provider["capacity"]:
                    refuse("CAPACITY_EXCEEDED", "Insufficient simultaneous capacity.", "Capacité simultanée insuffisante.")
                row = {key: args[key] for key in required - {"now_tick"}}
                row.update(status="RESERVED", request_sha256=request_hash, created_tick=now, updated_tick=now)
                columns = list(row)
                self.db.execute("INSERT INTO reservations(" + ",".join(columns) + ") VALUES (" + ",".join("?" for _ in columns) + ")", tuple(row[key] for key in columns))
                self._history("RESERVED", now, self._reservation(args["key"]))
                return self._result(args["key"])
            return self._transaction("reserve", reserve, now)
        if operation in {"commit", "fulfill", "release"}:
            fields(args, {"key", "now_tick"})
            key = identifier(args["key"], "key")
            now = integer(args["now_tick"], "now_tick")
            def transition():
                row = self._reservation(key)
                if operation == "release":
                    if row["status"] == "FULFILLED":
                        refuse("FULFILLED_IMMUTABLE", "Completed work cannot release its consumed capacity.",
                               "Le travail réalisé ne peut libérer sa capacité consommée.")
                    if row["status"] in {"RELEASED", "EXPIRED"}:
                        return self._result(key)
                    status = "RELEASED"
                else:
                    if row["status"] == "FULFILLED" or (operation == "commit" and row["status"] == "COMMITTED"):
                        return self._result(key)
                    if row["status"] in {"EXPIRED", "RELEASED"}:
                        refuse("RESERVATION_" + row["status"], "Reservation is no longer active.", "La réservation n’est plus active.")
                    if operation == "fulfill" and row["status"] != "COMMITTED":
                        refuse("COMMIT_REQUIRED", "Commit the allocation before fulfillment.", "Engager l’allocation avant la réalisation.")
                    self._available(row["route"])
                    authorized = self.db.execute("SELECT * FROM authorized_orders WHERE order_id=?", (row["order_id"],)).fetchone()
                    deadline = authorized["deadline_tick"]
                    if row["route"] == "primary":
                        self._primary_ready(authorized)
                    if now > deadline or now > row["window_end"]:
                        refuse("DEADLINE_EXCEEDED", "Completion is beyond the frozen deadline or window.",
                               "La réalisation dépasse l’échéance ou la fenêtre figée.")
                    if operation == "fulfill" and now < row["window_start"]:
                        refuse("OUTSIDE_WINDOW", "Fulfillment is before the authorized window.", "La réalisation précède la fenêtre autorisée.")
                    status = "COMMITTED" if operation == "commit" else "FULFILLED"
                self.db.execute("UPDATE reservations SET status=?,updated_tick=? WHERE key=?", (status, now, key))
                updated = self._reservation(key)
                if operation == "fulfill":
                    artifact = {"schema": ARTIFACT_SCHEMA,
                                **{field: row[field] for field in ("run_id", "contract_sha256", "order_id", "recipient", "product", "spec_sha256", "quantity", "route", "key")},
                                "state": "COMPLETED", "completed_tick": now, "completed_monotonic_ns": time.monotonic_ns()}
                    artifact_bytes = canonical(artifact) + b"\n"
                    self.db.execute("INSERT INTO receipts VALUES (?,?,?,?,?,?)", (key, row["order_id"], canonical(artifact).decode(), hashlib.sha256(artifact_bytes).hexdigest(), now, artifact["completed_monotonic_ns"]))
                self._history(status, now, updated)
                return self._result(key)
            result = self._transaction(operation, transition, now)
            if operation == "fulfill":
                return self._export(key)
            return result
        if operation == "expire":
            fields(args, {"now_tick"})
            now = integer(args["now_tick"], "now_tick")
            def expire():
                return {"status": "EXPIRY_APPLIED", "now_tick": now,
                        "expired_keys": [r[0] for r in self.db.execute("SELECT key FROM reservations WHERE status='EXPIRED' ORDER BY key")]}
            return self._transaction("expire", expire, now)
        if operation == "capacity":
            fields(args, {"route", "new_capacity", "now_tick"})
            route = route_name(args["route"])
            capacity = integer(args["new_capacity"], "new_capacity")
            now = integer(args["now_tick"], "now_tick")
            def adjust():
                peak = self._peak(route, now)
                if capacity < peak:
                    refuse("CAPACITY_ENCUMBERED", "Capacity is already allocated; lowering it would overbook commitments.",
                           "La capacité est déjà allouée ; sa réduction surchargerait les engagements.")
                old = self.db.execute("SELECT capacity FROM routes WHERE route=?", (route,)).fetchone()[0]
                self.db.execute("UPDATE routes SET capacity=? WHERE route=?", (capacity, route))
                self._history("CAPACITY_CHANGED", now, {"route": route}, {"previous_capacity": old, "capacity": capacity})
                return {"status": "CAPACITY_CHANGED", "route": route, "capacity": capacity, "peak_allocated": peak}
            return self._transaction("capacity", adjust, now)
        if operation == "lookup":
            fields(args, {"key"})
            return self._result(identifier(args["key"], "key"))
        if operation == "reconcile":
            fields(args, set())
            exported = []
            conflicts = []
            for row in self.db.execute("SELECT key FROM receipts ORDER BY order_id").fetchall():
                try:
                    exported.append(self._export(row["key"]))
                except Refusal as exc:
                    conflicts.append({"key": row["key"], "code": exc.code, "detail": exc.detail})
            return {"status": "RECONCILED" if not conflicts else "RECONCILIATION_INCOMPLETE", "outputs": exported, "conflicts": conflicts}
        if operation == "snapshot":
            fields(args, set())
            self.db.execute("BEGIN")
            try:
                result = {"metadata": {r["key"]: json.loads(r["value"]) for r in self.db.execute("SELECT * FROM metadata ORDER BY key")}}
                for table, ordering in (("routes", "route"), ("authorized_orders", "order_id"), ("orders", "order_id"),
                                        ("reservations", "key"), ("receipts", "key"), ("history", "sequence")):
                    result[table] = [dict(r) for r in self.db.execute("SELECT * FROM " + table + " ORDER BY " + ordering)]
                for row in result["receipts"]:
                    row["payload"] = json.loads(row["payload"])
                for row in result["history"]:
                    row["detail"] = json.loads(row["detail"])
                self.db.commit()
                return result
            except BaseException:
                self.db.rollback()
                raise
        if operation == "checkpoint":
            fields(args, set())
            result = tuple(self.db.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone())
            if result[0] != 0:
                refuse("CHECKPOINT_BUSY", "The checkpoint is blocked by an active database connection; durable finalization is incomplete.",
                       "Un accès actif à la base bloque le point de contrôle ; la finalisation durable est incomplète.")
            return {"status": "CHECKPOINTED", "sqlite": list(result)}
        refuse("UNSUPPORTED_OPERATION", "Unsupported service operation.", "Opération du service non prise en charge.")


def emit(value):
    sys.stdout.buffer.write(canonical(value) + b"\n")
    sys.stdout.buffer.flush()


def serve(service):
    while True:
        raw = sys.stdin.buffer.readline(MAX_LINE + 1)
        if not raw:
            return
        request_id = None
        try:
            if len(raw) > MAX_LINE:
                refuse("INPUT_TOO_LARGE", "The request exceeds the byte limit.", "La requête dépasse la limite en octets.")
            request = decode(raw)
            fields(request, {"id", "op", "args"}, {"hooks"})
            request_id = request["id"]
            if type(request_id) is int:
                integer(request_id, "id")
            else:
                identifier(request_id, "id")
            requested_hooks = request.get("hooks", [])
            if type(requested_hooks) is not list or any(type(h) is not str or h not in HOOKS for h in requested_hooks) or len(requested_hooks) > len(HOOKS):
                refuse("INVALID_HOOK", "Unsupported transition hook.", "Point de transition non pris en charge.")
            def hook(name):
                if name in requested_hooks:
                    emit({"id": request_id, "event": "hook", "hook": name})
                    continuation = decode(sys.stdin.buffer.readline(MAX_LINE + 1))
                    if continuation != {"continue": True}:
                        raise OSError("HOOK_INTERRUPTED")
            service.hook = hook
            result = service.dispatch(request["op"], request["args"])
            emit({"id": request_id, "ok": True, "result": result})
        except Refusal as exc:
            emit({"id": request_id, "ok": False, "code": exc.code, "detail": exc.detail})
            if len(raw) > MAX_LINE:
                return
        except (OSError, sqlite3.Error, RecursionError, TypeError, KeyError, OverflowError) as exc:
            if service.db.in_transaction:
                service.db.rollback()
            emit({"id": request_id, "ok": False, "code": "SERVICE_ERROR",
                  "detail": {"en": "Service operation did not complete: " + type(exc).__name__,
                             "fr": "L’opération du service n’a pas abouti : " + type(exc).__name__}})


class Parser(argparse.ArgumentParser):
    def error(self, message):
        emit({"id": None, "ok": False, "code": "CLI_ARGUMENT",
              "detail": {"en": "Invalid service command arguments.", "fr": "Arguments de commande du service invalides."}})
        self.exit(2)


def main(argv=None):
    parser = Parser(description="Disposable local service / Service local jetable — CONTINUITY Ω / CONTINUITÉ Ω")
    parser.add_argument("--db", required=True, help="SQLite path / Chemin SQLite")
    parser.add_argument("--artifacts", required=True, help="Durable output directory / Répertoire des résultats durables")
    options = parser.parse_args(argv)
    service = None
    try:
        service = Service(options.db, options.artifacts)
        serve(service)
        return 0
    except Refusal as exc:
        emit({"id": None, "ok": False, "code": exc.code, "detail": exc.detail})
        return 2
    except (OSError, sqlite3.Error):
        emit({"id": None, "ok": False, "code": "SERVICE_START_FAILED",
              "detail": {"en": "The local service could not start.", "fr": "Le service local n’a pas pu démarrer."}})
        return 3
    finally:
        if service is not None:
            service.close()


if __name__ == "__main__":
    raise SystemExit(main())
