"""Optimality/equal-information controls for the bounded public planning domain."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from continuity_economy.fixtures import fixture_names,load_fixture
from continuity_economy.planning import choose_plan,make_proposal
from continuity_economy.participants import ParticipantService,quote_terms
from continuity_economy.schema import digest,validate_contract,HarnessError,lots
from continuity_economy.adapters import LocalAIAdapter


def state(name="primary-recovery"):
    f=load_fixture(name)
    return {"contract":f["contract"],"policies":f["policies"],"tick":0,
            "blocked_dependencies":f["contract"]["blocked_dependencies"],"catalog":{"participant_accounting":[]}}


class PlanningTests(unittest.TestCase):
    def independent_decision(self, s, plan):
        with tempfile.TemporaryDirectory() as folder:
            service=ParticipantService(Path(folder)/"participants.sqlite",s["contract"],s["policies"])
            try:
                proposal=make_proposal(s,plan,1)
                service.dispatch("propose",{"proposal":proposal,"tick":1})
                return service.dispatch("decide",{"proposal_id":proposal["proposal_id"],"tick":2})
            finally:
                service.close()

    def test_all_registered_inputs_are_strictly_valid_and_hashed(self):
        self.assertEqual(len(fixture_names()),7)
        for name in fixture_names():
            with self.subTest(name=name): validate_contract(load_fixture(name)["contract"])

    def test_two_algorithms_choose_same_minimum_in_registered_domain(self):
        for name in fixture_names():
            s=state(name)
            a,b=choose_plan(s,"conventional"),choose_plan(s,"harness")
            with self.subTest(name=name):
                self.assertEqual(a["plan"],b["plan"])
                self.assertTrue(a["search"]["exhaustive_within_declared_domain"])
                self.assertTrue(b["search"]["exhaustive_within_declared_domain"])

    def test_primary_price_is_complete_tariff_not_selected_success_only(self):
        s=state(); p=choose_plan(s)["plan"]
        self.assertEqual({a["provider_id"] for a in p["allocations"]},{"PRIMARY"})
        # 1900 initial+1900 correction units, two setup budgets100, profit100,
        # coordinator cost200+outside/minimum100 =4400 authored minor units.
        self.assertEqual(p["buyer_price_minor"],4400)
        self.assertEqual(p["rework_budget_minor"],2000)
        q=quote_terms(s["contract"],s["policies"],p["allocations"])
        self.assertEqual(q["minimum_buyer_price_minor"],4400)

    def test_funded_backup_is_chosen_before_spending_one_proposal_on_insolvent_primary(self):
        for method in ("conventional","harness"):
            with self.subTest(method=method):
                s=state();s["contract"]["bounds"]["max_proposals"]=1
                next(p for p in s["policies"]["providers"] if p["party_id"]=="PRIMARY")["balance_minor"]=0
                chosen=choose_plan(s,method)
                self.assertEqual({a["provider_id"] for a in chosen["plan"]["allocations"]},{"BACKUP"})
                self.assertGreater(chosen["search"]["participant_prunes"],0)
                self.assertEqual(self.independent_decision(s,chosen["plan"])["proposal"]["status"],"ACCEPTED")

    def test_provider_liability_limit_is_screened_equally_by_both_methods(self):
        s=state()
        next(p for p in s["policies"]["providers"] if p["party_id"]=="PRIMARY")["liability_limit_minor"]=0
        conventional=choose_plan(s,"conventional")["plan"]
        harness=choose_plan(s,"harness")["plan"]
        self.assertEqual(conventional,harness)
        self.assertEqual({a["provider_id"] for a in conventional["allocations"]},{"BACKUP"})
        self.assertEqual(self.independent_decision(s,conventional)["proposal"]["status"],"ACCEPTED")

    def test_live_withdrawal_uses_current_free_funds_not_retained_starting_balance(self):
        with tempfile.TemporaryDirectory() as folder:
            s=state(); service=ParticipantService(Path(folder)/"participants.sqlite",s["contract"],s["policies"])
            try:
                primary=next(p for p in s["policies"]["providers"] if p["party_id"]=="PRIMARY")
                service.dispatch("withdraw",{"party_id":"PRIMARY","event_id":"visible-withdrawal","amount_minor":primary["balance_minor"],"tick":1})
                s["catalog"]=service.status();s["tick"]=1
                before=service.snapshot()
                for method in ("conventional","harness"):
                    chosen=choose_plan(s,method)
                    self.assertEqual(chosen["search"]["funding_basis"],"CURRENT_UNENCUMBERED_BALANCES")
                    self.assertNotIn("PRIMARY",{a["provider_id"] for a in chosen["plan"]["allocations"]})
                self.assertEqual(before,service.snapshot())
                proposal=make_proposal(s,chosen["plan"],1)
                service.dispatch("propose",{"proposal":proposal,"tick":2})
                accepted=service.dispatch("decide",{"proposal_id":proposal["proposal_id"],"tick":3})
                self.assertEqual(accepted["proposal"]["status"],"ACCEPTED")
            finally:
                service.close()

    def test_encumbered_working_capital_is_not_available_to_a_new_plan(self):
        with tempfile.TemporaryDirectory() as folder:
            s=state(); next(p for p in s["policies"]["providers"] if p["party_id"]=="PRIMARY")["balance_minor"]=4000
            service=ParticipantService(Path(folder)/"participants.sqlite",s["contract"],s["policies"])
            try:
                proposal=make_proposal(s,choose_plan(s)["plan"],1)
                service.dispatch("propose",{"proposal":proposal,"tick":1})
                service.dispatch("decide",{"proposal_id":proposal["proposal_id"],"tick":2})
                s["catalog"]=service.status();s["tick"]=2
                account=next(a for a in s["catalog"]["participant_accounting"] if a["party_id"]=="PRIMARY")
                self.assertEqual((account["balance_minor"],account["held_minor"],account["free_minor"]),(4000,4000,0))
                for method in ("conventional","harness"):
                    self.assertNotIn("PRIMARY",{a["provider_id"] for a in choose_plan(s,method)["plan"]["allocations"]})
                # The candidate separately resumes the active agreement; this
                # screen alone does not authorize a second contract commitment.
                self.assertEqual(len(service.snapshot()["agreements"]),1)
            finally:
                service.close()

    def test_funding_constraints_allow_a_feasible_split_without_discarding_provider(self):
        s=state(); next(p for p in s["policies"]["providers"] if p["party_id"]=="PRIMARY")["balance_minor"]=2500
        a,b=choose_plan(s,"conventional")["plan"],choose_plan(s,"harness")["plan"]
        self.assertEqual(a,b)
        self.assertEqual({r["provider_id"] for r in a["allocations"]},{"PRIMARY","BACKUP"})
        units=sum(r["last_unit"]-r["first_unit"]+1 for r in a["allocations"] if r["provider_id"]=="PRIMARY")
        self.assertLessEqual(2*(100+units),2500)
        self.assertEqual(self.independent_decision(s,a)["proposal"]["status"],"ACCEPTED")

    def test_coordinator_funding_and_liability_are_required_by_both_methods(self):
        for field in ("balance_minor","liability_limit_minor"):
            for method in ("conventional","harness"):
                with self.subTest(field=field,method=method):
                    s=state();s["policies"]["coordinator"][field]=199
                    chosen=choose_plan(s,method)
                    self.assertIsNone(chosen["plan"])
                    self.assertEqual(chosen["reason"],"NO_FUNDED_SERVICE_ARRANGEMENT")
                    self.assertTrue(chosen["search"]["exhaustive_within_declared_domain"])

    def test_missing_current_funding_evidence_does_not_reuse_starting_balances(self):
        s=state();s["catalog"]={"schema":"continuity-economy/participants/v1","participant_accounting":[]}
        for method in ("conventional","harness"):
            with self.subTest(method=method),self.assertRaisesRegex(HarnessError,"FUNDING_INFORMATION_MISSING"):
                choose_plan(s,method)

    def test_sponsor_can_fund_explicit_technical_control_without_pretending_trade(self):
        s=state("technical-no-trade")
        for p in s["policies"]["providers"]:p["balance_minor"]=0
        s["policies"]["coordinator"]["balance_minor"]=0
        for method in ("conventional","harness"):
            with self.subTest(method=method):
                chosen=choose_plan(s,method)
                self.assertIsNotNone(chosen["plan"])
                decision=self.independent_decision(s,chosen["plan"])
                self.assertEqual(decision["proposal"]["status"],"REJECTED")

    def test_buyer_uncertainty_and_outside_option_remain_independent_decisions(self):
        for name,expected in (("technical-no-trade","REJECTED"),("uncertain-value","NOT_ESTABLISHED")):
            for method in ("conventional","harness"):
                with self.subTest(name=name,method=method):
                    s=state(name);chosen=choose_plan(s,method)
                    self.assertIsNotNone(chosen["plan"])
                    self.assertEqual(self.independent_decision(s,chosen["plan"])["proposal"]["status"],expected)

    def test_rework_funding_is_required_only_when_corrections_are_permitted(self):
        s=state();s["contract"]["max_attempts"]=1
        next(p for p in s["policies"]["providers"] if p["party_id"]=="PRIMARY")["balance_minor"]=2000
        for method in ("conventional","harness"):
            chosen=choose_plan(s,method)["plan"]
            self.assertEqual({a["provider_id"] for a in chosen["allocations"]},{"PRIMARY"})
            self.assertEqual(chosen["rework_budget_minor"],0)
            self.assertEqual(self.independent_decision(s,chosen)["proposal"]["status"],"ACCEPTED")

    def test_provider_transfer_revocation_is_visible_during_planning(self):
        s=state();s["tick"]=10;s["contract"]["revocations"]=[{"party_id":"PRIMARY","tick":10,"action":"transfer"}]
        for method in ("conventional","harness"):
            self.assertNotIn("PRIMARY",{a["provider_id"] for a in choose_plan(s,method)["plan"]["allocations"]})

    def test_conventional_backup_is_better_than_constructed_alternative(self):
        s=state("conventional-better")
        p=choose_plan(s)["plan"]
        self.assertEqual({a["provider_id"] for a in p["allocations"]},{"BACKUP"})
        self.assertEqual(p["buyer_price_minor"],4500)
        s["blocked_dependencies"].append("BACKUP-HOST")
        alternative=choose_plan(s)["plan"]
        self.assertGreater(alternative["buyer_price_minor"],p["buyer_price_minor"])

    def test_construction_after_failure_covers_same_exact_units(self):
        s=state("constructed-continuity");s["blocked_dependencies"].append("BACKUP-HOST")
        p=choose_plan(s)["plan"]
        self.assertEqual({a["provider_id"] for a in p["allocations"]},{"COMPAT-A","COMPAT-B"})
        self.assertEqual(sum(a["last_unit"]-a["first_unit"]+1 for a in p["allocations"]),1900)
        self.assertEqual([(a["lot_id"],a["first_unit"],a["last_unit"]) for a in p["allocations"]],
                         [(a["lot_id"],a["first_unit"],a["last_unit"]) for a in lots(s["contract"])])

    def test_failed_agreement_coordination_cost_is_explicit_in_next_price(self):
        s=state("constructed-continuity");s["blocked_dependencies"].append("BACKUP-HOST")
        p=choose_plan(s)["plan"]
        s["catalog"]["participant_accounting"]=[{"party_id":"COORDINATOR","unreimbursed_cancelled_cost_minor":200}]
        q=choose_plan(s)["plan"]
        self.assertEqual(q["buyer_price_minor"],p["buyer_price_minor"]+200)
        self.assertEqual(q["coordinator_fee_minor"],500)

    def test_shared_failed_dependency_removes_every_affected_route(self):
        s=state("conventional-better")
        s["contract"]["providers"][1]["dependency"]="PRIMARY-HOST"
        plan=choose_plan(s)["plan"]
        self.assertNotIn("BACKUP",{a["provider_id"] for a in plan["allocations"]})

    def test_primary_does_not_require_external_provider_disclosure(self):
        s=state();s["contract"]["providers"][0]["permissions"]["disclosure"]=False
        self.assertEqual({a["provider_id"] for a in choose_plan(s)["plan"]["allocations"]},{"PRIMARY"})

    def test_revoked_backup_disclosure_is_honored(self):
        s=state("conventional-better");s["effective_permissions"]={"BACKUP":{"production":True,"disclosure":False}}
        self.assertNotIn("BACKUP",{a["provider_id"] for a in choose_plan(s)["plan"]["allocations"]})

    def test_no_deal_and_bounded_search_exhaustion_are_distinct(self):
        for method in ("conventional","harness"):
            self.assertEqual(choose_plan(state("no-deal"),method)["reason"],"NO_CAPACITY_ARRANGEMENT")
            s=state();s["contract"]["bounds"]["max_plans"]=1
            r=choose_plan(s,method)
            self.assertEqual(r["reason"],"SEARCH_LIMIT")
            self.assertFalse(r["search"]["exhaustive_within_declared_domain"])

    def test_strict_overlap_unknown_fields_boolean_quantity_and_history(self):
        for mutate in (
            lambda c:c.update(unknown=True),
            lambda c:c["providers"][0]["windows"].append({"window_id":"W1","start":2,"end":30,"capacity":1000}),
            lambda c:c["obligations"][0].update(quantity=True),
            lambda c:c["obligations"][0].update(quantity="1100"),
            lambda c:c["source_events"].pop(),
            lambda c:c.update(permissible_recovery_loss_units=1),
            lambda c:c["obligations"][0]["spec"].update(barcode="unsupported"),
        ):
            c=state()["contract"];mutate(c)
            with self.subTest(contract=c["contract_id"]),self.assertRaises(HarnessError):validate_contract(c)

    def test_timing_windows_do_not_make_late_capacity_usable(self):
        s=state("conventional-better")
        for p in s["contract"]["providers"]:
            for w in p["windows"]:w.update(start=501,end=800)
        self.assertIsNone(choose_plan(s)["plan"])

    def test_absent_ai_is_explicitly_not_run(self):
        r=LocalAIAdapter().run(state(),lambda *_:self.fail("No model must call tools"))
        self.assertEqual(r,{"verdict":"NOT_RUN","reason":"LOCAL_AI_UNAVAILABLE"})

    def test_ai_protocol_refuses_malformed_actions_before_tool_effects(self):
        for action in ({"op":[],"args":{}}, {"op":"produce","args":[]}, {"op":"unknown","args":{}}):
            with self.subTest(action=action),self.assertRaises(HarnessError):
                LocalAIAdapter(lambda *_:action,"UNIT-STUB-NOT-AI").run(state(),lambda *_:self.fail("Malformed action reached tools"))

    def test_ai_protocol_stub_checks_plumbing_only(self):
        actions=iter([{"op":"status","args":{}},{"event":"done","result":{"verdict":"MOCK_PROTOCOL_ONLY"}}])
        calls=[]
        r=LocalAIAdapter(lambda context,history:next(actions),"UNIT-STUB-NOT-AI").run(state(),lambda op,args:calls.append(op) or {"ok":True})
        self.assertEqual(calls,["status"]);self.assertEqual(r["verdict"],"MOCK_PROTOCOL_ONLY")


if __name__=="__main__": unittest.main()
