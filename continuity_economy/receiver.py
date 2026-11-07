"""Independent semantic importer and durable recipient acceptance service.

The receiver retains its own contract, received byte strings, decisions, imported
unit content and post-commit observations.  It never imports the producer's
generation or decision functions.  Acceptance establishes the bounded digital
content contract only, not rendered appearance, printing or physical delivery.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import re
import sqlite3
import sys
import time

from continuity_harness.schema import (
    HarnessError, MAX_JSON_BYTES, canonical, digest, identifier, integer,
    object_fields, read_bytes, sha256, strict_loads, ERROR_MESSAGES,
)
from .schema import validate_contract

FORMAT = "continuity-economy/label-job/v1"
SCHEMA = "continuity-economy/receiver/v1"
PRODUCT_FIELDS = {"schema", "run_id", "contract_id", "contract_sha256", "obligation_id", "revision", "recipient",
                  "production_id", "arrangement_id", "provider_id", "delivery_id", "capacity_key", "lot_id",
                  "attempt", "first_unit", "last_unit", "supersedes", "labels"}
LABEL_FIELDS = {"ordinal", "serial", "sku", "name_en", "name_fr", "instructions_en", "instructions_fr", "lot"}
LITERAL_FIELDS = ("sku", "name_en", "name_fr", "instructions_en", "instructions_fr", "lot")
HOOKS = {"receive.before_commit", "receive.after_commit", "inspect.before_begin", "inspect.after_begin",
         "inspect.before_commit", "inspect.after_commit", "inspect.before_observation", "inspect.after_observation"}
MESSAGES = {
    "PRODUCT_SIZE_LIMIT": ("An authorized digital lot exceeds the supported byte bound; no receiving state was created.", "Un lot numérique autorisé dépasse la limite d’octets prise en charge ; aucun état de réception n’a été créé."),
    "CONTRACT_MISMATCH": ("The durable receiver belongs to another retained contract.", "Le destinataire durable appartient à un autre contrat conservé."),
    "UNSUPPORTED_PRODUCT": ("This digital product format or feature is unsupported.", "Ce format ou cette fonction de produit numérique n’est pas pris en charge."),
    "UNKNOWN_OBLIGATION": ("The obligation is absent from the retained contract.", "L’obligation est absente du contrat conservé."),
    "UNKNOWN_DELIVERY": ("The receiver has not received this delivery.", "Le destinataire n’a pas reçu cette remise."),
    "DELIVERY_ID_MISMATCH": ("The product belongs to a different delivery.", "Le produit appartient à une autre remise."),
    "DELIVERY_BINDING_MISMATCH": ("Delivery, production, capacity and fixed-lot identities do not agree.", "Les identités de remise, de production, de capacité et de lot fixe ne concordent pas."),
    "IDEMPOTENCY_CONFLICT": ("This delivery identifier already binds different received bytes or an obligation.", "Cet identifiant de remise est déjà lié à d’autres octets reçus ou à une autre obligation."),
    "WRONG_RUN": ("The received product belongs to another exercise.", "Le produit reçu appartient à un autre exercice."),
    "WRONG_CONTRACT": ("The received product does not bind the retained contract.", "Le produit reçu n’est pas lié au contrat conservé."),
    "WRONG_OBLIGATION": ("The received product names a different obligation.", "Le produit reçu désigne une autre obligation."),
    "WRONG_RECIPIENT": ("The received product names a different recipient.", "Le produit reçu désigne un autre destinataire."),
    "STALE_REVISION": ("The received product does not use the retained final revision.", "Le produit reçu n’utilise pas la révision finale conservée."),
    "CANCELLED_OBLIGATION": ("A cancelled obligation cannot be accepted.", "Une obligation annulée ne peut pas être acceptée."),
    "SOURCE_NOT_ESTABLISHED": ("Required source completeness has not been established.", "L’exhaustivité requise des sources n’est pas établie."),
    "UNIT_COVERAGE_MISMATCH": ("The product does not contain exactly the declared fixed-lot units.", "Le produit ne contient pas exactement les unités du lot fixe déclaré."),
    "DUPLICATE_UNITS": ("The received product contains duplicate units.", "Le produit reçu contient des unités en double."),
    "CONTENT_MISMATCH": ("The substantive label content differs from the retained specification.", "Le contenu substantiel des étiquettes diffère de la spécification conservée."),
    "SERIAL_MISMATCH": ("A unit serial differs from the retained serial convention.", "Le numéro de série d’une unité diffère de la convention conservée."),
    "DUPLICATE_FULFILLMENT": ("Some units have already been accepted; no duplicate units were imported.", "Certaines unités sont déjà acceptées ; aucune unité en double n’a été importée."),
    "CORRECTION_HISTORY_REQUIRED": ("A correction must identify the previous rejected delivery.", "Une correction doit désigner la remise refusée précédente."),
    "INVALID_CORRECTION": ("The correction does not follow a rejected delivery of the same obligation and range.", "La correction ne suit pas une remise refusée de la même obligation et de la même plage."),
    "CORRECTION_BRANCH_CONFLICT": ("The rejected delivery already has a correction attempt.", "La remise refusée possède déjà une tentative de correction."),
    "ATTEMPT_LIMIT": ("The retained correction-attempt limit has been reached.", "La limite conservée des tentatives de correction est atteinte."),
    "DEADLINE_EXPIRED": ("Recipient inspection occurred after the declared deadline.", "L’inspection par le destinataire a eu lieu après l’échéance déclarée."),
    "ACCEPTED": ("The receiver imported and accepted the specified digital content.", "Le destinataire a importé et accepté le contenu numérique spécifié."),
    "RECEIVED": ("The receiver retained the actual delivered bytes for inspection.", "Le destinataire a conservé les octets réellement remis pour inspection."),
    "INVALID_HOOK": ("The requested transition hook is unsupported.", "Le point de transition demandé n’est pas pris en charge."),
    "UNSUPPORTED_OPERATION": ("The receiving operation is unsupported.", "L’opération de réception n’est pas prise en charge."),
    "CHECKPOINT_BUSY": ("Active database access prevents durable finalization.", "Un accès actif à la base empêche la finalisation durable."),
    "RESOURCE_LIMIT": ("The bounded delivery count has been reached.", "La limite du nombre de remises est atteinte."),
    "SERVICE_ERROR": ("The receiving operation did not complete.", "L’opération de réception n’a pas abouti."),
    "SERVICE_START_FAILED": ("The receiving service could not start.", "Le service de réception n’a pas pu démarrer."),
    "CLI_ARGUMENT": ("Invalid receiving service command arguments.", "Arguments de commande du service de réception invalides."),
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


def text_value(value, location, maximum=160):
    if type(value) is not str or not 1 <= len(value) <= maximum or any(ord(c) < 32 for c in value):
        fail("INVALID_TYPE", location)
    canonical(value)
    return value


def retained_contract(value):
    """Admit the complete neutral schema before creating receiving state.

    Content acceptance remains separately implemented below. Neutral contract
    validation is shared, never the producer's generator or decision function.
    """
    contract = strict_loads(read_bytes(value)) if isinstance(value, (str, Path)) else value
    return deepcopy(validate_contract(contract))


class Receiver:
    def __init__(self, database, inbox, contract):
        self.contract = retained_contract(contract)
        self.contract_sha256 = digest(self.contract)
        self.obligations = {o["obligation_id"]: o for o in self.contract["obligations"]}
        self.database, self.inbox = checked_path(database), checked_path(inbox)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.database, timeout=10, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA busy_timeout=10000")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS receipts(
              delivery_id TEXT PRIMARY KEY,obligation_id TEXT NOT NULL,artifact_name TEXT NOT NULL,
              first_unit INTEGER NOT NULL,last_unit INTEGER NOT NULL,
              content_sha256 TEXT NOT NULL,byte_count INTEGER NOT NULL,
              received_tick INTEGER NOT NULL,received_ns INTEGER NOT NULL,raw BLOB NOT NULL);
            CREATE TABLE IF NOT EXISTS decisions(
              delivery_id TEXT PRIMARY KEY,obligation_id TEXT NOT NULL,decision TEXT NOT NULL,code TEXT NOT NULL,
              inspected_tick INTEGER NOT NULL,inspected_ns INTEGER NOT NULL,content_sha256 TEXT NOT NULL,
              revision INTEGER,recipient TEXT,first_unit INTEGER NOT NULL,last_unit INTEGER NOT NULL,
              quantity INTEGER NOT NULL,supersedes TEXT);
            CREATE TABLE IF NOT EXISTS observations(
              delivery_id TEXT PRIMARY KEY,decision TEXT NOT NULL,content_sha256 TEXT NOT NULL,
              observed_tick INTEGER NOT NULL,observed_ns INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS imported_units(
              obligation_id TEXT NOT NULL,ordinal INTEGER NOT NULL,delivery_id TEXT NOT NULL,
              serial TEXT NOT NULL,sku TEXT NOT NULL,name_en TEXT NOT NULL,name_fr TEXT NOT NULL,
              instructions_en TEXT NOT NULL,instructions_fr TEXT NOT NULL,lot TEXT NOT NULL,
              PRIMARY KEY(obligation_id,ordinal));
            CREATE TABLE IF NOT EXISTS events(
              sequence INTEGER PRIMARY KEY AUTOINCREMENT,event TEXT NOT NULL,delivery_id TEXT,
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

    def event(self, event, delivery_id, tick, detail):
        self.db.execute("INSERT INTO events(event,delivery_id,tick,observed_ns,detail) VALUES(?,?,?,?,?)",
                        (event, delivery_id, tick, time.monotonic_ns(), canonical(detail).decode()))

    def delivery_binding(self, delivery_id, obligation_id):
        """Derive the fixed range from the trusted transport identity, not JSON claims."""
        identifier(delivery_id, "delivery_id")
        identifier(obligation_id, "obligation_id")
        obligation = self.obligations.get(obligation_id)
        if obligation is None:
            fail("UNKNOWN_OBLIGATION", obligation_id)
        match = re.fullmatch(r"(.+)\." + re.escape(obligation_id) + r"\.L([0-9]{3})\.A([0-9]+)\.D", delivery_id)
        if match is None:
            fail("DELIVERY_BINDING_MISMATCH", delivery_id)
        arrangement_id, number, attempt = match.group(1), int(match.group(2)), int(match.group(3))
        identifier(arrangement_id, "arrangement_id")
        integer(attempt, "attempt", 1, self.contract["max_attempts"])
        lot_size = self.contract["lot_size"] if self.contract["allow_split"] else obligation["quantity"]
        first, last = (number - 1) * lot_size + 1, min(number * lot_size, obligation["quantity"])
        if number < 1 or first > last:
            fail("DELIVERY_BINDING_MISMATCH", delivery_id)
        lot_id = obligation_id + ".L" + str(number).zfill(3)
        capacity_key = arrangement_id + "." + lot_id + ".A" + str(attempt)
        if delivery_id != capacity_key + ".D":
            fail("DELIVERY_BINDING_MISMATCH", delivery_id)
        return {"arrangement_id": arrangement_id, "lot_id": lot_id, "attempt": attempt,
                "production_id": capacity_key, "capacity_key": capacity_key, "delivery_id": delivery_id,
                "first_unit": first, "last_unit": last}

    def receive(self, args):
        object_fields(args, {"delivery_id", "obligation_id", "now_tick"}, path="receive")
        tick = integer(args["now_tick"], "receive.now_tick", 0, 1_000_000_000)
        binding = self.delivery_binding(args["delivery_id"], args["obligation_id"])
        did = args["delivery_id"]
        filename = did + ".json"
        raw = read_bytes(self.inbox / filename)
        content_sha = hashlib.sha256(raw).hexdigest()
        received_ns = time.monotonic_ns()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            old = self.db.execute("SELECT * FROM receipts WHERE delivery_id=?", (did,)).fetchone()
            if old:
                if old["content_sha256"] != content_sha or bytes(old["raw"]) != raw or old["obligation_id"] != args["obligation_id"]:
                    fail("IDEMPOTENCY_CONFLICT", did)
                self.event("RECEIPT_REPLAY", did, tick, {"sha256": content_sha})
            else:
                if self.db.execute("SELECT count(*) FROM receipts").fetchone()[0] >= 256:
                    fail("RESOURCE_LIMIT", "receipts")
                self.db.execute("INSERT INTO receipts VALUES(?,?,?,?,?,?,?,?,?,?)",
                                (did, args["obligation_id"], filename, binding["first_unit"], binding["last_unit"],
                                 content_sha, len(raw), tick, received_ns, raw))
                self.event("RECEIVED", did, tick, {"sha256": content_sha, "bytes": len(raw)})
            self.hook("receive.before_commit")
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise
        self.hook("receive.after_commit")
        return self.status(did)

    def inspect_content(self, receipt):
        """Inspect literal received content against this receiver's retained spec."""
        value = strict_loads(bytes(receipt["raw"]))
        object_fields(value, PRODUCT_FIELDS, path="product")
        if value["schema"] != FORMAT:
            fail("UNSUPPORTED_PRODUCT", "product.schema")
        for key in ("run_id", "contract_id", "obligation_id", "recipient", "production_id", "arrangement_id",
                    "provider_id", "delivery_id", "capacity_key", "lot_id"):
            identifier(value[key], "product." + key)
        sha256(value["contract_sha256"], "product.contract_sha256")
        integer(value["revision"], "product.revision", 0)
        for key in ("first_unit", "last_unit"):
            integer(value[key], "product." + key, 1, 2000)
        integer(value["attempt"], "product.attempt", 1, self.contract["max_attempts"])
        if value["supersedes"] is not None:
            identifier(value["supersedes"], "product.supersedes")
        if value["run_id"] != self.contract["run_id"]:
            fail("WRONG_RUN")
        if value["contract_id"] != self.contract["contract_id"] or value["contract_sha256"] != self.contract_sha256:
            fail("WRONG_CONTRACT")
        if value["delivery_id"] != receipt["delivery_id"]:
            fail("DELIVERY_ID_MISMATCH")
        if value["obligation_id"] != receipt["obligation_id"]:
            fail("WRONG_OBLIGATION")
        obligation = self.obligations[receipt["obligation_id"]]
        if obligation["status"] != "ACTIVE":
            fail("CANCELLED_OBLIGATION")
        if not self.contract["source_complete"]:
            fail("SOURCE_NOT_ESTABLISHED")
        if value["revision"] != obligation["revision"]:
            fail("STALE_REVISION")
        if value["recipient"] != obligation["recipient"]:
            fail("WRONG_RECIPIENT")
        binding = self.delivery_binding(receipt["delivery_id"], receipt["obligation_id"])
        if any(value[k] != expected for k, expected in binding.items()):
            fail("DELIVERY_BINDING_MISMATCH")
        labels = value["labels"]
        expected_count = receipt["last_unit"] - receipt["first_unit"] + 1
        if type(labels) is not list or len(labels) != expected_count:
            fail("UNIT_COVERAGE_MISMATCH")
        ordinals = []
        spec = obligation["spec"]
        for index, unit in enumerate(labels):
            object_fields(unit, LABEL_FIELDS, path="label")
            ordinal = integer(unit["ordinal"], "label.ordinal", 1, obligation["quantity"])
            ordinals.append(ordinal)
            for key in LITERAL_FIELDS:
                text_value(unit[key], "label." + key)
                if unit[key] != spec[key]:
                    fail("CONTENT_MISMATCH", key)
            text_value(unit["serial"], "label.serial", 166)
            if unit["serial"] != spec["serial_prefix"] + str(ordinal).zfill(6):
                fail("SERIAL_MISMATCH")
        if len(set(ordinals)) != len(ordinals):
            fail("DUPLICATE_UNITS")
        if ordinals != list(range(receipt["first_unit"], receipt["last_unit"] + 1)):
            fail("UNIT_COVERAGE_MISMATCH")
        return value

    def check_correction(self, product, receipt):
        predecessor = product["supersedes"]
        expected_predecessor = product["arrangement_id"] + "." + product["lot_id"] + ".A1.D"
        if (product["attempt"] == 1 and predecessor is not None) or \
                (product["attempt"] == 2 and predecessor != expected_predecessor):
            fail("INVALID_CORRECTION", "attempt/predecessor binding")
        if predecessor is None:
            previous = self.db.execute("""SELECT delivery_id FROM decisions WHERE obligation_id=?
                AND first_unit=? AND last_unit=? AND delivery_id=? AND decision='REJECTED' LIMIT 1""",
                (receipt["obligation_id"], receipt["first_unit"], receipt["last_unit"], expected_predecessor)).fetchone()
            if previous:
                fail("CORRECTION_HISTORY_REQUIRED", previous[0])
            # A different agreement's A1 is a separately funded production, not
            # this agreement's cheap A2. The broker and fresh verifier enforce
            # prior cancellation and absence of accepted/overlapping allocation;
            # this content service still forbids duplicate imported units.
            return
        seen = {receipt["delivery_id"]}
        count = 1
        child = self.db.execute("SELECT delivery_id FROM decisions WHERE supersedes=? LIMIT 1", (predecessor,)).fetchone()
        if child:
            fail("CORRECTION_BRANCH_CONFLICT", child[0])
        while predecessor is not None:
            if predecessor in seen:
                fail("INVALID_CORRECTION", "cycle")
            seen.add(predecessor)
            prior = self.db.execute("SELECT * FROM decisions WHERE delivery_id=?", (predecessor,)).fetchone()
            if prior is None or prior["decision"] != "REJECTED" or prior["obligation_id"] != receipt["obligation_id"] or \
                    prior["first_unit"] != receipt["first_unit"] or prior["last_unit"] != receipt["last_unit"]:
                fail("INVALID_CORRECTION", predecessor)
            count += 1
            if count > self.contract["max_attempts"]:
                fail("ATTEMPT_LIMIT")
            predecessor = prior["supersedes"]

    def inspect(self, args):
        object_fields(args, {"delivery_id", "now_tick"}, path="inspect")
        did = identifier(args["delivery_id"], "inspect.delivery_id")
        tick = integer(args["now_tick"], "inspect.now_tick", 0, 1_000_000_000)
        self.hook("inspect.before_begin")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.hook("inspect.after_begin")
            receipt = self.db.execute("SELECT * FROM receipts WHERE delivery_id=?", (did,)).fetchone()
            if receipt is None:
                fail("UNKNOWN_DELIVERY", did)
            previous = self.db.execute("SELECT * FROM decisions WHERE delivery_id=?", (did,)).fetchone()
            if tick < receipt["received_tick"] or (previous is not None and tick < previous["inspected_tick"]):
                fail("INVALID_RANGE", "inspection clock moved backwards")
            if previous is None:
                product = None
                decision, code = "ACCEPTED", "ACCEPTED"
                inspected_ns = time.monotonic_ns()
                try:
                    product = self.inspect_content(receipt)
                    self.check_correction(product, receipt)
                    obligation = self.obligations[receipt["obligation_id"]]
                    if tick > obligation["deadline_tick"] or inspected_ns < self.contract["start_ns"] or inspected_ns > self.contract["start_ns"] + self.contract["wall_deadline_ms"] * 1_000_000:
                        fail("DEADLINE_EXPIRED")
                    occupied = self.db.execute("SELECT ordinal FROM imported_units WHERE obligation_id=? AND ordinal BETWEEN ? AND ? LIMIT 1",
                                               (receipt["obligation_id"], receipt["first_unit"], receipt["last_unit"])).fetchone()
                    if occupied:
                        fail("DUPLICATE_FULFILLMENT")
                except HarnessError as error:
                    decision, code = "REJECTED", error.code
                # Preserve correction and revision metadata only when it parses;
                # all acceptance decisions above independently validate it.
                if product is None:
                    try:
                        parsed = strict_loads(bytes(receipt["raw"]))
                        product = parsed if type(parsed) is dict else {}
                    except HarnessError:
                        product = {}
                revision = product.get("revision") if type(product.get("revision")) is int else None
                recipient = product.get("recipient") if type(product.get("recipient")) is str else None
                supersedes = product.get("supersedes")
                if supersedes is not None:
                    try:
                        identifier(supersedes, "supersedes")
                    except HarnessError:
                        supersedes = None
                if decision == "ACCEPTED":
                    for unit in product["labels"]:
                        self.db.execute("INSERT INTO imported_units VALUES(?,?,?,?,?,?,?,?,?,?)",
                                        (receipt["obligation_id"], unit["ordinal"], did, unit["serial"], unit["sku"],
                                         unit["name_en"], unit["name_fr"], unit["instructions_en"], unit["instructions_fr"], unit["lot"]))
                quantity = receipt["last_unit"] - receipt["first_unit"] + 1
                self.db.execute("INSERT INTO decisions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                (did, receipt["obligation_id"], decision, code, tick, inspected_ns, receipt["content_sha256"],
                                 revision, recipient, receipt["first_unit"], receipt["last_unit"], quantity, supersedes))
                self.event("RECIPIENT_" + decision, did, tick, {"code": code, "quantity": quantity, "sha256": receipt["content_sha256"]})
            else:
                self.event("INSPECTION_REPLAY", did, tick, {"original_decision": previous["decision"]})
            self.hook("inspect.before_commit")
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise
        self.hook("inspect.after_commit")
        self.hook("inspect.before_observation")
        # The observed time is taken after the decision and imported units have
        # committed.  A restart must use its later observation, never invent an
        # earlier favorable timestamp.  Existing observations are immutable.
        self.db.execute("BEGIN IMMEDIATE")
        try:
            observed = self.db.execute("SELECT * FROM observations WHERE delivery_id=?", (did,)).fetchone()
            if observed is None:
                decision = self.db.execute("SELECT * FROM decisions WHERE delivery_id=?", (did,)).fetchone()
                observed_ns = time.monotonic_ns()
                self.db.execute("INSERT INTO observations VALUES(?,?,?,?,?)",
                                (did, decision["decision"], decision["content_sha256"], tick, observed_ns))
                self.event("DECISION_OBSERVED", did, tick, {"decision": decision["decision"], "sha256": decision["content_sha256"], "observed_ns": observed_ns})
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise
        self.hook("inspect.after_observation")
        return self.status(did)

    def status(self, delivery_id):
        identifier(delivery_id, "delivery_id")
        receipt = self.db.execute("SELECT * FROM receipts WHERE delivery_id=?", (delivery_id,)).fetchone()
        if receipt is None:
            fail("UNKNOWN_DELIVERY", delivery_id)
        result = {k: receipt[k] for k in receipt.keys() if k != "raw"}
        decision = self.db.execute("SELECT * FROM decisions WHERE delivery_id=?", (delivery_id,)).fetchone()
        observation = self.db.execute("SELECT * FROM observations WHERE delivery_id=?", (delivery_id,)).fetchone()
        result["decision"] = dict(decision) if decision else None
        result["observation"] = dict(observation) if observation else None
        result["status"] = decision["decision"] if decision else "RECEIVED"
        result["accepted_units"] = self.db.execute("SELECT count(*) FROM imported_units WHERE delivery_id=?", (delivery_id,)).fetchone()[0]
        result["timely"] = None
        if observation and decision and decision["decision"] == "ACCEPTED":
            obligation = self.obligations[receipt["obligation_id"]]
            result["timely"] = (observation["observed_tick"] <= obligation["deadline_tick"] and
                                self.contract["start_ns"] <= observation["observed_ns"] <=
                                self.contract["start_ns"] + self.contract["wall_deadline_ms"] * 1_000_000)
        return result

    def snapshot(self):
        return {"schema": SCHEMA, "contract_sha256": self.contract_sha256,
                "deliveries": [self.status(row[0]) for row in self.db.execute("SELECT delivery_id FROM receipts ORDER BY delivery_id")],
                "imported_units": self.db.execute("SELECT count(*) FROM imported_units").fetchone()[0],
                "event_count": self.db.execute("SELECT count(*) FROM events").fetchone()[0]}

    def dispatch(self, operation, args):
        if operation == "receive":
            return self.receive(args)
        if operation == "inspect":
            return self.inspect(args)
        if operation == "status":
            object_fields(args, {"delivery_id"}, path="status")
            return self.status(args["delivery_id"])
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
    parser = Parser(description="Digital product receipt and acceptance / Réception et acceptation du produit numérique", add_help=False)
    parser.add_argument("-h", "--help", action="help",
                        help="Show complete help and exit / Afficher l’aide complète et quitter")
    parser.add_argument("--db", required=True, help="Recipient SQLite path / Chemin SQLite du destinataire")
    parser.add_argument("--inbox", required=True, help="Received-file directory / Répertoire des fichiers reçus")
    parser.add_argument("--contract", required=True, help="Retained acceptance contract / Contrat d’acceptation conservé")
    options = parser.parse_args(argv)
    service = None
    try:
        service = Receiver(options.db, options.inbox, options.contract)
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
