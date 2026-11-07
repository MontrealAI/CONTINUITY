"""Retained participant policies and a synthetic, durable SMU ledger.

This service is controlled by the exercise authority, never by the candidate.
It evaluates immutable proposals using separately retained policies. All values
are authored synthetic minor units; no account here is a financial service.

Reuse: bounded JSON/canonical helpers from continuity_harness.schema and the
SQLite WAL/FULL, BEGIN IMMEDIATE and transition-hook discipline of
continuity_harness.service at qualified baseline 396227d8da2f55f674f479de16089c7ce28ef290.
Neither historical module is changed. The fresh verifier must implement its own
economic and ledger replay rather than import this module as its oracle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import time

from .policy_schema import validate_policies, validate_proposal_shape
from .schema import validate_contract

from continuity_harness.schema import (HarnessError, MAX_JSON_BYTES, canonical, digest,
                                       identifier, integer, object_fields, strict_load,
                                       strict_loads, sha256)


POLICY_SCHEMA = "continuity-economy/policies/v1"
PROPOSAL_SCHEMA = "continuity-economy/proposal/v1"
SERVICE_SCHEMA = "continuity-economy/participants/v1"
MAX_MONEY = 1_000_000_000
MAX_TICK = 1_000_000_000
MAX_ITEMS = 4_096
SINK = "COST_SINK"
OUTSIDE = "OUTSIDE_ACCOUNT"
ACTIVE = ("ACTIVE", "SETTLED")


MESSAGES = {
    "INVALID_POLICY": ("The retained participant policy is invalid.", "La politique conservée du participant est invalide."),
    "INVALID_PROPOSAL": ("The proposed terms are invalid.", "Les conditions proposées sont invalides."),
    "UNSUPPORTED_VERSION": ("The schema or version is unsupported.", "Le schéma ou la version n’est pas pris en charge."),
    "CONTRACT_MISMATCH": ("The proposal is not bound to this retained contract.", "La proposition n’est pas liée à ce contrat conservé."),
    "POLICY_REVISION_MISMATCH": ("The retained policy revision changed; a new proposal is required.", "La révision de la politique conservée a changé ; une nouvelle proposition est requise."),
    "IDEMPOTENCY_CONFLICT": ("This stable identifier already binds different terms.", "Cet identifiant stable est déjà lié à d’autres conditions."),
    "PROPOSAL_NOT_FOUND": ("The proposal does not exist.", "La proposition n’existe pas."),
    "AGREEMENT_NOT_FOUND": ("The agreement does not exist.", "L’accord n’existe pas."),
    "AGREEMENT_CLOSED": ("The agreement is already closed.", "L’accord est déjà clos."),
    "CONTRACT_ALREADY_COMMITTED": ("Another agreement already commits this contract.", "Un autre accord engage déjà ce contrat."),
    "PROPOSAL_EXPIRED": ("The proposal or permission has expired.", "La proposition ou l’autorisation a expiré."),
    "CLOCK_REGRESSION": ("The trusted exercise clock moved backwards.", "L’horloge de confiance de l’exercice a reculé."),
    "CONSENT_REVOKED": ("Current consent does not authorize this action.", "Le consentement actuel n’autorise pas cette action."),
    "ACTION_NOT_ALLOWED": ("The participant cannot perform this action under the contract.", "Le participant ne peut pas effectuer cette action selon le contrat."),
    "INSUFFICIENT_FUNDS": ("Unencumbered modeled funds are insufficient.", "Les fonds modélisés non engagés sont insuffisants."),
    "BUYER_OUTSIDE_OPTION": ("The buyer does not meet its modeled outside option or price constraint.", "L’acheteur ne satisfait pas son option extérieure ou sa limite de prix modélisée."),
    "UNCERTAIN_BUYER_VALUE": ("The value interval crosses the break-even condition; acceptance is not established.", "L’intervalle de valeur traverse le seuil de rentabilité ; l’acceptation n’est pas établie."),
    "PROVIDER_PARTICIPATION": ("The provider’s payment does not cover its declared cost budget and outside option.", "Le paiement du fournisseur ne couvre pas son budget de coûts déclaré et son option extérieure."),
    "COORDINATOR_PARTICIPATION": ("The coordinator’s fee does not cover its declared cost and outside option.", "Les frais du coordonnateur ne couvrent pas son coût déclaré et son option extérieure."),
    "LIABILITY_LIMIT": ("The declared failure exposure exceeds a participant’s accepted limit.", "L’exposition déclarée en cas d’échec dépasse la limite acceptée d’un participant."),
    "REWORK_BUDGET_MISMATCH": ("The proposed correction budget does not match the retained cost model.", "Le budget de correction proposé ne correspond pas au modèle de coûts conservé."),
    "PRICE_NOT_BALANCED": ("The buyer’s price does not equal provider payments plus the coordinator fee.", "Le prix de l’acheteur ne correspond pas aux paiements des fournisseurs plus les frais du coordonnateur."),
    "ALLOCATION_COVERAGE": ("Allocations must cover each active obligation exactly in its authorized lots.", "Les affectations doivent couvrir exactement chaque engagement actif dans ses lots autorisés."),
    "CAPACITY_TERMS_EXCEEDED": ("The proposal exceeds a declared capacity window.", "La proposition dépasse une fenêtre de capacité déclarée."),
    "SPLIT_NOT_ALLOWED": ("This contract does not permit splitting an obligation among providers.", "Ce contrat n’autorise pas la répartition d’un engagement entre fournisseurs."),
    "DUPLICATE_PRODUCTION": ("The same lot and attempt already have a different production identifier.", "Le même lot et la même tentative ont déjà un autre identifiant de production."),
    "INVALID_ATTEMPT": ("The production attempt is unsupported or lacks its predecessor.", "La tentative de production n’est pas prise en charge ou ne possède pas de prédécesseur."),
    "MISSING_PRODUCTION": ("Required production evidence is missing.", "Une preuve de production requise est absente."),
    "MISSING_ACCEPTANCE": ("Distinct recipient acceptance references are required for every authorized lot.", "Des références d’acceptation du destinataire distinctes sont requises pour chaque lot autorisé."),
    "TECHNICAL_CONTROL_FORBIDDEN": ("A separately authorized and funded technical control is unavailable.", "Aucun contrôle technique distinctement autorisé et financé n’est disponible."),
    "POLICY_IDENTITY_CHANGED": ("Policy replacement cannot rewrite participant identities or initial balances.", "Le remplacement d’une politique ne peut pas réécrire les identités ni les soldes initiaux des participants."),
    "UNSAFE_PATH": ("The service path is unsafe.", "Le chemin du service n’est pas sûr."),
    "CHECKPOINT_BUSY": ("The durable checkpoint is blocked by an active connection.", "Le point de contrôle durable est bloqué par une connexion active."),
    "INVALID_HOOK": ("The transition hook is unsupported.", "Le point de transition n’est pas pris en charge."),
    "UNSUPPORTED_OPERATION": ("The participant operation is unsupported.", "L’opération du participant n’est pas prise en charge."),
    "SERVICE_ERROR": ("The participant operation did not complete.", "L’opération du participant n’a pas abouti."),
    "SERVICE_START_FAILED": ("The participant service could not start.", "Le service des participants n’a pas pu démarrer."),
    "CLI_ARGUMENT": ("Invalid participant-service command arguments.", "Arguments de commande du service des participants invalides."),
}


class ParticipantError(ValueError):
    def __init__(self, code, detail=""):
        self.code = code
        self.location = detail
        pair = MESSAGES.get(code, ("Participant operation refused.", "Opération du participant refusée."))
        self.detail = {"en": pair[0], "fr": pair[1]}
        super().__init__(code + (": " + detail if detail else ""))


def fail(code, detail=""):
    raise ParticipantError(code, detail)


def money(value, path):
    return integer(value, path, 0, MAX_MONEY)


def tick_value(value, path="tick"):
    return integer(value, path, 0, MAX_TICK)


def _list(value, path, maximum=MAX_ITEMS):
    if type(value) is not list or len(value) > maximum:
        fail("INVALID_PROPOSAL", path)
    return value


def _bool(value, path):
    if type(value) is not bool:
        fail("INVALID_POLICY", path)
    return value




def _contract_view(contract):
    """The global contract is validated before any participant state mutation."""
    return validate_contract(contract)


def validate_allocations(contract, policies, allocations):
    _contract_view(contract)
    validate_policies(policies)
    active = {o["obligation_id"]: o for o in contract["obligations"] if o["status"] == "ACTIVE"}
    cps = {p["provider_id"]: p for p in contract["providers"]}
    pps = {p["party_id"]: p for p in policies["providers"]}
    if set(cps) != set(pps):
        fail("INVALID_POLICY", "provider identities do not match contract")
    rows = _list(allocations, "allocations")
    coverage = {oid: [] for oid in active}
    usage, lot_ids = {}, set()
    for a in rows:
        object_fields(a, {"lot_id", "provider_id", "window_id", "obligation_id", "first_unit", "last_unit", "pay_minor"}, path="allocation")
        for key in ("lot_id", "provider_id", "window_id", "obligation_id"):
            identifier(a[key], "allocation." + key)
        integer(a["first_unit"], "allocation.first_unit", 1, 1_000_000)
        integer(a["last_unit"], "allocation.last_unit", 1, 1_000_000)
        money(a["pay_minor"], "allocation.pay_minor")
        oid, pid = a["obligation_id"], a["provider_id"]
        if a["lot_id"] in lot_ids or oid not in active or pid not in cps:
            fail("ALLOCATION_COVERAGE", a["lot_id"])
        lot_ids.add(a["lot_id"])
        first, last = a["first_unit"], a["last_unit"]
        size = contract["lot_size"] if contract["allow_split"] else active[oid]["quantity"]
        expected_last = min(first + size - 1, active[oid]["quantity"])
        expected_id = f'{oid}.L{(first - 1) // size + 1:03d}'
        if first > active[oid]["quantity"] or (first - 1) % size or last != expected_last or a["lot_id"] != expected_id:
            fail("ALLOCATION_COVERAGE", a["lot_id"])
        windows = {w["window_id"]: w for w in cps[pid]["windows"]}
        if a["window_id"] not in windows:
            fail("ALLOCATION_COVERAGE", "unknown window")
        w = windows[a["window_id"]]
        if w["start"] > active[oid]["deadline_tick"]:
            fail("CAPACITY_TERMS_EXCEEDED", "window begins after deadline")
        coverage[oid].append((first, last, pid))
        key = (pid, a["window_id"])
        usage[key] = usage.get(key, 0) + last - first + 1
        if usage[key] > w["capacity"]:
            fail("CAPACITY_TERMS_EXCEEDED", pid + "." + a["window_id"])
    for oid, rows_for_order in coverage.items():
        cursor = 1
        for first, last, _ in sorted(rows_for_order):
            if first != cursor:
                fail("ALLOCATION_COVERAGE", oid)
            cursor = last + 1
        if cursor != active[oid]["quantity"] + 1:
            fail("ALLOCATION_COVERAGE", oid)
        if not contract["allow_split"] and len({r[2] for r in rows_for_order}) > 1:
            fail("SPLIT_NOT_ALLOWED", oid)
    return allocations


def quote_terms(contract, policies, allocations):
    """Public planning arithmetic, available equally to all candidate methods.

    This is not participant acceptance and must not be the verifier's oracle.
    Setup is once per provider/arrangement; correction setup is once per provider
    if a correction occurs. The funded budget allows one correction of every lot.
    """
    validate_allocations(contract, policies, allocations)
    grouped = {}
    for a in allocations:
        row = grouped.setdefault(a["provider_id"], {"units": 0, "promised_payment_minor": 0})
        row["units"] += a["last_unit"] - a["first_unit"] + 1
        row["promised_payment_minor"] += a["pay_minor"]
    provider_rows = []
    for policy in sorted(policies["providers"], key=lambda p: p["party_id"]):
        pid = policy["party_id"]
        if pid not in grouped:
            continue
        row = grouped[pid]
        base = policy["setup_cost_minor"] + policy["unit_cost_minor"] * row["units"]
        rework = (policy["rework_setup_cost_minor"] + policy["rework_unit_cost_minor"] * row["units"]) if contract["max_attempts"] == 2 else 0
        outside = max(policy["min_profit_minor"], policy["outside_profit_minor"])
        total = base + rework
        for amount in (base, rework, total + outside):
            money(amount, "quote.total")
        provider_rows.append({"party_id": pid, **row, "base_cost_minor": base, "rework_cost_minor": rework,
                              "maximum_unpaid_cost_exposure_minor": total,
                              "participation_profit_minor": outside,
                              "minimum_payment_minor": total + outside,
                              "guaranteed_profit_minor": row["promised_payment_minor"] - total})
    c = policies["coordinator"]
    cf = c["operating_cost_minor"] + max(c["min_profit_minor"], c["outside_profit_minor"])
    minimum = sum(p["minimum_payment_minor"] for p in provider_rows) + cf
    buyer = policies["buyer"]
    for amount in (cf, minimum, sum(p["rework_cost_minor"] for p in provider_rows)):
        money(amount, "quote.total")
    return {"currency": "SMU", "providers": provider_rows,
            "minimum_coordinator_fee_minor": cf, "minimum_buyer_price_minor": minimum,
            "rework_budget_minor": sum(p["rework_cost_minor"] for p in provider_rows),
            "buyer_definite_max_price_minor": min(buyer["max_price_minor"], buyer["value_min_minor"] - buyer["outside_utility_minor"]),
            "buyer_possible_max_price_minor": min(buyer["max_price_minor"], buyer["value_max_minor"] - buyer["outside_utility_minor"]),
            "break_even_value_minor": minimum + buyer["outside_utility_minor"],
            "scope": "AUTHORED_SYNTHETIC_MODEL"}


def validate_proposal(contract, policies, value):
    validate_proposal_shape(value)
    object_fields(value, {"schema", "proposal_id", "contract_sha256", "policy_revision", "allocations", "buyer_price_minor", "coordinator_fee_minor", "rework_budget_minor", "cancellation_fee_minor", "expires_tick"}, path="proposal")
    if value["schema"] != PROPOSAL_SCHEMA:
        fail("UNSUPPORTED_VERSION", "proposal")
    identifier(value["proposal_id"], "proposal_id")
    sha256(value["contract_sha256"], "contract_sha256")
    integer(value["policy_revision"], "policy_revision", 1, MAX_ITEMS)
    if value["contract_sha256"] != digest(contract):
        fail("CONTRACT_MISMATCH")
    for key in ("buyer_price_minor", "coordinator_fee_minor", "rework_budget_minor", "cancellation_fee_minor"):
        money(value[key], key)
    tick_value(value["expires_tick"], "expires_tick")
    if value["expires_tick"] < 1 or value["cancellation_fee_minor"] > value["buyer_price_minor"]:
        fail("INVALID_PROPOSAL", "expiry or cancellation fee")
    validate_allocations(contract, policies, value["allocations"])
    canonical(value)
    return value


DDL = """
CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS policy_versions(revision INTEGER PRIMARY KEY,sha256 TEXT NOT NULL,payload TEXT NOT NULL,effective_tick INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS proposals(proposal_id TEXT PRIMARY KEY,sha256 TEXT NOT NULL,payload TEXT NOT NULL,policy_revision INTEGER NOT NULL,submitted_tick INTEGER NOT NULL,status TEXT NOT NULL,decision_tick INTEGER);
CREATE TABLE IF NOT EXISTS decisions(sequence INTEGER PRIMARY KEY AUTOINCREMENT,proposal_id TEXT NOT NULL,party_id TEXT NOT NULL,role TEXT NOT NULL,verdict TEXT NOT NULL,code TEXT NOT NULL,tick INTEGER NOT NULL,policy_revision INTEGER NOT NULL,detail TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS agreements(agreement_id TEXT PRIMARY KEY,proposal_id TEXT UNIQUE NOT NULL,kind TEXT NOT NULL,status TEXT NOT NULL,terms_sha256 TEXT NOT NULL,policy_revision INTEGER NOT NULL,accepted_tick INTEGER NOT NULL,settled_tick INTEGER,cancelled_tick INTEGER,acceptance_ids TEXT,reason TEXT,pricing TEXT NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_contract ON agreements((1)) WHERE status IN ('ACTIVE','SETTLED');
CREATE TABLE IF NOT EXISTS accounts(party_id TEXT PRIMARY KEY,role TEXT NOT NULL,balance_minor INTEGER NOT NULL CHECK(balance_minor>=0),initial_balance_minor INTEGER NOT NULL CHECK(initial_balance_minor>=0));
CREATE TABLE IF NOT EXISTS holds(hold_id TEXT PRIMARY KEY,agreement_id TEXT NOT NULL,party_id TEXT NOT NULL,kind TEXT NOT NULL,amount_minor INTEGER NOT NULL CHECK(amount_minor>=0),initial_minor INTEGER NOT NULL CHECK(initial_minor>=0),created_tick INTEGER NOT NULL,closed_tick INTEGER,UNIQUE(agreement_id,party_id,kind));
CREATE TABLE IF NOT EXISTS entries(sequence INTEGER PRIMARY KEY AUTOINCREMENT,entry_id TEXT UNIQUE NOT NULL,agreement_id TEXT,kind TEXT NOT NULL,from_party TEXT,to_party TEXT,amount_minor INTEGER NOT NULL CHECK(amount_minor>=0),hold_kind TEXT,tick INTEGER NOT NULL,detail TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS productions(production_id TEXT PRIMARY KEY,agreement_id TEXT NOT NULL,lot_id TEXT NOT NULL,provider_id TEXT NOT NULL,attempt INTEGER NOT NULL,request_sha256 TEXT NOT NULL,charge_minor INTEGER NOT NULL,tick INTEGER NOT NULL,funding_party_id TEXT NOT NULL,setup_charged INTEGER NOT NULL,UNIQUE(agreement_id,lot_id,attempt));
CREATE TABLE IF NOT EXISTS authorizations(sequence INTEGER PRIMARY KEY AUTOINCREMENT,action_id TEXT NOT NULL,agreement_id TEXT NOT NULL,party_id TEXT NOT NULL,action TEXT NOT NULL,verdict TEXT NOT NULL,code TEXT NOT NULL,tick INTEGER NOT NULL,request_sha256 TEXT NOT NULL,policy_revision INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS events(sequence INTEGER PRIMARY KEY AUTOINCREMENT,event_id TEXT UNIQUE NOT NULL,kind TEXT NOT NULL,tick INTEGER NOT NULL,payload TEXT NOT NULL);
"""


def checked_path(path):
    p = Path(path).absolute()
    if any(part.is_symlink() for part in (p, *p.parents)):
        fail("UNSAFE_PATH")
    if p.exists() and not p.is_file():
        fail("UNSAFE_PATH")
    return p


class ParticipantService:
    def __init__(self, database, contract, policies, hook=None):
        _contract_view(contract)
        validate_policies(policies)
        if {p["provider_id"] for p in contract["providers"]} != {p["party_id"] for p in policies["providers"]}:
            fail("INVALID_POLICY", "provider identities")
        self.contract = json.loads(canonical(contract))
        self.original_policies = json.loads(canonical(policies))
        self.contract_sha256 = digest(contract)
        self.path = checked_path(database)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA busy_timeout=10000")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript(DDL)
        self.hook = hook or (lambda name: None)
        try:
            self._initialize()
        except BaseException:
            self.db.close()
            raise

    def close(self):
        self.db.close()

    def _meta(self, key, default=None):
        row = self.db.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def _set_meta(self, key, value):
        self.db.execute("INSERT INTO metadata VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, canonical(value).decode()))

    def _initialize(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            existing = self._meta("schema")
            if existing is not None:
                if existing != SERVICE_SCHEMA or self._meta("contract_sha256") != self.contract_sha256 or self._meta("initial_policy_sha256") != digest(self.original_policies):
                    fail("CONTRACT_MISMATCH", "restart identity")
                self.db.commit()
                return
            self._set_meta("schema", SERVICE_SCHEMA)
            self._set_meta("run_id", self.contract["run_id"])
            self._set_meta("contract_sha256", self.contract_sha256)
            self._set_meta("initial_policy_sha256", digest(self.original_policies))
            self._set_meta("current_policy_revision", self.original_policies["revision"])
            self._set_meta("last_tick", 0)
            self.db.execute("INSERT INTO policy_versions VALUES (?,?,?,?)", (self.original_policies["revision"], digest(self.original_policies), canonical(self.original_policies).decode(), 0))
            records = [(self.original_policies["buyer"], "buyer"), (self.original_policies["coordinator"], "coordinator"), (self.original_policies["technical_sponsor"], "technical_sponsor")]
            records += [(p, "provider") for p in self.original_policies["providers"]]
            for p, role in records:
                self.db.execute("INSERT INTO accounts VALUES (?,?,?,?)", (p["party_id"], role, p["balance_minor"], p["balance_minor"]))
            for pid, role in ((SINK, "modeled_cost_sink"), (OUTSIDE, "modeled_withdrawal_destination")):
                self.db.execute("INSERT INTO accounts VALUES (?,?,0,0)", (pid, role))
            self._set_meta("initial_total_minor", sum(p["balance_minor"] for p, _ in records))
            self._event("initial-policies", "INITIAL_POLICIES", 0, {"policy_sha256": digest(self.original_policies), "contract_sha256": self.contract_sha256})
            self.hook("init.before_commit")
            self.db.commit()
            self.hook("init.after_commit")
        except BaseException:
            if self.db.in_transaction:
                self.db.rollback()
            raise

    def _transaction(self, op, now, function):
        tick_value(now)
        self.hook(op + ".before_begin")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.hook(op + ".after_begin")
            if now < self._meta("last_tick", 0):
                fail("CLOCK_REGRESSION")
            self._set_meta("last_tick", now)
            result = function()
            self._invariants()
            self.hook(op + ".before_commit")
            self.db.commit()
        except BaseException:
            if self.db.in_transaction:
                self.db.rollback()
            raise
        self.hook(op + ".after_commit")
        return result

    def _invariants(self):
        total = self.db.execute("SELECT COALESCE(SUM(balance_minor),0) FROM accounts").fetchone()[0]
        if total != self._meta("initial_total_minor"):
            raise sqlite3.IntegrityError("synthetic currency conservation")
        for a in self.db.execute("SELECT * FROM accounts"):
            if self._held(a["party_id"]) > a["balance_minor"]:
                raise sqlite3.IntegrityError("encumbered funds exceed balance")

    def _policies(self, revision=None):
        revision = self._meta("current_policy_revision") if revision is None else revision
        row = self.db.execute("SELECT payload FROM policy_versions WHERE revision=?", (revision,)).fetchone()
        if row is None:
            fail("POLICY_REVISION_MISMATCH")
        return json.loads(row[0])

    def _proposal(self, pid):
        row = self.db.execute("SELECT * FROM proposals WHERE proposal_id=?", (pid,)).fetchone()
        if row is None:
            fail("PROPOSAL_NOT_FOUND", pid)
        result = dict(row)
        result["payload"] = json.loads(result["payload"])
        return result

    def _agreement(self, aid):
        row = self.db.execute("SELECT * FROM agreements WHERE agreement_id=?", (aid,)).fetchone()
        if row is None:
            fail("AGREEMENT_NOT_FOUND", aid)
        result = dict(row)
        result["pricing"] = json.loads(result["pricing"])
        result["acceptance_ids"] = json.loads(result["acceptance_ids"]) if result["acceptance_ids"] else None
        return result

    def _account(self, pid):
        row = self.db.execute("SELECT * FROM accounts WHERE party_id=?", (pid,)).fetchone()
        if row is None:
            fail("INVALID_POLICY", "unknown participant")
        return dict(row)

    def _held(self, pid):
        return self.db.execute("SELECT COALESCE(SUM(amount_minor),0) FROM holds WHERE party_id=?", (pid,)).fetchone()[0]

    def _free(self, pid):
        return self._account(pid)["balance_minor"] - self._held(pid)

    def _entry(self, eid, aid, kind, src, dst, amount, hold_kind, now, detail=None):
        self.db.execute("INSERT INTO entries(entry_id,agreement_id,kind,from_party,to_party,amount_minor,hold_kind,tick,detail) VALUES (?,?,?,?,?,?,?,?,?)", (eid, aid, kind, src, dst, amount, hold_kind, now, canonical(detail or {}).decode()))

    def _event(self, eid, kind, now, payload):
        self.db.execute("INSERT INTO events(event_id,kind,tick,payload) VALUES (?,?,?,?)", (eid, kind, now, canonical(payload).decode()))

    def _hold(self, aid, pid, kind, amount, now):
        if self._free(pid) < amount:
            fail("INSUFFICIENT_FUNDS", pid)
        hid = digest({"agreement_id": aid, "party_id": pid, "kind": kind})
        self.db.execute("INSERT INTO holds VALUES (?,?,?,?,?,?,?,NULL)", (hid, aid, pid, kind, amount, amount, now))
        self._entry("hold." + hid, aid, "HOLD", pid, None, amount, kind, now)

    def _transfer(self, eid, aid, kind, src, dst, amount, now, hold_kind=None, detail=None):
        if amount < 0 or self._account(src)["balance_minor"] < amount:
            fail("INSUFFICIENT_FUNDS", src)
        if hold_kind is not None:
            row = self.db.execute("SELECT * FROM holds WHERE agreement_id=? AND party_id=? AND kind=?", (aid, src, hold_kind)).fetchone()
            if row is None or row["amount_minor"] < amount:
                fail("INSUFFICIENT_FUNDS", src + "." + hold_kind)
            self.db.execute("UPDATE holds SET amount_minor=amount_minor-? WHERE hold_id=?", (amount, row["hold_id"]))
        elif self._free(src) < amount:
            fail("INSUFFICIENT_FUNDS", src)
        self.db.execute("UPDATE accounts SET balance_minor=balance_minor-? WHERE party_id=?", (amount, src))
        self.db.execute("UPDATE accounts SET balance_minor=balance_minor+? WHERE party_id=?", (amount, dst))
        self._entry(eid, aid, kind, src, dst, amount, hold_kind, now, detail)

    def _release_all(self, aid, now):
        for h in self.db.execute("SELECT * FROM holds WHERE agreement_id=? AND closed_tick IS NULL ORDER BY hold_id", (aid,)).fetchall():
            self.db.execute("UPDATE holds SET amount_minor=0,closed_tick=? WHERE hold_id=?", (now, h["hold_id"]))
            self._entry("release." + h["hold_id"], aid, "RELEASE", h["party_id"], None, h["amount_minor"], h["kind"], now)

    def _policy_party(self, policies, pid):
        for role in ("buyer", "coordinator", "technical_sponsor"):
            if policies[role]["party_id"] == pid:
                return policies[role], role
        for p in policies["providers"]:
            if p["party_id"] == pid:
                return p, "provider"
        fail("INVALID_POLICY", "unknown participant")

    def _has_consent(self, pid, action, now, policies=None):
        policies = policies or self._policies()
        party, role = self._policy_party(policies, pid)
        if role == "technical_sponsor":
            return party["authorized"]
        if now >= party["consent_until_tick"]:
            return False
        return not any(r["party_id"] == pid and r["tick"] <= now and r["action"] in (action, "consent") for r in self.contract["revocations"])

    def _can_act(self, agreement, party_id, action, now):
        if agreement["status"] != "ACTIVE":
            return "AGREEMENT_CLOSED"
        proposal = self._proposal(agreement["proposal_id"])["payload"]
        if now >= proposal["expires_tick"] or now > self.contract["deadline_tick"]:
            return "PROPOSAL_EXPIRED"
        policies = self._policies()
        selected = {a["provider_id"] for a in proposal["allocations"]}
        buyer = policies["buyer"]["party_id"]
        coordinator = policies["coordinator"]["party_id"]
        roles = {"produce": selected, "transfer": selected | {coordinator}, "accept": {buyer}, "consent": selected | {buyer, coordinator}}
        if action not in roles or party_id not in roles[action]:
            return "ACTION_NOT_ALLOWED"
        required = {party_id}
        if action in ("produce", "transfer"):
            required |= {buyer, coordinator}
        if any(not self._has_consent(pid, action, now, policies) for pid in required):
            return "CONSENT_REVOKED"
        cp = next((p for p in self.contract["providers"] if p["provider_id"] == party_id), None)
        if cp and action in ("produce", "transfer"):
            if not cp["permissions"]["production"] or (action == "transfer" and cp["role"] != "primary" and not cp["permissions"]["disclosure"]):
                return "ACTION_NOT_ALLOWED"
        if agreement["kind"] == "TECHNICAL":
            if not policies["technical_sponsor"]["authorized"]:
                return "TECHNICAL_CONTROL_FORBIDDEN"
            for pid in required - {buyer}:
                p, _ = self._policy_party(policies, pid)
                if not p.get("technical_control_allowed", False):
                    return "TECHNICAL_CONTROL_FORBIDDEN"
        return "AUTHORIZED"

    def _result(self, pid):
        proposal = self._proposal(pid)
        decisions = [dict(r) for r in self.db.execute("SELECT * FROM decisions WHERE proposal_id=? ORDER BY sequence", (pid,))]
        for d in decisions:
            d["detail"] = json.loads(d["detail"])
        row = self.db.execute("SELECT agreement_id FROM agreements WHERE proposal_id=?", (pid,)).fetchone()
        return {"proposal": proposal, "decisions": decisions, "agreement": self._agreement(row[0]) if row else None}

    def _decision_rows(self, proposal, policies, now, quote):
        rows = []
        price = proposal["buyer_price_minor"]
        selected = {p["party_id"]: p for p in quote["providers"]}
        global_code = None
        if proposal["policy_revision"] != policies["revision"]:
            global_code = "POLICY_REVISION_MISMATCH"
        elif now >= proposal["expires_tick"]:
            global_code = "PROPOSAL_EXPIRED"
        elif price != sum(a["pay_minor"] for a in proposal["allocations"]) + proposal["coordinator_fee_minor"]:
            global_code = "PRICE_NOT_BALANCED"
        elif proposal["rework_budget_minor"] != quote["rework_budget_minor"]:
            global_code = "REWORK_BUDGET_MISMATCH"
        elif self.db.execute("SELECT 1 FROM agreements WHERE status IN ('ACTIVE','SETTLED')").fetchone():
            global_code = "CONTRACT_ALREADY_COMMITTED"
        records = [(policies["buyer"], "buyer"), *[(p, "provider") for p in policies["providers"] if p["party_id"] in selected], (policies["coordinator"], "coordinator")]
        for p, role in records:
            pid, code, verdict = p["party_id"], global_code or "ACCEPTED", "ACCEPTED"
            detail = {"scope": "AUTHORED_SYNTHETIC_MODEL", "free_funds_minor": self._free(pid)}
            needed_actions = ("consent", "produce", "transfer") if role == "provider" else ("consent", "accept") if role == "buyer" else ("consent",)
            if not global_code and any(not self._has_consent(pid, action, now, policies) for action in needed_actions):
                code = "CONSENT_REVOKED"
            elif not global_code and role == "buyer":
                detail.update(required_value_minor=price + p["outside_utility_minor"], value_min_minor=p["value_min_minor"], value_max_minor=p["value_max_minor"], outside_utility_minor=p["outside_utility_minor"], net_value_min_minor=p["value_min_minor"] - price, net_value_max_minor=p["value_max_minor"] - price)
                if price > p["max_price_minor"] or p["value_max_minor"] - price < p["outside_utility_minor"]:
                    code = "BUYER_OUTSIDE_OPTION"
                elif p["value_min_minor"] - price < p["outside_utility_minor"]:
                    code, verdict = "UNCERTAIN_BUYER_VALUE", "NOT_ESTABLISHED"
                elif self._free(pid) < price:
                    code = "INSUFFICIENT_FUNDS"
            elif not global_code and role == "provider":
                q = selected[pid]
                detail.update(q)
                cp = next(cp for cp in self.contract["providers"] if cp["provider_id"] == pid)
                if not cp["permissions"]["production"] or (cp["role"] != "primary" and not cp["permissions"]["disclosure"]):
                    code = "ACTION_NOT_ALLOWED"
                elif q["promised_payment_minor"] < q["minimum_payment_minor"]:
                    code = "PROVIDER_PARTICIPATION"
                elif q["maximum_unpaid_cost_exposure_minor"] > p["liability_limit_minor"]:
                    code = "LIABILITY_LIMIT"
                elif self._free(pid) < q["base_cost_minor"] + q["rework_cost_minor"]:
                    code = "INSUFFICIENT_FUNDS"
            elif not global_code and role == "coordinator":
                detail.update(operating_cost_minor=p["operating_cost_minor"], promised_fee_minor=proposal["coordinator_fee_minor"], participation_profit_minor=max(p["min_profit_minor"], p["outside_profit_minor"]), guaranteed_profit_minor=proposal["coordinator_fee_minor"] - p["operating_cost_minor"])
                if proposal["coordinator_fee_minor"] < quote["minimum_coordinator_fee_minor"]:
                    code = "COORDINATOR_PARTICIPATION"
                elif p["operating_cost_minor"] > p["liability_limit_minor"]:
                    code = "LIABILITY_LIMIT"
                elif self._free(pid) < p["operating_cost_minor"]:
                    code = "INSUFFICIENT_FUNDS"
            if code != "ACCEPTED" and verdict != "NOT_ESTABLISHED":
                verdict = "REJECTED"
            rows.append({"party_id": pid, "role": role, "verdict": verdict, "code": code, "detail": detail})
        return rows

    def dispatch(self, operation, args):
        if operation == "ping":
            object_fields(args, set())
            return {"schema": SERVICE_SCHEMA, "pid": os.getpid(), "contract_sha256": self.contract_sha256}
        if operation == "snapshot":
            object_fields(args, set())
            return self.snapshot()
        if operation in ("status", "catalog"):
            object_fields(args, set())
            return self.status()
        if operation == "checkpoint":
            object_fields(args, set())
            result = list(self.db.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone())
            if result != [0, 0, 0]:
                fail("CHECKPOINT_BUSY")
            return {"status": "CHECKPOINTED", "sqlite": result}
        if operation == "propose":
            object_fields(args, {"proposal", "tick"})
            now = tick_value(args["tick"])
            p = validate_proposal(self.contract, self._policies(), args["proposal"])
            def proposed():
                old = self.db.execute("SELECT sha256 FROM proposals WHERE proposal_id=?", (p["proposal_id"],)).fetchone()
                if old:
                    if old[0] != digest(p):
                        fail("IDEMPOTENCY_CONFLICT", p["proposal_id"])
                    return self._result(p["proposal_id"])
                self.db.execute("INSERT INTO proposals VALUES (?,?,?,?,?,'PROPOSED',NULL)", (p["proposal_id"], digest(p), canonical(p).decode(), p["policy_revision"], now))
                return self._result(p["proposal_id"])
            return self._transaction(operation, now, proposed)
        if operation == "decide":
            object_fields(args, {"proposal_id", "tick"})
            pid, now = identifier(args["proposal_id"], "proposal_id"), tick_value(args["tick"])
            def decided():
                saved = self._proposal(pid)
                if saved["status"] != "PROPOSED":
                    return self._result(pid)
                p, policies = saved["payload"], self._policies()
                quote = quote_terms(self.contract, policies, p["allocations"])
                decisions = self._decision_rows(p, policies, now, quote)
                for d in decisions:
                    self.db.execute("INSERT INTO decisions(proposal_id,party_id,role,verdict,code,tick,policy_revision,detail) VALUES (?,?,?,?,?,?,?,?)", (pid, d["party_id"], d["role"], d["verdict"], d["code"], now, policies["revision"], canonical(d["detail"]).decode()))
                status = "ACCEPTED" if all(d["verdict"] == "ACCEPTED" for d in decisions) else "REJECTED" if any(d["verdict"] == "REJECTED" for d in decisions) else "NOT_ESTABLISHED"
                self.db.execute("UPDATE proposals SET status=?,decision_tick=? WHERE proposal_id=?", (status, now, pid))
                if status == "ACCEPTED":
                    self.db.execute("INSERT INTO agreements VALUES (?,?,?,'ACTIVE',?,?,?,NULL,NULL,NULL,NULL,?)", (pid, pid, "TRADE", saved["sha256"], policies["revision"], now, canonical(quote).decode()))
                    self._hold(pid, policies["buyer"]["party_id"], "BUYER_ESCROW", p["buyer_price_minor"], now)
                    for q in quote["providers"]:
                        self._hold(pid, q["party_id"], "WORKING", q["base_cost_minor"], now)
                        self._hold(pid, q["party_id"], "REWORK_LIABILITY", q["rework_cost_minor"], now)
                    c = policies["coordinator"]
                    self._hold(pid, c["party_id"], "COORDINATION", c["operating_cost_minor"], now)
                    self._transfer("coordinate." + pid, pid, "COORDINATION_COST", c["party_id"], SINK, c["operating_cost_minor"], now, "COORDINATION")
                return self._result(pid)
            return self._transaction(operation, now, decided)
        if operation == "authorize":
            object_fields(args, {"agreement_id", "party_id", "action", "action_id", "tick"})
            for key in ("agreement_id", "party_id", "action_id"):
                identifier(args[key], key)
            if args["action"] not in ("produce", "transfer", "accept", "consent"):
                fail("ACTION_NOT_ALLOWED")
            now = tick_value(args["tick"])
            bound = {k: v for k, v in args.items() if k != "tick"}
            def authorized():
                previous = self.db.execute("SELECT request_sha256 FROM authorizations WHERE action_id=? LIMIT 1", (args["action_id"],)).fetchone()
                if previous and previous[0] != digest(bound):
                    fail("IDEMPOTENCY_CONFLICT", args["action_id"])
                agreement = self._agreement(args["agreement_id"])
                code = self._can_act(agreement, args["party_id"], args["action"], now)
                verdict = "AUTHORIZED" if code == "AUTHORIZED" else "REFUSED"
                self.db.execute("INSERT INTO authorizations(action_id,agreement_id,party_id,action,verdict,code,tick,request_sha256,policy_revision) VALUES (?,?,?,?,?,?,?,?,?)", (args["action_id"], args["agreement_id"], args["party_id"], args["action"], verdict, code, now, digest(bound), self._meta("current_policy_revision")))
                return {"verdict": verdict, "code": code, "action_id": args["action_id"], "tick": now}
            return self._transaction(operation, now, authorized)
        if operation == "charge_production":
            object_fields(args, {"agreement_id", "production_id", "lot_id", "attempt", "tick"})
            for key in ("agreement_id", "production_id", "lot_id"):
                identifier(args[key], key)
            integer(args["attempt"], "attempt", 1, self.contract["max_attempts"])
            now = tick_value(args["tick"])
            bound = {k: v for k, v in args.items() if k != "tick"}
            def charged():
                old = self.db.execute("SELECT * FROM productions WHERE production_id=?", (args["production_id"],)).fetchone()
                if old:
                    if old["request_sha256"] != digest(bound):
                        fail("IDEMPOTENCY_CONFLICT", args["production_id"])
                    return dict(old)
                agreement = self._agreement(args["agreement_id"])
                p = self._proposal(agreement["proposal_id"])["payload"]
                a = next((a for a in p["allocations"] if a["lot_id"] == args["lot_id"]), None)
                if a is None:
                    fail("ALLOCATION_COVERAGE", args["lot_id"])
                code = self._can_act(agreement, a["provider_id"], "produce", now)
                if code != "AUTHORIZED":
                    fail(code)
                if self.db.execute("SELECT 1 FROM productions WHERE agreement_id=? AND lot_id=? AND attempt=?", (agreement["agreement_id"], a["lot_id"], args["attempt"])).fetchone():
                    fail("DUPLICATE_PRODUCTION", a["lot_id"])
                if args["attempt"] == 2 and not self.db.execute("SELECT 1 FROM productions WHERE agreement_id=? AND lot_id=? AND attempt=1", (agreement["agreement_id"], a["lot_id"])).fetchone():
                    fail("INVALID_ATTEMPT", "missing first attempt")
                policies = self._policies(agreement["policy_revision"])
                pp = next(q for q in policies["providers"] if q["party_id"] == a["provider_id"])
                first = not self.db.execute("SELECT 1 FROM productions WHERE agreement_id=? AND provider_id=? AND attempt=?", (agreement["agreement_id"], a["provider_id"], args["attempt"])).fetchone()
                prefix = "" if args["attempt"] == 1 else "rework_"
                charge = pp[prefix + "unit_cost_minor"] * (a["last_unit"] - a["first_unit"] + 1) + (pp[prefix + "setup_cost_minor"] if first else 0)
                funder = policies["technical_sponsor"]["party_id"] if agreement["kind"] == "TECHNICAL" else pp["party_id"]
                hold = "TECHNICAL" if agreement["kind"] == "TECHNICAL" else "WORKING" if args["attempt"] == 1 else "REWORK_LIABILITY"
                self._transfer("production." + args["production_id"], agreement["agreement_id"], "BASE_COST" if args["attempt"] == 1 else "REWORK_COST", funder, SINK, charge, now, hold, {"lot_id": a["lot_id"], "provider_id": a["provider_id"], "attempt": args["attempt"], "setup_charged": first, "production_id": args["production_id"]})
                self.db.execute("INSERT INTO productions VALUES (?,?,?,?,?,?,?,?,?,?)", (args["production_id"], agreement["agreement_id"], a["lot_id"], a["provider_id"], args["attempt"], digest(bound), charge, now, funder, int(first)))
                return dict(self.db.execute("SELECT * FROM productions WHERE production_id=?", (args["production_id"],)).fetchone())
            return self._transaction(operation, now, charged)
        if operation == "settle":
            object_fields(args, {"agreement_id", "acceptance_ids", "tick"})
            aid, now = identifier(args["agreement_id"], "agreement_id"), tick_value(args["tick"])
            refs = _list(args["acceptance_ids"], "acceptance_ids", MAX_ITEMS)
            for ref in refs:
                identifier(ref, "acceptance_id")
            if not refs or len(set(refs)) != len(refs):
                fail("MISSING_ACCEPTANCE")
            refs = sorted(refs)
            def settled():
                agreement = self._agreement(aid)
                if agreement["status"] == "SETTLED":
                    if agreement["acceptance_ids"] != refs:
                        fail("IDEMPOTENCY_CONFLICT", "settlement acceptance")
                    return agreement
                if agreement["status"] != "ACTIVE":
                    fail("AGREEMENT_CLOSED")
                p = self._proposal(agreement["proposal_id"])["payload"]
                if len(refs) != len(p["allocations"]):
                    fail("MISSING_ACCEPTANCE")
                produced = {r[0] for r in self.db.execute("SELECT lot_id FROM productions WHERE agreement_id=?", (aid,))}
                if produced != {a["lot_id"] for a in p["allocations"]}:
                    fail("MISSING_PRODUCTION")
                policies = self._policies(agreement["policy_revision"])
                if agreement["kind"] == "TRADE":
                    buyer = policies["buyer"]["party_id"]
                    for q in agreement["pricing"]["providers"]:
                        self._transfer("settle." + aid + "." + q["party_id"], aid, "PROVIDER_PAYMENT", buyer, q["party_id"], q["promised_payment_minor"], now, "BUYER_ESCROW", {"acceptance_ids": refs})
                    self._transfer("settle." + aid + ".coordinator", aid, "COORDINATOR_PAYMENT", buyer, policies["coordinator"]["party_id"], p["coordinator_fee_minor"], now, "BUYER_ESCROW", {"acceptance_ids": refs})
                self._release_all(aid, now)
                self.db.execute("UPDATE agreements SET status='SETTLED',settled_tick=?,acceptance_ids=? WHERE agreement_id=?", (now, canonical(refs).decode(), aid))
                self._event("settlement." + aid, "RECIPIENT_ACCEPTANCE_REFERENCES", now, {"agreement_id": aid, "acceptance_ids": refs, "trust": "CONTROLLER_SUPPLIED_REQUIRES_FRESH_RECEIVER_RECONCILIATION"})
                return self._agreement(aid)
            return self._transaction(operation, now, settled)
        if operation == "cancel":
            object_fields(args, {"agreement_id", "reason", "tick"})
            aid, now = identifier(args["agreement_id"], "agreement_id"), tick_value(args["tick"])
            reason = identifier(args["reason"], "reason")
            def cancelled():
                agreement = self._agreement(aid)
                if agreement["status"] == "CANCELLED":
                    if agreement["reason"] != reason:
                        fail("IDEMPOTENCY_CONFLICT", "cancellation")
                    return agreement
                if agreement["status"] != "ACTIVE":
                    fail("AGREEMENT_CLOSED")
                p = self._proposal(agreement["proposal_id"])["payload"]
                policies = self._policies(agreement["policy_revision"])
                if agreement["kind"] == "TRADE":
                    self._transfer("cancel." + aid, aid, "CANCELLATION_PAYMENT", policies["buyer"]["party_id"], policies["coordinator"]["party_id"], p["cancellation_fee_minor"], now, "BUYER_ESCROW", {"reason": reason})
                self._release_all(aid, now)
                self.db.execute("UPDATE agreements SET status='CANCELLED',cancelled_tick=?,reason=? WHERE agreement_id=?", (now, reason, aid))
                self._event("cancelled." + aid, "CANCELLED", now, {"agreement_id": aid, "reason": reason, "incurred_costs_preserved": True})
                return self._agreement(aid)
            return self._transaction(operation, now, cancelled)
        if operation == "grant_technical":
            object_fields(args, {"proposal_id", "tick"})
            pid, now = identifier(args["proposal_id"], "proposal_id"), tick_value(args["tick"])
            aid = "technical." + pid
            identifier(aid, "technical agreement_id")
            def granted():
                old = self.db.execute("SELECT agreement_id FROM agreements WHERE proposal_id=?", (pid,)).fetchone()
                if old:
                    agreement = self._agreement(old[0])
                    if agreement["kind"] != "TECHNICAL":
                        fail("IDEMPOTENCY_CONFLICT", pid)
                    return agreement
                saved = self._proposal(pid)
                p, policies = saved["payload"], self._policies()
                if self.contract["mode"] != "technical_control" or saved["status"] != "REJECTED" or p["policy_revision"] != policies["revision"] or not policies["technical_sponsor"]["authorized"] or now >= p["expires_tick"]:
                    fail("TECHNICAL_CONTROL_FORBIDDEN")
                if self.db.execute("SELECT 1 FROM agreements WHERE status IN ('ACTIVE','SETTLED')").fetchone():
                    fail("CONTRACT_ALREADY_COMMITTED")
                quote = quote_terms(self.contract, policies, p["allocations"])
                selected = {q["party_id"] for q in quote["providers"]}
                required = [policies["coordinator"], *[q for q in policies["providers"] if q["party_id"] in selected]]
                if any(not q["technical_control_allowed"] or not self._has_consent(q["party_id"], "consent", now, policies) for q in required) or not self._has_consent(policies["buyer"]["party_id"], "consent", now, policies):
                    fail("TECHNICAL_CONTROL_FORBIDDEN")
                needed = sum(q["base_cost_minor"] + q["rework_cost_minor"] for q in quote["providers"]) + policies["coordinator"]["operating_cost_minor"]
                sponsor = policies["technical_sponsor"]["party_id"]
                if self._free(sponsor) < needed:
                    fail("INSUFFICIENT_FUNDS", sponsor)
                self.db.execute("INSERT INTO agreements VALUES (?,?,?,'ACTIVE',?,?,?,NULL,NULL,NULL,NULL,?)", (aid, pid, "TECHNICAL", saved["sha256"], policies["revision"], now, canonical(quote).decode()))
                self._hold(aid, sponsor, "TECHNICAL", needed, now)
                self._transfer("coordinate." + aid, aid, "COORDINATION_COST", sponsor, SINK, policies["coordinator"]["operating_cost_minor"], now, "TECHNICAL", {"beneficiary": policies["coordinator"]["party_id"]})
                self._event("technical." + pid, "TECHNICAL_GRANT", now, {"agreement_id": aid, "proposal_id": pid, "trade_status": saved["status"], "maximum_funding_minor": needed, "scope": "EXPLICIT_SYNTHETIC_RESEARCH_CONTROL_NOT_ACCEPTED_TRADE"})
                return self._agreement(aid)
            return self._transaction(operation, now, granted)
        if operation == "replace_policies":
            object_fields(args, {"policies", "tick"})
            policies, now = validate_policies(args["policies"]), tick_value(args["tick"])
            def replaced():
                current = self._policies()
                old = self.db.execute("SELECT sha256 FROM policy_versions WHERE revision=?", (policies["revision"],)).fetchone()
                if old:
                    if old[0] != digest(policies):
                        fail("IDEMPOTENCY_CONFLICT", "policy revision")
                    return {"revision": policies["revision"], "sha256": old[0]}
                if policies["revision"] != current["revision"] + 1:
                    fail("POLICY_REVISION_MISMATCH")
                def identity(doc):
                    return sorted([(role, doc[role]["party_id"], doc[role]["balance_minor"]) for role in ("buyer", "coordinator", "technical_sponsor")] + [("provider", p["party_id"], p["balance_minor"]) for p in doc["providers"]])
                if identity(policies) != identity(self.original_policies):
                    fail("POLICY_IDENTITY_CHANGED")
                self.db.execute("INSERT INTO policy_versions VALUES (?,?,?,?)", (policies["revision"], digest(policies), canonical(policies).decode(), now))
                self._set_meta("current_policy_revision", policies["revision"])
                self._event("policy." + str(policies["revision"]), "POLICY_REPLACED", now, {"old_revision": current["revision"], "new_revision": policies["revision"], "old_sha256": digest(current), "new_sha256": digest(policies), "accepted_terms_unchanged": True})
                return {"revision": policies["revision"], "sha256": digest(policies)}
            return self._transaction(operation, now, replaced)
        if operation == "withdraw":
            object_fields(args, {"party_id", "amount_minor", "event_id", "tick"})
            pid, eid = identifier(args["party_id"], "party_id"), identifier(args["event_id"], "event_id")
            amount, now = money(args["amount_minor"], "amount_minor"), tick_value(args["tick"])
            if pid in (SINK, OUTSIDE):
                fail("ACTION_NOT_ALLOWED")
            bound = {k: v for k, v in args.items() if k != "tick"}
            def withdrawn():
                old = self.db.execute("SELECT payload FROM events WHERE event_id=?", (eid,)).fetchone()
                if old:
                    if json.loads(old[0]) != bound:
                        fail("IDEMPOTENCY_CONFLICT", eid)
                    return {"event_id": eid, "amount_minor": amount}
                self._transfer("withdraw." + eid, None, "WITHDRAWAL", pid, OUTSIDE, amount, now)
                self._event(eid, "FUNDING_WITHDRAWN", now, bound)
                return {"event_id": eid, "amount_minor": amount}
            return self._transaction(operation, now, withdrawn)
        fail("UNSUPPORTED_OPERATION")

    def status(self):
        """Candidate-visible state, including all failed/cancelled deal costs.

        No output bytes or hidden receiver acceptance state are returned. Monetary
        summaries are conveniences; fresh verification replays underlying entries.
        """
        snap = self.snapshot()
        cancelled = {a["agreement_id"] for a in snap["agreements"] if a["status"] == "CANCELLED"}
        accounting = []
        costs = {"BASE_COST", "REWORK_COST", "COORDINATION_COST"}
        receipts = {"PROVIDER_PAYMENT", "COORDINATOR_PAYMENT", "CANCELLATION_PAYMENT"}
        for account in snap["accounts"]:
            pid = account["party_id"]
            held = sum(h["amount_minor"] for h in snap["holds"] if h["party_id"] == pid)
            incurred = sum(e["amount_minor"] for e in snap["entries"] if e["from_party"] == pid and e["kind"] in costs)
            received = sum(e["amount_minor"] for e in snap["entries"] if e["to_party"] == pid and e["kind"] in receipts)
            cancelled_cost = sum(e["amount_minor"] for e in snap["entries"] if e["from_party"] == pid and e["kind"] in costs and e["agreement_id"] in cancelled)
            compensation = sum(e["amount_minor"] for e in snap["entries"] if e["to_party"] == pid and e["kind"] == "CANCELLATION_PAYMENT")
            accounting.append({**account, "held_minor": held, "free_minor": account["balance_minor"] - held,
                "incurred_cost_minor": incurred, "received_payment_minor": received,
                "trade_cash_margin_minor": received - incurred,
                "cancelled_cost_minor": cancelled_cost, "cancellation_receipts_minor": compensation,
                "unreimbursed_cancelled_cost_minor": max(0, cancelled_cost - compensation)})
        current = next(p["payload"] for p in snap["policy_versions"] if p["revision"] == snap["metadata"]["current_policy_revision"])
        return {"schema": SERVICE_SCHEMA, "current_policies": current, "last_tick": snap["metadata"]["last_tick"],
                "proposals": [{k: p[k] for k in ("proposal_id", "status", "policy_revision", "sha256", "submitted_tick", "decision_tick", "payload")} for p in snap["proposals"]],
                "agreements": [{k: a[k] for k in ("agreement_id", "proposal_id", "kind", "status", "accepted_tick", "settled_tick", "cancelled_tick", "acceptance_ids", "reason")} for a in snap["agreements"]],
                "decisions": snap["decisions"], "productions": snap["productions"],
                "participant_accounting": accounting, "scope": "AUTHORED_SYNTHETIC_MODEL"}

    def snapshot(self):
        self.db.execute("BEGIN")
        try:
            result = {"metadata": {r["key"]: json.loads(r["value"]) for r in self.db.execute("SELECT * FROM metadata ORDER BY key")}}
            for table, ordering in (("policy_versions", "revision"), ("proposals", "proposal_id"), ("decisions", "sequence"), ("agreements", "agreement_id"), ("accounts", "party_id"), ("holds", "hold_id"), ("entries", "sequence"), ("productions", "production_id"), ("authorizations", "sequence"), ("events", "sequence")):
                result[table] = [dict(r) for r in self.db.execute("SELECT * FROM " + table + " ORDER BY " + ordering)]
            for table, fields in (("policy_versions", ("payload",)), ("proposals", ("payload",)), ("decisions", ("detail",)), ("agreements", ("pricing", "acceptance_ids")), ("entries", ("detail",)), ("events", ("payload",))):
                for row in result[table]:
                    for field in fields:
                        if row[field] is not None:
                            row[field] = json.loads(row[field])
            self.db.commit()
            return result
        except BaseException:
            if self.db.in_transaction:
                self.db.rollback()
            raise


OPERATIONS = ("init", "propose", "decide", "authorize", "charge_production", "settle", "cancel", "grant_technical", "replace_policies", "withdraw")
HOOKS = {op + suffix for op in OPERATIONS for suffix in (".before_begin", ".after_begin", ".before_commit", ".after_commit")}


def emit(value):
    sys.stdout.buffer.write(canonical(value) + b"\n")
    sys.stdout.buffer.flush()


def serve(service):
    while True:
        raw = sys.stdin.buffer.readline(MAX_JSON_BYTES + 1)
        if not raw:
            return
        rid = None
        try:
            request = strict_loads(raw)
            object_fields(request, {"id", "op", "args"}, {"hooks"}, path="request")
            rid = identifier(request["id"], "request.id")
            hooks = request.get("hooks", [])
            if type(hooks) is not list or len(hooks) > len(HOOKS) or any(type(h) is not str or h not in HOOKS for h in hooks):
                fail("INVALID_HOOK")
            def hook(name):
                if name in hooks:
                    emit({"id": rid, "event": "hook", "hook": name})
                    if strict_loads(sys.stdin.buffer.readline(MAX_JSON_BYTES + 1)) != {"continue": True}:
                        raise OSError("HOOK_INTERRUPTED")
            service.hook = hook
            result = service.dispatch(request["op"], request["args"])
            emit({"id": rid, "ok": True, "result": result})
        except ParticipantError as exc:
            emit({"id": rid, "ok": False, "code": exc.code, "detail": exc.detail, "location": exc.location})
        except HarnessError as exc:
            emit({"id": rid, "ok": False, "code": exc.code, "detail": {"en": MESSAGES[exc.code][0], "fr": MESSAGES[exc.code][1]} if exc.code in MESSAGES else {"en": exc.as_dict("en")["message"], "fr": exc.as_dict("fr")["message"]}, "location": exc.detail})
            if len(raw) > MAX_JSON_BYTES:
                return
        except (sqlite3.Error, OSError, ValueError, TypeError, KeyError, OverflowError, RecursionError) as exc:
            if service.db.in_transaction:
                service.db.rollback()
            emit({"id": rid, "ok": False, "code": "SERVICE_ERROR", "detail": {"en": MESSAGES["SERVICE_ERROR"][0], "fr": MESSAGES["SERVICE_ERROR"][1]}, "location": type(exc).__name__})


class Parser(argparse.ArgumentParser):
    def error(self, message):
        emit({"id": None, "ok": False, "code": "CLI_ARGUMENT", "detail": {"en": MESSAGES["CLI_ARGUMENT"][0], "fr": MESSAGES["CLI_ARGUMENT"][1]}})
        self.exit(2)


def main(argv=None):
    parser = Parser(description="Synthetic participant service / Service de participants synthétiques — CONTINUITY Ω / CONTINUITÉ Ω", add_help=False)
    parser.add_argument("-h", "--help", action="help",
                        help="Show this help and exit / Afficher cette aide et quitter")
    parser.add_argument("--db", required=True, help="SQLite path / Chemin SQLite")
    parser.add_argument("--contract", required=True, help="Retained contract / Contrat conservé")
    parser.add_argument("--policies", required=True, help="Retained participant policies / Politiques conservées des participants")
    options = parser.parse_args(argv)
    service = None
    try:
        service = ParticipantService(options.db, strict_load(options.contract), strict_load(options.policies))
        serve(service)
        return 0
    except (ParticipantError, HarnessError) as exc:
        detail = exc.detail if isinstance(exc, ParticipantError) else {"en": MESSAGES[exc.code][0], "fr": MESSAGES[exc.code][1]} if exc.code in MESSAGES else {"en": exc.as_dict("en")["message"], "fr": exc.as_dict("fr")["message"]}
        emit({"id": None, "ok": False, "code": exc.code, "detail": detail})
        return 2
    except (sqlite3.Error, OSError):
        emit({"id": None, "ok": False, "code": "SERVICE_START_FAILED", "detail": {"en": MESSAGES["SERVICE_START_FAILED"][0], "fr": MESSAGES["SERVICE_START_FAILED"][1]}})
        return 3
    finally:
        if service:
            service.close()


if __name__ == "__main__":
    raise SystemExit(main())
