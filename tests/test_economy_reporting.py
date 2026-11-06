"""Parity of claim boundaries, quantities, uncertainty and retained evidence."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest

from continuity_harness.schema import HarnessError, digest
from continuity_economy.reporting import render_passport, write_passports, TEXT, STATUS, FIELDS, LITERAL_TRANSLATIONS

BT = chr(96)


def quoted(text):
    return BT + text + BT


def sample_result():
    return {
        "schema": "continuity-economy/verification/v1", "verifier_version": "0.2.0",
        "run_id": "REPORT-RUN", "contract_id": "DIGITAL-PROMISE", "contract_sha256": "a1" * 32,
        "reference_sha256": "b2" * 32, "authority_status": "DEMONSTRATED",
        "verification_status": "COMPLETE",
        "assessment": {"test_assertion": "PASSED", "target_verdict": "PARTIAL",
                       "evidence_stage": "LOCAL_DIGITAL_PRODUCT_EXECUTION", "claim_status": "FAILED"},
        "claims": {"outcome": "FAILED", "service_feasibility": "FAILED", "method_advantage": "NOT_ESTABLISHED"},
        "safety_status": "DEMONSTRATED", "real_customer_authenticity": "NOT_ESTABLISHED",
        "commercial_value": "NOT_ESTABLISHED",
        "per_obligation": [{"obligation_id": "ORDER-A", "recipient": "BUYER-A", "revision": 2, "quantity": 4,
                            "produced_quantity": 4, "received_quantity": 4, "rejected_quantity": 2,
                            "accepted_quantity": 2, "missing_quantity": 2, "duplicate_quantity": 0,
                            "late_quantity": 0, "unauthorized_quantity": 0, "outcome": "PARTIAL",
                            "reason_codes": ["CAPACITY_EXCEEDED"], "deadline_tick": 100}],
        "per_arrangement": [{"proposal_id": "PROPOSAL-1", "agreement_id": "ARR-1", "kind": "MARKET",
                             "status": "CANCELLED", "proposed_terms": {"buyer_price_minor": 250, "rework_budget_minor": 20,
                                                "cancellation_fee_minor": 5, "policy_revision": 1},
                             "participant_decisions": [{"party_id": "BUYER", "verdict": "ACCEPTED", "tick": 1},
                                                       {"party_id": "PROVIDER", "verdict": "ACCEPTED", "tick": 1}],
                             "ex_ante_feasibility": "DEMONSTRATED", "realized_feasibility": "FAILED",
                             "costs": {"amount_minor": 125}, "payments": {"amount_minor": 5}}],
        "totals": {"required_quantity": 4, "accepted_quantity": 2},
        "accounting": {"currency": "SMU", "value_min_minor": 300, "value_max_minor": 450,
                       "outside_utility_minor": 40, "balance_minor": 875},
        "resources": {"wall_ns": 1_234_567, "storage_bytes": 98765, "requests": 8, "retries": 1,
                      "restarts": 1, "human_interventions": 0, "adaptation_labor_ns": None},
        "verification_resources": {"wall_ns": 34567},
        "accounting_gaps": ["PREPARATION_LABOR_NOT_MEASURED", "INTEGRATION_LABOR_NOT_MEASURED",
                            "ADAPTATION_LABOR_NOT_MEASURED", "MONETARY_RATES_NOT_MEASURED"],
        "failures": [{"code": "MISSING_ACCEPTED_UNITS", "detail": "ORDER-A:3-4", "scope": "outcome",
                       "obligation_id": "ORDER-A", "arrangement_id": "ARR-1"}],
        "unresolved": [{"code": "MONETARY_RATES_NOT_MEASURED", "detail": "SMU", "scope": "accounting"}],
        "evidence_sha256": {"evidence/receiver.sqlite": "c3" * 32, "evidence/producer.sqlite": "d4" * 32},
    }


def machine_record(text):
    match = re.search(BT * 3 + r"json\n(.*?)\n" + BT * 3, text, re.S)
    if not match:
        raise AssertionError("Complete structured verification record is missing")
    return json.loads(match.group(1))


class PassportParity(unittest.TestCase):
    def test_same_complete_record_and_digest_generate_both_languages_without_mutation(self):
        result = sample_result(); original = deepcopy(result)
        context = {"seed": 17, "deadline_tick": 100, "wall_deadline_ms": 30000,
                   "commands": [["python3", "-m", "continuity_economy", "--language", "fr", "demo"]],
                   "fault_schedule": [{"event": "ACK_LOST_AFTER_ACCEPTANCE", "trigger": "inspect", "occurrence": 1}]}
        original_context = deepcopy(context)
        for language in ("en", "fr"):
            text = render_passport(result, language, context)
            self.assertEqual(machine_record(text), result)
            self.assertIn("structured-result-sha256: " + digest(result), text)
            self.assertIn("evidence/receiver.sqlite", text)
            self.assertIn("ACK_LOST_AFTER_ACCEPTANCE", text)
            self.assertIn("| ORDER-A | BUYER-A | 2 | 4 | 4 | 4 | 2 | 2 |", text)
            for number in ("1234567", "98765", "34567", "30000", "875", "250"):
                self.assertIn(number, text)
        self.assertEqual(result, original); self.assertEqual(context, original_context)

    def test_french_title_and_human_boundaries_are_translated(self):
        en = render_passport(sample_result(), "en"); fr = render_passport(sample_result(), "fr")
        self.assertTrue(en.startswith("# CONTINUITY Ω Harness — Economy of continuity"))
        self.assertTrue(fr.startswith("# CONTINUITÉ Ω — Économie de la continuité"))
        for phrase in ("Trois affirmations distinctes", "Champs d’évaluation distincts",
                       "Exécution et acceptation par obligation", "Ressources mesurées et lacunes",
                       "authentifient pas", "contrats réels", "qualité d’impression", "Non établi"):
            self.assertIn(phrase, fr)
        for phrase in ("Three distinct claims", "No arrangement record", "Missing measurements are not displayed"):
            self.assertNotIn(phrase, fr)
        self.assertNotEqual(en, fr)

    def test_passing_test_does_not_change_failed_promise_or_partial_target(self):
        for language in ("en", "fr"):
            text = render_passport(sample_result(), language); record = machine_record(text)
            self.assertEqual(record["assessment"]["test_assertion"], "PASSED")
            self.assertEqual(record["assessment"]["target_verdict"], "PARTIAL")
            self.assertEqual(record["claims"]["outcome"], "FAILED")
            for code in ("PASSED", "PARTIAL", "FAILED"):
                self.assertIn("(" + quoted(code) + ")", text)

    def test_outcome_feasibility_and_method_claims_can_differ(self):
        result = sample_result()
        result["claims"] = {"outcome": "DEMONSTRATED", "service_feasibility": "FAILED", "method_advantage": "NOT_ESTABLISHED"}
        result["assessment"]["claim_status"] = "DEMONSTRATED"
        for language in ("en", "fr"):
            text = render_passport(result, language)
            self.assertEqual(machine_record(text)["claims"], result["claims"])
            claim_lines = text.split("<!-- structured-result-sha256:", 1)[1].split("## ", 2)[1]
            for code in result["claims"].values():
                self.assertIn(quoted(code), claim_lines)

    def test_every_economic_section_keeps_the_synthetic_boundary(self):
        for language in ("en", "fr"):
            result = sample_result()
            result["per_arrangement"].append({**result["per_arrangement"][0], "agreement_id": "ARR-2"})
            text = render_passport(result, language)
            self.assertGreaterEqual(text.count(TEXT["model"][1 if language == "fr" else 0]), 5)
            self.assertIn("SMU", text)
            self.assertIn(quoted("commercial_value"), text)
            self.assertEqual(machine_record(text)["commercial_value"], "NOT_ESTABLISHED")

    def test_missing_costs_remain_null_instead_of_invented_zeroes(self):
        for language in ("en", "fr"):
            text = render_passport(sample_result(), language)
            self.assertIsNone(machine_record(text)["resources"]["adaptation_labor_ns"])
            line = next(line for line in text.splitlines() if quoted("resources.adaptation_labor_ns") in line)
            self.assertIn("Non consigné" if language == "fr" else "Not recorded", line)
            self.assertNotIn("| 0 |", line)
            self.assertIn(quoted("ADAPTATION_LABOR_NOT_MEASURED"), text)

    def test_ai_not_run_has_no_invented_obligations_or_success(self):
        result = sample_result(); result["per_obligation"] = []; result["per_arrangement"] = []
        result["claims"] = {k: "NOT_ESTABLISHED" for k in result["claims"]}
        result["assessment"] = {"test_assertion": "NOT_EVALUATED", "target_verdict": "NOT_RUN",
                                "evidence_stage": "NOT_RUN", "claim_status": "NOT_ESTABLISHED"}
        result["verification_status"] = "INCOMPLETE"
        for language in ("en", "fr"):
            text = render_passport(result, language)
            self.assertIn(quoted("NOT_RUN"), text)
            self.assertEqual(machine_record(text)["per_obligation"], [])
            self.assertIn(TEXT["no_arrangements"][1 if language == "fr" else 0], text)

    def test_false_acceptance_mutant_is_not_qualified_by_passing_challenge(self):
        context = {"challenge": {"test_assertion": "PASSED", "target_verdict": "DEMONSTRATED",
                                  "reference_verdict": "FAILED", "checker_qualification": "FAILED"}}
        for language in ("en", "fr"):
            text = render_passport(sample_result(), language, context)
            self.assertIn(TEXT["failed_checker"][1 if language == "fr" else 0], text)
            for key in ("challenge.checker_qualification", "challenge.target_verdict", "challenge.reference_verdict"):
                self.assertIn(quoted(key), text)
            self.assertEqual(machine_record(text)["claims"]["outcome"], "FAILED")

    def test_unknown_future_fields_remain_in_complete_record(self):
        result = sample_result(); result["additional_measurement"] = {"exact_minor": 137, "remaining_unknown": None, "eligible": False}
        for language in ("en", "fr"):
            self.assertEqual(machine_record(render_passport(result, language)), result)

    def test_actual_verifier_fields_and_model_bounds_have_localized_human_labels(self):
        result = sample_result()
        result["authority_status"] = "ESTABLISHED_FOR_SYNTHETIC_EXERCISE"
        result["per_arrangement"][0]["kind"] = "TRADE"
        result["per_arrangement"][0]["independent_terms"] = {
            "buyer_definite_max_price_minor": 280, "buyer_possible_max_price_minor": 420,
            "minimum_buyer_price_minor": 350, "break_even_value_minor": 390,
            "scope": "AUTHORED_SYNTHETIC_MODEL"}
        result["per_arrangement"][0]["incurred_cost_minor"] = 125
        result["per_arrangement"][0]["correction_cost_minor"] = 20
        result["accounting"]["campaign"] = [{"party_id": "PROVIDER", "realized_profit_minor": -25,
                                            "participation_covered": False}]
        result["resources"]["measurement_scope"] = next(iter(LITERAL_TRANSLATIONS))
        result["accounting_gaps"].append("VERIFICATION_LABOR_NOT_MEASURED")
        result["trust_assumptions"] = ["SHARED_AUTHORSHIP_NOT_THIRD_PARTY_CERTIFICATION"]
        for language in ("en", "fr"):
            text = render_passport(result, language)
            human = text.split(BT * 3 + "json", 1)[0]
            for code in ("TRADE", "ESTABLISHED_FOR_SYNTHETIC_EXERCISE", "AUTHORED_SYNTHETIC_MODEL",
                         "VERIFICATION_LABOR_NOT_MEASURED", "SHARED_AUTHORSHIP_NOT_THIRD_PARTY_CERTIFICATION"):
                self.assertIn(STATUS[code][language == "fr"], human)
            for key in ("buyer_definite_max_price_minor", "buyer_possible_max_price_minor",
                        "minimum_buyer_price_minor", "break_even_value_minor", "incurred_cost_minor",
                        "correction_cost_minor", "realized_profit_minor", "participation_covered"):
                self.assertIn(FIELDS[key][language == "fr"], human)
            self.assertIn("| -25 |", human)
            self.assertIn(LITERAL_TRANSLATIONS[next(iter(LITERAL_TRANSLATIONS))][language == "fr"], human)
            self.assertEqual(machine_record(text), result)

    def test_source_faults_and_context_contract_are_visible_without_claim_mutation(self):
        result = sample_result(); del result["contract_id"]
        result["implementation"] = {"git_commit": "12" * 20, "dirty": True}
        result["fault_schedule"] = [{"event": "PRODUCTION_CRASH_HALF_WRITE", "occurrence": 1}]
        result["faults_observed"] = deepcopy(result["fault_schedule"])
        result["untriggered_faults"] = []
        original = deepcopy(result)
        for language in ("en", "fr"):
            text = render_passport(result, language, {"contract": {"contract_id": "RETAINED-PROMISE"}})
            human = text.split(BT * 3 + "json", 1)[0]
            self.assertIn("RETAINED-PROMISE", human)
            self.assertIn("12" * 20, human)
            self.assertIn(STATUS["PRODUCTION_CRASH_HALF_WRITE"][language == "fr"], human)
            self.assertEqual(machine_record(text), original)
        self.assertEqual(result, original)

    def test_cancelled_historical_quantity_is_not_presented_as_an_active_requirement(self):
        result = sample_result()
        cancelled = {**result["per_obligation"][0], "obligation_id": "CANCELLED-ORDER",
                     "quantity": 100, "required_quantity": 0, "status": "CANCELLED", "outcome": "CANCELLED",
                     "produced_quantity": 0, "received_quantity": 0, "rejected_quantity": 0, "accepted_quantity": 0}
        result["per_obligation"].append(cancelled)
        for language in ("en", "fr"):
            text = render_passport(result, language)
            self.assertIn("| CANCELLED-ORDER | BUYER-A | 2 | 0 | 0 | 0 | 0 | 0 |", text)
            self.assertEqual(machine_record(text)["per_obligation"][-1]["quantity"], 100)
            self.assertEqual(machine_record(text)["per_obligation"][-1]["required_quantity"], 0)

    def test_monetary_minor_unit_scale_is_explicit_and_values_are_not_rescaled(self):
        result = sample_result()
        for language in ("en", "fr"):
            text = render_passport(result, language)
            self.assertIn("100 unités mineures valent 1 SMU" if language == "fr" else
                          "100 minor units equal 1 fictional SMU", text)
            price_line = next(line for line in text.splitlines()
                              if quoted("proposed_terms.buyer_price_minor") in line)
            self.assertIn("| 250 |", price_line)
            self.assertIn("mineures" if language == "fr" else "minor units", price_line)
            self.assertEqual(machine_record(text)["per_arrangement"][0]["proposed_terms"]["buyer_price_minor"], 250)
        for key, pair in FIELDS.items():
            if key.endswith("_minor"):
                with self.subTest(field=key):
                    self.assertIn("minor units", pair[0])
                    self.assertIn("mineures", pair[1])

    def test_partial_active_arrangement_discloses_unresolved_escrow_without_inventing_payment(self):
        result = sample_result()
        result["per_arrangement"][0]["status"] = "ACTIVE"
        result["per_arrangement"][0]["realized_feasibility"] = "NOT_ESTABLISHED"
        result["per_arrangement"][0]["payments_minor"] = 0
        result["accounting"]["campaign"] = [{"party_id": "BUYER", "funds_still_held_minor": 250}]
        for language in ("en", "fr"):
            text = render_passport(result, language)
            self.assertIn(TEXT["partial_liabilities"][language == "fr"], text)
            self.assertEqual(machine_record(text), result)
            self.assertEqual(machine_record(text)["per_arrangement"][0]["payments_minor"], 0)
            self.assertEqual(machine_record(text)["claims"]["outcome"], "FAILED")

    def test_actual_mutant_shape_separates_valid_reference_outcome_and_failed_checker(self):
        result = sample_result()
        result["claims"]["outcome"] = "DEMONSTRATED"
        result["claims"]["checker_qualification"] = "FAILED"
        result["assessment"].update(target_verdict="FAILED", evidence_stage="TARGETED_VERIFIER_MUTATION",
                                    claim_status="FAILED")
        result["challenge"] = {"assessed_claim": "CHECKER_QUALIFICATION",
                               "checker_qualification": "FAILED", "reference_verdict": "DEMONSTRATED",
                               "target_verdict": "FAILED", "scope": "REGISTERED_SYNTHETIC_CHALLENGE"}
        for language in ("en", "fr"):
            text = render_passport(result, language)
            self.assertIn(TEXT["failed_checker"][language == "fr"], text)
            self.assertIn(TEXT["checker_claim"][language == "fr"], text)
            self.assertIn(TEXT["claim_status"][language == "fr"], text)
            self.assertNotIn("Outcome claim status", text)
            self.assertNotIn("État de l’affirmation de résultat", text)
            self.assertEqual(machine_record(text)["claims"]["outcome"], "DEMONSTRATED")
            self.assertEqual(machine_record(text)["claims"]["checker_qualification"], "FAILED")
            self.assertEqual(machine_record(text)["assessment"]["test_assertion"], "PASSED")

    def test_written_reassessment_preserves_both_previous_passports(self):
        result = sample_result()
        with tempfile.TemporaryDirectory() as temp:
            first = write_passports(result, temp)
            previous = {lang: Path(first[lang]).read_bytes() for lang in ("en", "fr")}
            write_passports(result, temp)
            self.assertFalse((Path(temp) / "passport-history").exists())
            updated = deepcopy(result); updated["verification_status"] = "INCOMPLETE"
            updated["claims"]["outcome"] = "NOT_ESTABLISHED"; updated["assessment"]["claim_status"] = "NOT_ESTABLISHED"
            second = write_passports(updated, temp)
            for language in ("en", "fr"):
                old = Path(temp) / "passport-history" / ("PASSPORT." + language + "." + hashlib.sha256(previous[language]).hexdigest() + ".md")
                self.assertEqual(old.read_bytes(), previous[language])
                self.assertEqual(machine_record(Path(second[language]).read_text()), updated)

    def test_symlink_output_is_rejected_without_modifying_target(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp); target = folder / "keep.txt"; target.write_text("keep")
            (folder / "PASSPORT.en.md").symlink_to(target)
            with self.assertRaises(HarnessError) as caught:
                write_passports(sample_result(), folder)
            self.assertEqual(caught.exception.code, "UNSAFE_PATH")
            self.assertEqual(target.read_text(), "keep")

    def test_localization_pairs_are_complete_and_table_data_is_escaped(self):
        for mapping in (TEXT, STATUS, FIELDS, LITERAL_TRANSLATIONS):
            for key, pair in mapping.items():
                with self.subTest(key=key):
                    self.assertEqual(len(pair), 2)
                    self.assertTrue(all(isinstance(value, str) and value for value in pair))
        result = sample_result(); result["failures"][0]["detail"] = "<script>|unsafe\nlocator"
        for language in ("en", "fr"):
            text = render_passport(result, language)
            self.assertIn("&lt;script&gt;\\|unsafe / locator", text)
            self.assertEqual(machine_record(text)["failures"][0]["detail"], result["failures"][0]["detail"])


if __name__ == "__main__":
    unittest.main()
