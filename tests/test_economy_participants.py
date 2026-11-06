"""Synthetic participation, conserved funding, immutable terms and real crashes.

These tests use the preregistered authored policies. They establish local model
behavior, never voluntary real demand, payments, actual wages or profitability.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

from continuity_harness.rpc import ProcessChannel
from continuity_harness.schema import HarnessError, canonical, digest, strict_loads
from continuity_economy.policy_schema import validate_policies, validate_proposal_shape
from continuity_economy.participants import ParticipantError, ParticipantService, quote_terms
from continuity_economy.schema import lots, validate_contract


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "experiments/economy-v0.2/fixtures"


def fixture(name="primary-recovery"):
    data = json.loads((FIXTURES / (name + ".json")).read_text())
    return deepcopy(data["contract"]), deepcopy(data["policies"])


def proposal(contract, policies, pid="proposal-1", provider="PRIMARY"):
    allocations = [{**lot, "provider_id": provider, "window_id": "W0", "pay_minor": 0} for lot in lots(contract)]
    quote = quote_terms(contract, policies, allocations)
    for q in quote["providers"]:
        next(a for a in allocations if a["provider_id"] == q["party_id"])["pay_minor"] = q["minimum_payment_minor"]
    return {"schema": "continuity-economy/proposal/v1", "proposal_id": pid,
            "contract_sha256": digest(contract), "policy_revision": policies["revision"],
            "allocations": allocations, "buyer_price_minor": quote["minimum_buyer_price_minor"],
            "coordinator_fee_minor": quote["minimum_coordinator_fee_minor"],
            "rework_budget_minor": quote["rework_budget_minor"], "cancellation_fee_minor": 0,
            "expires_tick": contract["deadline_tick"] + 1}


def accept(service, terms, now=1):
    service.dispatch("propose", {"proposal": terms, "tick": now})
    return service.dispatch("decide", {"proposal_id": terms["proposal_id"], "tick": now + 1})


def produce_all(service, terms, now=10):
    for index, a in enumerate(terms["allocations"]):
        service.dispatch("charge_production", {"agreement_id": terms["proposal_id"], "production_id": "produce-" + a["lot_id"], "lot_id": a["lot_id"], "attempt": 1, "tick": now + index})


def acceptance_refs(terms):
    return ["accepted-" + a["lot_id"] for a in terms["allocations"]]


class ParticipantClient(ProcessChannel):
    def __init__(self, folder, db="participants.sqlite"):
        super().__init__([sys.executable, "-m", "continuity_economy.participants", "--db", str(folder / db),
                          "--contract", str(folder / "contract.json"), "--policies", str(folder / "policies.json")],
                         ROOT, folder / "participants.stderr", timeout_ms=10000)
        self.counter = 0

    def start(self, op, args=None, hooks=None):
        self.counter += 1
        rid = "request-" + str(self.counter)
        msg = {"id": rid, "op": op, "args": args or {}}
        if hooks:
            msg["hooks"] = hooks
        self.send(msg)
        return rid

    def call(self, op, args=None):
        rid = self.start(op, args)
        result = self.receive()
        if result.get("id") != rid:
            raise AssertionError(result)
        return result


class ParticipantPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.contract, self.policies = fixture()
        self.service = None

    def tearDown(self):
        if self.service:
            self.service.close()
        self.temp.cleanup()

    def open_service(self):
        self.service = ParticipantService(self.folder / "participants.sqlite", self.contract, self.policies)
        return self.service

    def assert_conserved(self):
        snap = self.service.snapshot()
        self.assertEqual(sum(a["balance_minor"] for a in snap["accounts"]), snap["metadata"]["initial_total_minor"])
        for a in snap["accounts"]:
            held = sum(h["amount_minor"] for h in snap["holds"] if h["party_id"] == a["party_id"])
            self.assertGreaterEqual(a["balance_minor"], held)
            self.assertGreaterEqual(held, 0)
        return snap

    def test_all_registered_policies_and_global_contracts_validate(self):
        for path in FIXTURES.glob("*.json"):
            with self.subTest(fixture=path.name):
                item = json.loads(path.read_text())
                validate_contract(item["contract"])
                validate_policies(item["policies"])

    def test_strict_money_and_policy_fields_before_database_creation(self):
        for bad in (True, False, "100", 1.5, None, -1, 1_000_000_001):
            with self.subTest(bad=bad):
                changed = deepcopy(self.policies)
                changed["buyer"]["balance_minor"] = bad
                path = self.folder / "must-not-exist.sqlite"
                with self.assertRaises(HarnessError):
                    ParticipantService(path, self.contract, changed)
                self.assertFalse(path.exists())
        for field in ("unknown", "accept_my_proposal"):
            changed = deepcopy(self.policies); changed[field] = True
            with self.assertRaises(HarnessError):
                validate_policies(changed)
        changed = deepcopy(self.policies); changed["buyer"]["value_min_minor"] = changed["buyer"]["value_max_minor"] + 1
        with self.assertRaises(HarnessError):
            validate_policies(changed)

    def test_policy_currency_version_and_duplicate_identities_are_refused(self):
        for change in (lambda p: p.update(schema="continuity-economy/policies/v99"),
                       lambda p: p.update(currency="USD"),
                       lambda p: p["providers"][0].update(party_id="BUYER"),
                       lambda p: p["coordinator"].update(party_id="COST_SINK")):
            p = deepcopy(self.policies); change(p)
            with self.assertRaises(HarnessError):
                validate_policies(p)

    def test_proposal_and_independent_decision_are_distinct(self):
        s = self.open_service(); p = proposal(self.contract, self.policies)
        result = s.dispatch("propose", {"proposal": p, "tick": 1})
        self.assertEqual(result["proposal"]["status"], "PROPOSED")
        self.assertIsNone(result["agreement"])
        self.assertEqual(s.snapshot()["holds"], [])
        result = s.dispatch("decide", {"proposal_id": p["proposal_id"], "tick": 2})
        self.assertEqual(result["proposal"]["status"], "ACCEPTED")
        self.assertEqual({d["role"] for d in result["decisions"]}, {"buyer", "provider", "coordinator"})
        self.assertTrue(all(d["verdict"] == "ACCEPTED" for d in result["decisions"]))
        self.assertEqual(result["agreement"]["terms_sha256"], digest(p))
        self.assert_conserved()

    def test_idempotent_proposal_and_decision_do_not_repeat_holds_or_costs(self):
        s = self.open_service(); p = proposal(self.contract, self.policies); accept(s, p)
        before = s.snapshot()
        s.dispatch("propose", {"proposal": p, "tick": 3})
        s.dispatch("decide", {"proposal_id": p["proposal_id"], "tick": 4})
        after = s.snapshot()
        for table in ("holds", "entries", "decisions", "accounts", "agreements"):
            self.assertEqual(before[table], after[table])
        changed = deepcopy(p); changed["coordinator_fee_minor"] += 1; changed["buyer_price_minor"] += 1
        with self.assertRaisesRegex(ParticipantError, "IDEMPOTENCY_CONFLICT"):
            s.dispatch("propose", {"proposal": changed, "tick": 5})

    def test_wrong_metadata_and_unit_coverage_are_refused_before_proposal(self):
        s = self.open_service(); base = proposal(self.contract, self.policies)
        changes = [lambda p: p.update(contract_sha256="0" * 64),
                   lambda p: p["allocations"].pop(),
                   lambda p: p["allocations"].append(deepcopy(p["allocations"][0])),
                   lambda p: p["allocations"][0].update(last_unit=499),
                   lambda p: p["allocations"][0].update(obligation_id="DL-300"),
                   lambda p: p["allocations"][0].update(lot_id="different-lot"),
                   lambda p: p["allocations"][0].update(provider_id="UNAUTHORIZED"),
                   lambda p: p["allocations"][0].update(pay_minor=True),
                   lambda p: p.update(buyer_price_minor="4400"),
                   lambda p: p.update(proposal_id="x" * 75),
                   lambda p: p.update(unknown=True)]
        for change in changes:
            p = deepcopy(base); change(p)
            with self.assertRaises((ParticipantError, HarnessError)):
                s.dispatch("propose", {"proposal": p, "tick": 1})
            self.assertEqual(s.snapshot()["proposals"], [])
        self.assert_conserved()

    def test_fixed_lots_do_not_introduce_unpermitted_splitting(self):
        self.contract["allow_split"] = False
        self.contract["lot_size"] = 500
        s = self.open_service(); p = proposal(self.contract, self.policies)
        self.assertEqual(len(p["allocations"]), 2)
        self.assertEqual([a["last_unit"] for a in p["allocations"]], [1100, 800])
        self.assertEqual(accept(s, p)["proposal"]["status"], "ACCEPTED")

    def test_buyer_outside_option_rejection_is_retained_without_spending(self):
        self.policies["buyer"]["outside_utility_minor"] = 30000
        s = self.open_service(); p = proposal(self.contract, self.policies)
        r = accept(s, p)
        self.assertEqual(r["proposal"]["status"], "REJECTED")
        buyer = next(d for d in r["decisions"] if d["role"] == "buyer")
        self.assertEqual(buyer["code"], "BUYER_OUTSIDE_OPTION")
        self.assertEqual(s.snapshot()["holds"], [])
        self.assertEqual(s.snapshot()["entries"], [])
        self.assert_conserved()

    def test_uncertain_value_reports_region_without_cherry_picked_acceptance(self):
        p = proposal(self.contract, self.policies)
        threshold = p["buyer_price_minor"] + self.policies["buyer"]["outside_utility_minor"]
        self.policies["buyer"]["value_min_minor"] = threshold - 1
        self.policies["buyer"]["value_max_minor"] = threshold + 1
        s = self.open_service(); r = accept(s, proposal(self.contract, self.policies))
        self.assertEqual(r["proposal"]["status"], "NOT_ESTABLISHED")
        buyer = next(d for d in r["decisions"] if d["role"] == "buyer")
        self.assertEqual(buyer["code"], "UNCERTAIN_BUYER_VALUE")
        self.assertEqual(buyer["detail"]["required_value_minor"], threshold)
        self.assertEqual(s.snapshot()["holds"], [])

    def test_provider_and_coordinator_outside_options_are_explicit(self):
        self.policies["providers"][0]["outside_profit_minor"] = 300
        self.policies["coordinator"]["outside_profit_minor"] = 400
        s = self.open_service(); p = proposal(self.contract, self.policies)
        q = quote_terms(self.contract, self.policies, p["allocations"])
        self.assertEqual(q["providers"][0]["participation_profit_minor"], 300)
        self.assertEqual(q["minimum_coordinator_fee_minor"], 600)
        p["allocations"][0]["pay_minor"] -= 1; p["buyer_price_minor"] -= 1
        r = accept(s, p)
        self.assertEqual(next(d for d in r["decisions"] if d["role"] == "provider")["code"], "PROVIDER_PARTICIPATION")
        p2 = proposal(self.contract, self.policies, "proposal-2")
        p2["coordinator_fee_minor"] -= 1; p2["buyer_price_minor"] -= 1
        r = accept(s, p2, 4)
        self.assertEqual(next(d for d in r["decisions"] if d["role"] == "coordinator")["code"], "COORDINATOR_PARTICIPATION")

    def test_prices_and_liabilities_changed_after_proposal_require_new_consent(self):
        s = self.open_service(); p = proposal(self.contract, self.policies)
        s.dispatch("propose", {"proposal": p, "tick": 1})
        changed = deepcopy(self.policies); changed["revision"] = 2
        changed["providers"][0]["unit_cost_minor"] += 1
        changed["providers"][0]["liability_limit_minor"] = 1
        s.dispatch("replace_policies", {"policies": changed, "tick": 2})
        r = s.dispatch("decide", {"proposal_id": p["proposal_id"], "tick": 3})
        self.assertEqual(r["proposal"]["status"], "REJECTED")
        self.assertTrue(all(d["code"] == "POLICY_REVISION_MISMATCH" for d in r["decisions"]))
        p2 = proposal(self.contract, changed, "proposal-2")
        r = accept(s, p2, 4)
        self.assertEqual(next(d for d in r["decisions"] if d["role"] == "provider")["code"], "LIABILITY_LIMIT")
        snap = s.snapshot()
        self.assertEqual(len(snap["policy_versions"]), 2)
        self.assertEqual(snap["proposals"][0]["payload"], p)
        self.assertEqual(snap["holds"], [])

    def test_funding_change_after_proposal_rejects_without_negative_balance(self):
        s = self.open_service(); p = proposal(self.contract, self.policies)
        s.dispatch("propose", {"proposal": p, "tick": 1})
        change = {"party_id": "BUYER", "amount_minor": 30000, "event_id": "withdrawal-1", "tick": 2}
        s.dispatch("withdraw", change)
        r = s.dispatch("decide", {"proposal_id": p["proposal_id"], "tick": 3})
        self.assertEqual(next(d for d in r["decisions"] if d["role"] == "buyer")["code"], "INSUFFICIENT_FUNDS")
        before = s.snapshot()
        s.dispatch("withdraw", {**change, "tick": 4})
        self.assertEqual(before["accounts"], s.snapshot()["accounts"])
        self.assertEqual(before["entries"], s.snapshot()["entries"])
        self.assert_conserved()

    def test_accepted_escrow_cannot_be_withdrawn_or_counted_twice(self):
        s = self.open_service(); p = proposal(self.contract, self.policies); accept(s, p)
        before = s.snapshot()
        with self.assertRaisesRegex(ParticipantError, "INSUFFICIENT_FUNDS"):
            s.dispatch("withdraw", {"party_id": "BUYER", "amount_minor": 30000 - p["buyer_price_minor"] + 1, "event_id": "withdraw-reserved", "tick": 3})
        self.assertEqual(before["accounts"], s.snapshot()["accounts"])
        second = proposal(self.contract, self.policies, "proposal-2")
        r = accept(s, second, 4)
        self.assertEqual(r["proposal"]["status"], "REJECTED")
        self.assertTrue(all(d["code"] == "CONTRACT_ALREADY_COMMITTED" for d in r["decisions"]))
        self.assert_conserved()

    def test_actual_costs_and_unused_correction_holds_stay_distinct(self):
        s = self.open_service(); p = proposal(self.contract, self.policies); accept(s, p)
        produce_all(s, p)
        r = s.dispatch("settle", {"agreement_id": p["proposal_id"], "acceptance_ids": acceptance_refs(p), "tick": 30})
        self.assertEqual(r["status"], "SETTLED")
        snap = self.assert_conserved()
        provider = next(a for a in snap["accounts"] if a["party_id"] == "PRIMARY")
        self.assertEqual(provider["balance_minor"] - provider["initial_balance_minor"], 2100)
        costs = sum(e["amount_minor"] for e in snap["entries"] if e["kind"] == "BASE_COST")
        self.assertEqual(costs, 2000)
        self.assertEqual(sum(e["amount_minor"] for e in snap["entries"] if e["kind"] == "REWORK_COST"), 0)
        self.assertEqual(sum(e["amount_minor"] for e in snap["entries"] if e["kind"] == "RELEASE" and e["hold_kind"] == "REWORK_LIABILITY"), 2000)
        self.assertTrue(all(h["amount_minor"] == 0 for h in snap["holds"]))
        self.assertEqual(len([e for e in snap["entries"] if e["kind"] == "PROVIDER_PAYMENT"]), 1)

    def test_correction_cost_and_setup_once_per_provider_are_accounted(self):
        s = self.open_service(); p = proposal(self.contract, self.policies); accept(s, p); produce_all(s, p)
        for n, a in enumerate(p["allocations"][:2]):
            r = s.dispatch("charge_production", {"agreement_id": p["proposal_id"], "production_id": "repair-" + a["lot_id"], "lot_id": a["lot_id"], "attempt": 2, "tick": 20 + n})
            self.assertEqual(r["charge_minor"], 600 if n == 0 else 500)
            self.assertEqual(r["setup_charged"], 1 if n == 0 else 0)
        s.dispatch("settle", {"agreement_id": p["proposal_id"], "acceptance_ids": acceptance_refs(p), "tick": 30})
        snap = self.assert_conserved()
        self.assertEqual(sum(e["amount_minor"] for e in snap["entries"] if e["kind"] == "REWORK_COST"), 1100)
        self.assertEqual(sum(e["amount_minor"] for e in snap["entries"] if e["kind"] == "RELEASE" and e["hold_kind"] == "REWORK_LIABILITY"), 900)

    def test_retry_and_conflicting_production_ids_do_not_duplicate_costs(self):
        s = self.open_service(); p = proposal(self.contract, self.policies); accept(s, p)
        a = p["allocations"][0]
        action = {"agreement_id": p["proposal_id"], "production_id": "stable-production", "lot_id": a["lot_id"], "attempt": 1, "tick": 3}
        first = s.dispatch("charge_production", action)
        repeated = s.dispatch("charge_production", {**action, "tick": 4})
        self.assertEqual(first, repeated)
        for change, code in (({"lot_id": p["allocations"][1]["lot_id"]}, "IDEMPOTENCY_CONFLICT"), ({"production_id": "duplicate-production"}, "DUPLICATE_PRODUCTION")):
            with self.assertRaisesRegex(ParticipantError, code):
                s.dispatch("charge_production", {**action, **change, "tick": 5})
        with self.assertRaisesRegex(ParticipantError, "INVALID_ATTEMPT"):
            s.dispatch("charge_production", {**action, "lot_id": p["allocations"][1]["lot_id"], "production_id": "premature-repair", "attempt": 2, "tick": 5})
        self.assertEqual(len(self.assert_conserved()["productions"]), 1)

    def test_cancel_preserves_failed_costs_and_new_deal_exposes_campaign_effort(self):
        s = self.open_service(); p = proposal(self.contract, self.policies); accept(s, p)
        a = p["allocations"][0]
        s.dispatch("charge_production", {"agreement_id": p["proposal_id"], "production_id": "failed-first", "lot_id": a["lot_id"], "attempt": 1, "tick": 3})
        s.dispatch("cancel", {"agreement_id": p["proposal_id"], "reason": "PROVIDER_FAILURE", "tick": 4})
        status = s.status()
        coordinator = next(a for a in status["participant_accounting"] if a["party_id"] == "COORDINATOR")
        provider = next(a for a in status["participant_accounting"] if a["party_id"] == "PRIMARY")
        self.assertEqual(coordinator["unreimbursed_cancelled_cost_minor"], 200)
        self.assertEqual(provider["unreimbursed_cancelled_cost_minor"], 600)
        self.assertEqual(provider["held_minor"], 0)
        p2 = proposal(self.contract, self.policies, "proposal-2")
        p2["coordinator_fee_minor"] += 200; p2["buyer_price_minor"] += 200
        self.assertEqual(accept(s, p2, 5)["proposal"]["status"], "ACCEPTED")
        produce_all(s, p2, 10)
        s.dispatch("settle", {"agreement_id": p2["proposal_id"], "acceptance_ids": acceptance_refs(p2), "tick": 30})
        coordinator = next(a for a in s.status()["participant_accounting"] if a["party_id"] == "COORDINATOR")
        self.assertEqual(coordinator["incurred_cost_minor"], 400)
        self.assertEqual(coordinator["trade_cash_margin_minor"], 100)
        self.assertEqual(len(s.snapshot()["proposals"]), 2)
        self.assert_conserved()

    def test_cancel_and_settlement_are_idempotent_and_keep_closed_state(self):
        s = self.open_service(); p = proposal(self.contract, self.policies); accept(s, p)
        first = s.dispatch("cancel", {"agreement_id": p["proposal_id"], "reason": "NO_DELIVERY", "tick": 3})
        before = s.snapshot()
        again = s.dispatch("cancel", {"agreement_id": p["proposal_id"], "reason": "NO_DELIVERY", "tick": 4})
        self.assertEqual(first, again)
        self.assertEqual(before["entries"], s.snapshot()["entries"])
        with self.assertRaisesRegex(ParticipantError, "IDEMPOTENCY_CONFLICT"):
            s.dispatch("cancel", {"agreement_id": p["proposal_id"], "reason": "OTHER_REASON", "tick": 5})
        with self.assertRaisesRegex(ParticipantError, "AGREEMENT_CLOSED"):
            s.dispatch("settle", {"agreement_id": p["proposal_id"], "acceptance_ids": acceptance_refs(p), "tick": 5})

    def test_technical_completion_funding_never_accepts_a_rejected_trade(self):
        self.contract, self.policies = fixture("technical-no-trade")
        s = self.open_service(); p = proposal(self.contract, self.policies, provider="BACKUP")
        self.assertEqual(accept(s, p)["proposal"]["status"], "REJECTED")
        grant = s.dispatch("grant_technical", {"proposal_id": p["proposal_id"], "tick": 3})
        self.assertEqual(grant["kind"], "TECHNICAL")
        for n, a in enumerate(p["allocations"]):
            s.dispatch("charge_production", {"agreement_id": grant["agreement_id"], "production_id": "technical-" + a["lot_id"], "lot_id": a["lot_id"], "attempt": 1, "tick": 4 + n})
        s.dispatch("settle", {"agreement_id": grant["agreement_id"], "acceptance_ids": acceptance_refs(p), "tick": 30})
        snap = self.assert_conserved()
        self.assertEqual(snap["proposals"][0]["status"], "REJECTED")
        self.assertFalse(any(e["kind"] in ("PROVIDER_PAYMENT", "COORDINATOR_PAYMENT") for e in snap["entries"]))
        for a in snap["accounts"]:
            if a["role"] in ("buyer", "provider", "coordinator"):
                self.assertEqual(a["balance_minor"], a["initial_balance_minor"])
        sponsor = next(a for a in snap["accounts"] if a["role"] == "technical_sponsor")
        self.assertEqual(sponsor["initial_balance_minor"] - sponsor["balance_minor"], 4150)

    def test_market_cannot_turn_rejected_trade_into_technical_grant(self):
        self.policies["buyer"]["max_price_minor"] = 1
        s = self.open_service(); p = proposal(self.contract, self.policies)
        self.assertEqual(accept(s, p)["proposal"]["status"], "REJECTED")
        with self.assertRaisesRegex(ParticipantError, "TECHNICAL_CONTROL_FORBIDDEN"):
            s.dispatch("grant_technical", {"proposal_id": p["proposal_id"], "tick": 3})
        self.assertEqual(s.snapshot()["agreements"], [])

    def test_technical_control_requires_every_permission_and_funded_sponsor(self):
        for change, expected in ((lambda p: p["technical_sponsor"].update(authorized=False), "TECHNICAL_CONTROL_FORBIDDEN"),
                                 (lambda p: p["providers"][1].update(technical_control_allowed=False), "TECHNICAL_CONTROL_FORBIDDEN"),
                                 (lambda p: p["technical_sponsor"].update(balance_minor=1), "INSUFFICIENT_FUNDS")):
            c, p = fixture("technical-no-trade"); change(p)
            with tempfile.TemporaryDirectory() as d:
                s = ParticipantService(Path(d) / "p.sqlite", c, p)
                try:
                    terms = proposal(c, p, provider="BACKUP"); accept(s, terms)
                    with self.assertRaisesRegex(ParticipantError, expected):
                        s.dispatch("grant_technical", {"proposal_id": terms["proposal_id"], "tick": 3})
                    self.assertEqual(s.snapshot()["holds"], [])
                finally:
                    s.close()

    def test_effective_revocation_rechecks_authorization_without_erasing_history(self):
        self.contract["revocations"] = [{"tick": 10, "party_id": "PRIMARY", "action": "consent"}]
        s = self.open_service(); p = proposal(self.contract, self.policies); accept(s, p)
        action = {"agreement_id": p["proposal_id"], "party_id": "PRIMARY", "action": "produce", "action_id": "produce-authorization", "tick": 5}
        self.assertEqual(s.dispatch("authorize", action)["verdict"], "AUTHORIZED")
        self.assertEqual(s.dispatch("authorize", {**action, "tick": 10})["code"], "CONSENT_REVOKED")
        self.assertEqual([a["verdict"] for a in s.snapshot()["authorizations"]], ["AUTHORIZED", "REFUSED"])
        with self.assertRaisesRegex(ParticipantError, "CONSENT_REVOKED"):
            s.dispatch("charge_production", {"agreement_id": p["proposal_id"], "production_id": "late-production", "lot_id": p["allocations"][0]["lot_id"], "attempt": 1, "tick": 10})
        self.assertEqual(s.snapshot()["productions"], [])

    def test_transfer_and_recipient_consent_revocation_have_exact_effective_tick(self):
        self.contract["revocations"] = [{"tick": 10, "party_id": "PRIMARY", "action": "transfer"}, {"tick": 12, "party_id": "BUYER", "action": "accept"}]
        s = self.open_service(); p = proposal(self.contract, self.policies); accept(s, p)
        def auth(party, action, tick):
            return s.dispatch("authorize", {"agreement_id": p["proposal_id"], "party_id": party, "action": action, "action_id": action + "-" + str(tick), "tick": tick})
        self.assertEqual(auth("PRIMARY", "transfer", 9)["verdict"], "AUTHORIZED")
        self.assertEqual(auth("PRIMARY", "transfer", 10)["code"], "CONSENT_REVOKED")
        self.assertEqual(auth("BUYER", "accept", 11)["verdict"], "AUTHORIZED")
        self.assertEqual(auth("BUYER", "accept", 12)["code"], "CONSENT_REVOKED")

    def test_primary_does_not_need_external_disclosure_backup_does(self):
        self.contract["providers"][0]["permissions"]["disclosure"] = False
        self.contract["providers"][1]["permissions"]["disclosure"] = False
        s = self.open_service(); primary = proposal(self.contract, self.policies)
        self.assertEqual(accept(s, primary)["proposal"]["status"], "ACCEPTED")
        auth = s.dispatch("authorize", {"agreement_id": primary["proposal_id"], "party_id": "PRIMARY", "action": "transfer", "action_id": "internal-delivery", "tick": 3})
        self.assertEqual(auth["verdict"], "AUTHORIZED")
        s.dispatch("cancel", {"agreement_id": primary["proposal_id"], "reason": "TEST_BOUNDARY", "tick": 4})
        backup = proposal(self.contract, self.policies, "backup-proposal", "BACKUP")
        r = accept(s, backup, 5)
        self.assertEqual(r["proposal"]["status"], "REJECTED")
        self.assertEqual(next(d for d in r["decisions"] if d["role"] == "provider")["code"], "ACTION_NOT_ALLOWED")

    def test_already_accrued_payment_survives_later_revocation(self):
        self.contract["revocations"] = [{"tick": 25, "party_id": "BUYER", "action": "consent"}]
        s = self.open_service(); p = proposal(self.contract, self.policies); accept(s, p); produce_all(s, p)
        result = s.dispatch("settle", {"agreement_id": p["proposal_id"], "acceptance_ids": acceptance_refs(p), "tick": 30})
        self.assertEqual(result["status"], "SETTLED")
        before = s.snapshot()
        self.assertEqual(s.dispatch("settle", {"agreement_id": p["proposal_id"], "acceptance_ids": acceptance_refs(p), "tick": 31}), result)
        self.assertEqual(before["entries"], s.snapshot()["entries"])
        changed = acceptance_refs(p); changed[0] = "replayed-other-acceptance"
        with self.assertRaisesRegex(ParticipantError, "IDEMPOTENCY_CONFLICT"):
            s.dispatch("settle", {"agreement_id": p["proposal_id"], "acceptance_ids": changed, "tick": 32})

    def test_accepted_terms_do_not_reprice_old_work_after_policy_change(self):
        s = self.open_service(); p = proposal(self.contract, self.policies); accept(s, p)
        changed = deepcopy(self.policies); changed["revision"] = 2
        changed["providers"][0]["unit_cost_minor"] = 10
        changed["providers"][0]["liability_limit_minor"] = 0
        s.dispatch("replace_policies", {"policies": changed, "tick": 3})
        produce_all(s, p)
        s.dispatch("settle", {"agreement_id": p["proposal_id"], "acceptance_ids": acceptance_refs(p), "tick": 30})
        snap = self.assert_conserved()
        self.assertEqual(sum(e["amount_minor"] for e in snap["entries"] if e["kind"] == "BASE_COST"), 2000)
        self.assertEqual(sum(e["amount_minor"] for e in snap["entries"] if e["kind"] == "PROVIDER_PAYMENT"), 4100)
        self.assertEqual(snap["agreements"][0]["policy_revision"], 1)
        self.assertEqual(snap["metadata"]["current_policy_revision"], 2)

    def test_settlement_requires_every_lot_and_charged_production(self):
        s = self.open_service(); p = proposal(self.contract, self.policies); accept(s, p)
        with self.assertRaisesRegex(ParticipantError, "MISSING_ACCEPTANCE"):
            s.dispatch("settle", {"agreement_id": p["proposal_id"], "acceptance_ids": ["one", "two"], "tick": 3})
        with self.assertRaisesRegex(ParticipantError, "MISSING_PRODUCTION"):
            s.dispatch("settle", {"agreement_id": p["proposal_id"], "acceptance_ids": acceptance_refs(p), "tick": 3})
        refs = acceptance_refs(p); refs[-1] = refs[0]
        with self.assertRaisesRegex(ParticipantError, "MISSING_ACCEPTANCE"):
            s.dispatch("settle", {"agreement_id": p["proposal_id"], "acceptance_ids": refs, "tick": 3})
        self.assertFalse(any(e["kind"] == "PROVIDER_PAYMENT" for e in s.snapshot()["entries"]))

    def test_deadline_boundary_offer_expiry_and_clock_regression(self):
        s = self.open_service(); p = proposal(self.contract, self.policies); accept(s, p)
        args = {"agreement_id": p["proposal_id"], "party_id": "PRIMARY", "action": "produce", "action_id": "at-deadline", "tick": 500}
        self.assertEqual(s.dispatch("authorize", args)["verdict"], "AUTHORIZED")
        self.assertEqual(s.dispatch("authorize", {**args, "action_id": "after-deadline", "tick": 501})["code"], "PROPOSAL_EXPIRED")
        with self.assertRaisesRegex(ParticipantError, "CLOCK_REGRESSION"):
            s.dispatch("authorize", {**args, "action_id": "backwards", "tick": 499})

    def test_offer_expiry_is_exclusive_and_preserves_rejected_decision(self):
        s = self.open_service(); p = proposal(self.contract, self.policies); p["expires_tick"] = 2
        result = accept(s, p)
        self.assertEqual(result["proposal"]["status"], "REJECTED")
        self.assertTrue(all(d["code"] == "PROPOSAL_EXPIRED" for d in result["decisions"]))
        self.assertEqual(s.snapshot()["holds"], [])

    def test_policy_replacement_cannot_reset_balances_or_identities(self):
        s = self.open_service()
        for change in (lambda p: p["buyer"].update(balance_minor=999999), lambda p: p["coordinator"].update(party_id="NEW-COORDINATOR")):
            p = deepcopy(self.policies); p["revision"] = 2; change(p)
            with self.assertRaisesRegex(ParticipantError, "POLICY_IDENTITY_CHANGED"):
                s.dispatch("replace_policies", {"policies": p, "tick": 1})
            self.assertEqual(len(s.snapshot()["policy_versions"]), 1)

    def test_symlink_database_and_changed_restart_authority_are_refused(self):
        target = self.folder / "target.sqlite"; target.write_bytes(b"unrelated")
        link = self.folder / "link.sqlite"; link.symlink_to(target)
        with self.assertRaisesRegex(ParticipantError, "UNSAFE_PATH"):
            ParticipantService(link, self.contract, self.policies)
        self.assertEqual(target.read_bytes(), b"unrelated")
        s = self.open_service(); s.close(); self.service = None
        changed = deepcopy(self.policies); changed["buyer"]["value_min_minor"] -= 1
        with self.assertRaisesRegex(ParticipantError, "CONTRACT_MISMATCH"):
            ParticipantService(self.folder / "participants.sqlite", self.contract, changed)


class ParticipantProcessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.contract, self.policies = fixture()
        (self.folder / "contract.json").write_bytes(canonical(self.contract))
        (self.folder / "policies.json").write_bytes(canonical(self.policies))
        self.clients = []

    def tearDown(self):
        for c in reversed(self.clients):
            try:
                c.close()
            except (OSError, ValueError):
                pass
        self.temp.cleanup()

    def client(self):
        c = ParticipantClient(self.folder); self.clients.append(c)
        self.assertTrue(c.call("ping")["ok"])
        return c

    def prepare(self, c, terms):
        self.assertTrue(c.call("propose", {"proposal": terms, "tick": 1})["ok"])

    def accept(self, c, terms):
        self.prepare(c, terms)
        r = c.call("decide", {"proposal_id": terms["proposal_id"], "tick": 2})
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["result"]["proposal"]["status"], "ACCEPTED")

    def test_real_process_rejects_duplicate_keys_and_boolean_money_bilingually(self):
        c = self.client()
        raw = b'{"id":"duplicate","op":"ping","args":{},"args":{}}\n'
        os.write(c.process.stdin.fileno(), raw)
        result = c.receive()
        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], "DUPLICATE_KEY")
        self.assertNotEqual(result["detail"]["en"], result["detail"]["fr"])
        p = proposal(self.contract, self.policies); p["buyer_price_minor"] = True
        result = c.call("propose", {"proposal": p, "tick": 1})
        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], "INVALID_TYPE")
        snap = c.call("snapshot")["result"]
        self.assertEqual(snap["proposals"], [])
        self.assertEqual(snap["entries"], [])

    def test_crash_before_decision_commit_rolls_back_all_decisions_and_holds(self):
        c = self.client(); p = proposal(self.contract, self.policies); self.prepare(c, p)
        c.start("decide", {"proposal_id": p["proposal_id"], "tick": 2}, ["decide.before_commit"])
        self.assertEqual(c.receive()["hook"], "decide.before_commit")
        c.kill()
        restarted = self.client(); snap = restarted.call("snapshot")["result"]
        self.assertEqual(snap["proposals"][0]["status"], "PROPOSED")
        self.assertEqual(snap["decisions"], []); self.assertEqual(snap["holds"], []); self.assertEqual(snap["entries"], [])
        self.assertEqual(restarted.call("decide", {"proposal_id": p["proposal_id"], "tick": 3})["result"]["proposal"]["status"], "ACCEPTED")

    def test_lost_decision_ack_after_commit_reconciles_without_recharging(self):
        c = self.client(); p = proposal(self.contract, self.policies); self.prepare(c, p)
        c.start("decide", {"proposal_id": p["proposal_id"], "tick": 2}, ["decide.after_commit"])
        self.assertEqual(c.receive()["hook"], "decide.after_commit"); c.kill()
        restarted = self.client(); before = restarted.call("snapshot")["result"]
        result = restarted.call("decide", {"proposal_id": p["proposal_id"], "tick": 3})
        self.assertEqual(result["result"]["proposal"]["status"], "ACCEPTED")
        after = restarted.call("snapshot")["result"]
        for table in ("decisions", "holds", "entries", "accounts"):
            self.assertEqual(before[table], after[table])

    def test_production_charge_crash_before_and_after_commit_is_not_double_spent(self):
        c = self.client(); p = proposal(self.contract, self.policies); self.accept(c, p)
        args = {"agreement_id": p["proposal_id"], "production_id": "production-1", "lot_id": p["allocations"][0]["lot_id"], "attempt": 1, "tick": 3}
        c.start("charge_production", args, ["charge_production.before_commit"])
        self.assertEqual(c.receive()["hook"], "charge_production.before_commit"); c.kill()
        restarted = self.client()
        self.assertEqual(restarted.call("snapshot")["result"]["productions"], [])
        restarted.start("charge_production", {**args, "tick": 4}, ["charge_production.after_commit"])
        self.assertEqual(restarted.receive()["hook"], "charge_production.after_commit"); restarted.kill()
        final = self.client(); before = final.call("snapshot")["result"]
        result = final.call("charge_production", {**args, "tick": 5})
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["result"]["charge_minor"], 600)
        after = final.call("snapshot")["result"]
        self.assertEqual(before["accounts"], after["accounts"])
        self.assertEqual(before["entries"], after["entries"])
        self.assertEqual(len(after["productions"]), 1)

    def test_lost_settlement_ack_after_commit_cannot_duplicate_payment(self):
        c = self.client(); p = proposal(self.contract, self.policies); self.accept(c, p)
        for i, a in enumerate(p["allocations"]):
            self.assertTrue(c.call("charge_production", {"agreement_id": p["proposal_id"], "production_id": "produce-" + a["lot_id"], "lot_id": a["lot_id"], "attempt": 1, "tick": 10 + i})["ok"])
        args = {"agreement_id": p["proposal_id"], "acceptance_ids": acceptance_refs(p), "tick": 30}
        c.start("settle", args, ["settle.after_commit"])
        self.assertEqual(c.receive()["hook"], "settle.after_commit"); c.kill()
        restarted = self.client(); before = restarted.call("snapshot")["result"]
        self.assertEqual(restarted.call("settle", {**args, "tick": 31})["result"]["status"], "SETTLED")
        after = restarted.call("snapshot")["result"]
        self.assertEqual(before["entries"], after["entries"])
        self.assertEqual(before["accounts"], after["accounts"])
        self.assertEqual(len([e for e in after["entries"] if e["kind"] == "PROVIDER_PAYMENT"]), 1)

    def test_two_real_processes_cannot_commit_same_funding_and_contract(self):
        a, b = self.client(), self.client()
        p1 = proposal(self.contract, self.policies, "competitor-a")
        p2 = proposal(self.contract, self.policies, "competitor-b")
        self.prepare(a, p1); self.prepare(b, p2)
        a.start("decide", {"proposal_id": p1["proposal_id"], "tick": 2}, ["decide.after_begin"])
        self.assertEqual(a.receive()["hook"], "decide.after_begin")
        b.start("decide", {"proposal_id": p2["proposal_id"], "tick": 2}, ["decide.before_begin"])
        self.assertEqual(b.receive()["hook"], "decide.before_begin")
        b.send({"continue": True})
        a.send({"continue": True})
        ra, rb = a.receive(), b.receive()
        self.assertTrue(ra["ok"], ra); self.assertTrue(rb["ok"], rb)
        self.assertEqual(ra["result"]["proposal"]["status"], "ACCEPTED")
        self.assertEqual(rb["result"]["proposal"]["status"], "REJECTED")
        self.assertTrue(all(d["code"] == "CONTRACT_ALREADY_COMMITTED" for d in rb["result"]["decisions"]))
        snap = a.call("snapshot")["result"]
        self.assertEqual(len(snap["agreements"]), 1)
        buyer_holds = [h for h in snap["holds"] if h["kind"] == "BUYER_ESCROW"]
        self.assertEqual(len(buyer_holds), 1)
        self.assertEqual(buyer_holds[0]["amount_minor"], p1["buyer_price_minor"])

    def test_concurrent_identical_cost_request_reconciles_one_durable_charge(self):
        a, b = self.client(), self.client(); p = proposal(self.contract, self.policies); self.accept(a, p)
        args = {"agreement_id": p["proposal_id"], "production_id": "shared-production", "lot_id": p["allocations"][0]["lot_id"], "attempt": 1, "tick": 3}
        a.start("charge_production", args, ["charge_production.after_begin"])
        self.assertEqual(a.receive()["hook"], "charge_production.after_begin")
        b.start("charge_production", args, ["charge_production.before_begin"])
        self.assertEqual(b.receive()["hook"], "charge_production.before_begin")
        b.send({"continue": True}); a.send({"continue": True})
        ra, rb = a.receive(), b.receive()
        self.assertTrue(ra["ok"], ra); self.assertTrue(rb["ok"], rb)
        self.assertEqual(ra["result"], rb["result"])
        snap = a.call("snapshot")["result"]
        self.assertEqual(len(snap["productions"]), 1)
        self.assertEqual(len([e for e in snap["entries"] if e["kind"] == "BASE_COST"]), 1)


if __name__ == "__main__":
    unittest.main()
