"""Semantic parity and safe presentation of the fresh Harness assessment."""

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from continuity_harness.reporting import render_passport, write_reports
from continuity_harness.schema import HarnessError, canonical, digest


def sample():
    resources = {"wall_ns": 123_456_789, "cpu_user_ns": 23_000_000,
                 "cpu_system_ns": 7_000_000, "peak_rss_bytes": None,
                 "storage_bytes": 42000, "requests": 14, "retries": 1,
                 "worker_restarts": 2, "human_interventions": 0,
                 "preparation_labor_seconds": None, "integration_labor_seconds": None,
                 "monetary_cost": None}
    result = {
        "schema": "continuity-harness/verification/v1", "verifier_version": "0.1.0",
        "run_id": "REPORT-001", "contract_sha256": "a" * 64,
        "reference_sha256": "b" * 64,
        "authority_status": "DEMONSTRATED", "verification_status": "COMPLETE",
        "assessment": {"test_assertion": "PASSED", "target_verdict": "PARTIAL",
                       "evidence_stage": "LOCAL_SOFTWARE_EXECUTION", "claim_status": "FAILED"},
        "safety_status": "DEMONSTRATED", "all_obligations_completed": False,
        "per_obligation": [
            {"order_id": "LBL-100", "recipient": "CUSTOMER-A", "product": "LABEL-A",
             "spec_sha256": "c" * 64, "expected_quantity": 1100, "observed_quantity": 1100,
             "accepted_quantity": 1100, "outcome": "COMPLETED", "reason_codes": [],
             "route": "backup", "deadline_tick": 100, "completed_tick": 12,
             "completion_ns": 12_345_678},
            {"order_id": "LBL-200", "recipient": "CUSTOMER-B", "product": "LABEL-A",
             "spec_sha256": "d" * 64, "expected_quantity": 800, "observed_quantity": 0,
             "accepted_quantity": 0, "outcome": "REFUSED",
             "reason_codes": ["CAPACITY_EXCEEDED", "NO_DURABLE_OUTPUT"],
             "route": None, "deadline_tick": 100, "completed_tick": None, "completion_ns": None},
        ],
        "totals": {"expected_obligations": 2, "accepted_obligations": 1,
                   "expected_units": 1900, "observed_units": 1100, "accepted_units": 1100,
                   "missing_units": 800, "late_obligations": 0, "incorrect_obligations": 0,
                   "duplicate_obligations": 0, "unsupported_obligations": 0},
        "ledger": {"max_simultaneous_allocated": {"primary": 0, "backup": 1100},
                   "history_transitions": 6, "primary_recovery_verified": False},
        "failures": [{"code": "ALL_OBLIGATIONS_NOT_COMPLETED", "detail": ""}],
        "unresolved": [], "evidence_sha256": {"evidence/artifacts/LBL-100.json": "e" * 64,
                                               "evidence/service.sqlite": "f" * 64},
        "resources": resources, "recovery_ms": 7,
        "trust_scope": "TRUSTED_HOST_CONTROLLER_CLOCK_AND_VERIFIER_AUTHORED_SYNTHETIC_SOURCE",
        "commercial_value": "NOT_ESTABLISHED", "real_customer_authenticity": "NOT_ESTABLISHED",
    }
    fault = {"event": "ACK_LOST_AFTER_DURABLE_FULFILLMENT", "action": "DROP_ACK", "target": "service"}
    controller = {
        "run_id": "REPORT-001", "method": "harness", "scenario": "constrained", "seed": 101,
        "state": "COMPLETE", "started_utc": "2026-11-06T20:00:00+00:00",
        "implementation": {"version": "0.1.0", "git_commit": "1" * 40, "dirty": False,
                           "source_sha256": {"continuity_harness/verifier.py": "2" * 64},
                           "environment": {"python": "3.12.14", "platform": "Linux x86_64", "sqlite_version": "3.45"}},
        "isolation": {"mechanism": "SECCOMP_BPF", "applied": True,
                      "probe": {"authority_open_denied": True, "workspace_open_denied": True,
                                "network_denied": True, "spawn_denied": True}},
        "fault_schedule": [fault], "faults_observed": [deepcopy(fault)], "events": [], "errors": [],
        "resources": resources,
    }
    info = {
        "run_dir": "/tmp/report example/run", "authority_dir": "/tmp/report example/authority",
        "reference_sha256": "b" * 64,
        "contract": {"contract_id": "CONTRACT-001", "version": 1, "source_sha256": "3" * 64,
                     "cutoff_sequence": 5, "source_complete": True, "deadline_tick": 100,
                     "wall_deadline_ms": 30000, "recovery_objective_ms": 15000,
                     "window": {"start": 0, "end": 100}, "lease_ticks": 20,
                     "capacities": {"primary": 3000, "backup": 1500},
                     "allowed_routes": ["primary", "backup"], "permissions": {"activation": True, "sharing": True},
                     "dependencies": {"primary": "GRID-A", "backup": "GRID-B"},
                     "blocked_dependencies": ["GRID-A"]},
        "commands": [["python3", "-m", "continuity_harness", "demo", "--out", "/tmp/report example"]],
    }
    return result, controller, info


class PassportTests(unittest.TestCase):
    def test_both_languages_preserve_partial_outcome_and_every_material_fact(self):
        result, controller, info = sample()
        rendered = {lang: render_passport(result, controller, info, lang) for lang in ("en", "fr")}
        for lang, text in rendered.items():
            with self.subTest(language=lang):
                for key in ("PASSED", "PARTIAL", "FAILED", "DEMONSTRATED", "LOCAL_SOFTWARE_EXECUTION", "NOT_ESTABLISHED"):
                    self.assertIn("`" + key + "`", text)
                for token in ("LBL-100", "LBL-200", "CUSTOMER-A", "CUSTOMER-B", "1100", "800", "1900",
                              "30000", "15000", "123456789 ns", "CAPACITY_EXCEEDED", "NO_DURABLE_OUTPUT",
                              "ALL_OBLIGATIONS_NOT_COMPLETED", "3.12.14", "Linux x86_64", "3.45", digest(result)):
                    self.assertIn(token, text)
                for value in ("a", "b", "c", "d", "e", "f"):
                    self.assertIn(value * 64, text)
                self.assertRegex(text, r"\| LBL-100 \| CUSTOMER-A \| 1100 \| 1100 \| 1100 \| `COMPLETED`")
                self.assertRegex(text, r"\| LBL-200 \| CUSTOMER-B \| 800 \| 0 \| 0 \| `REFUSED`")
        self.assertIn("| Every obligation completed | No |", rendered["en"])
        self.assertIn("| Toutes les obligations terminées | Non |", rendered["fr"])
        self.assertIn("insufficient remaining capacity; no excess allocation is implied", rendered["en"])
        self.assertIn("capacité restante insuffisante ; aucune surallocation n’est déduite", rendered["fr"])

    def test_french_title_and_explanations_are_translated(self):
        result, controller, info = sample()
        text = render_passport(result, controller, info, "fr")
        self.assertTrue(text.startswith("# CONTINUITÉ Ω — Banc d’essai et de vérification"))
        self.assertNotIn("# CONTINUITY", text)
        for phrase in ("Assertion du test", "Verdict du composant testé", "Stade des preuves",
                       "État de la vérification fraîche", "La promesse complète au client n’a pas été tenue."):
            self.assertIn(phrase, text)
        self.assertNotIn("The complete customer promise", text)
        self.assertIn("NON CONSIGNÉ / INCONNU", text)

    def test_unknown_measurements_are_not_replaced_with_zero(self):
        result, controller, info = sample()
        for language, unknown, label in (("en", "NOT RECORDED / UNKNOWN", "Peak resident memory (bytes)"),
                                         ("fr", "NON CONSIGNÉ / INCONNU", "Mémoire résidente maximale (octets)")):
            text = render_passport(result, controller, info, language)
            self.assertIn(f"| {label} | {unknown} |", text)
            money_label = "Complete monetary cost" if language == "en" else "Coût monétaire complet"
            self.assertIn(f"| {money_label} | {unknown} |", text)

    def test_missing_authority_or_verifier_result_stays_explicitly_unknown(self):
        for language in ("en", "fr"):
            text = render_passport({}, {}, {}, language)
            self.assertNotIn("`DEMONSTRATED`", text)
            self.assertNotIn("`PASS`", text)
            self.assertNotIn("`PASSED`", text)
            self.assertNotIn("| 0 |", text)
            self.assertIn("No per-obligation evidence" if language == "en" else "Aucune preuve par obligation", text)
            self.assertIn("no complete verification command" if language == "en" else "impossible de reconstruire une commande complète", text)

    def test_not_run_ai_is_never_presented_as_ai_performance(self):
        result, controller, info = sample()
        result["assessment"].update(test_assertion="NOT_RUN", target_verdict="NOT_RUN", evidence_stage="NOT_RUN", claim_status="NOT_ESTABLISHED")
        result["per_obligation"] = []
        result["all_obligations_completed"] = False
        controller.update(method="ai", state="NOT_RUN", errors=[{"code": "LOCAL_AI_UNAVAILABLE", "detail": ""}])
        for language in ("en", "fr"):
            text = render_passport(result, controller, info, language)
            self.assertIn("`NOT_RUN`", text)
            self.assertIn("LOCAL_AI_UNAVAILABLE", text)
            self.assertIn("AI performance was not measured" if language == "en" else "la performance d’IA n’a pas été mesurée", text)

    def test_reference_pin_is_distinct_from_observed_reference(self):
        result, controller, info = sample()
        info["reference_sha256"] = "4" * 64
        result["failures"] = [{"code": "REFERENCE_PIN_MISMATCH", "detail": ""}]
        for language in ("en", "fr"):
            text = render_passport(result, controller, info, language)
            self.assertIn("b" * 64, text)
            self.assertIn("4" * 64, text)
            self.assertIn("REFERENCE_PIN_MISMATCH", text)
            self.assertIn("--reference-sha256 " + "4" * 64, text)

    def test_mutation_test_pass_never_qualifies_the_defective_checker(self):
        result, controller, info = sample()
        result["assessment"].update(test_assertion="PASSED", target_verdict="DEMONSTRATED",
                                    evidence_stage="CHECKER_MUTATION_EXERCISE", claim_status="FAILED")
        result["challenge"] = {
            "id": "byte-integrity-mutant", "assessment_subject": "MUTATED_VERIFIER",
            "title": {"en": "Changed bytes accepted by the mutant", "fr": "Octets modifiés acceptés par le mutant"},
            "claim": {"en": "The tested checker detects changed bytes.", "fr": "Le vérificateur éprouvé détecte les octets modifiés."},
            "expected_observation": {"en": "False acceptance is exposed.", "fr": "L’acceptation indue est révélée."},
            "actual_observation": {"en": "The mutant accepted; the independent reference refused.", "fr": "Le mutant a accepté ; la référence indépendante a refusé."},
            "underlying_claim_status": "FAILED", "target_result_path": "TARGET_RESULT.json",
            "reference_result_path": "REFERENCE_RESULT.json", "source_evidence_path": "run",
            "mutation": {"hook": "byte_integrity", "kind": "disabled"},
        }
        for language, claim_label, explanation in (
            ("en", "Declared checker or procedure claim", "does not qualify that checker"),
            ("fr", "Affirmation déclarée sur le vérificateur ou la procédure", "ne qualifie pas celui-ci"),
        ):
            text = render_passport(result, controller, info, language)
            for token in ("PASSED", "DEMONSTRATED", "CHECKER_MUTATION_EXERCISE", "FAILED",
                          "MUTATED_VERIFIER", "TARGET_RESULT.json", "REFERENCE_RESULT.json", "byte-integrity-mutant"):
                self.assertIn(token, text)
            self.assertIn(f"| {claim_label} | `FAILED`", text)
            self.assertIn(explanation, text)
            self.assertIn(result["challenge"]["claim"][language], text)
            self.assertRegex(text, r"\| LBL-200 \| CUSTOMER-B \| 800 \| 0 \| 0 \| `REFUSED`")
            self.assertIn("[CHALLENGE.json](CHALLENGE.json)", text)
            self.assertIn("[controller.json](run/controller.json)", text)
            self.assertNotIn("[RESULT.json](RESULT.json)", text)

    def test_durable_completion_upper_bound_is_distinct_from_transition_time(self):
        result, controller, info = sample()
        result["per_obligation"][0].update(completion_ns=123456789, transition_ns=120000000,
                                           durable_observed_monotonic_ns=9123456789)
        resources = result["resources"]
        resources.update(controller_cpu_user_ns=4567890, controller_cpu_system_ns=1234000)
        for language, label, qualification in (
            ("en", "Durable completion observed no later than", "conservative upper bound"),
            ("fr", "Achèvement durable observé au plus tard après", "borne supérieure prudente"),
        ):
            text = render_passport(result, controller, info, language)
            for token in (label, qualification, "123456789 ns", "120000000 ns", "9123456789", "4567890 ns", "1234000 ns"):
                self.assertIn(token, text)

    def test_commands_quote_paths_and_include_the_independent_pin(self):
        result, controller, info = sample()
        text = render_passport(result, controller, info, "fr")
        self.assertIn("--language fr verify --run '/tmp/report example/run' --authority '/tmp/report example/authority'", text)
        self.assertIn("--reference-sha256 " + info["reference_sha256"], text)

    def test_rendering_is_deterministic_and_does_not_modify_facts(self):
        result, controller, info = sample()
        before = canonical([result, controller, info])
        first = render_passport(result, controller, info, "en")
        second = render_passport(result, controller, info, "en")
        self.assertEqual(first, second)
        self.assertEqual(before, canonical([result, controller, info]))

    def test_markdown_and_html_in_evidence_are_escaped(self):
        result, controller, info = sample()
        result["failures"] = [{"code": "VERIFICATION_ERROR", "detail": "<script>bad</script>|\n`test`", "order_id": "A|B"}]
        text = render_passport(result, controller, info)
        self.assertNotIn("<script>", text)
        self.assertIn("&lt;script&gt;", text)
        self.assertIn("A\\|B", text)
        self.assertIn("\\n&#96;test&#96;", text)

    def test_unexpected_diagnostic_stays_a_visible_code(self):
        result, controller, info = sample()
        result["unresolved"] = [{"code": "NEW_UNKNOWN_BOUNDARY", "detail": "test"}]
        for language in ("en", "fr"):
            text = render_passport(result, controller, info, language)
            self.assertIn("NEW_UNKNOWN_BOUNDARY", text)
            self.assertIn("Recorded technical diagnostic" if language == "en" else "Diagnostic technique consigné", text)

    def test_report_writer_refuses_either_existing_language_file(self):
        result, controller, info = sample()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prior = root / "PASSPORT.fr.md"
            prior.write_text("prior evidence", encoding="utf-8")
            with self.assertRaises(HarnessError) as raised:
                write_reports(root, result, controller, info)
            self.assertEqual(raised.exception.code, "OUTPUT_EXISTS")
            self.assertEqual(prior.read_text(), "prior evidence")
            self.assertFalse((root / "PASSPORT.en.md").exists())

    def test_report_writer_creates_two_identical_fact_views_without_overwrite(self):
        result, controller, info = sample()
        with tempfile.TemporaryDirectory() as directory:
            outputs = write_reports(directory, result, controller, info)
            self.assertEqual(set(outputs), {"en", "fr"})
            for language, filename in outputs.items():
                self.assertEqual(Path(filename).read_text(), render_passport(result, controller, info, language))
                self.assertIn(digest(result), Path(filename).read_text())
            with self.assertRaises(HarnessError):
                write_reports(directory, result, controller, info)

    def test_report_writer_refuses_symbolic_output_directory(self):
        result, controller, info = sample()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "real"
            target.mkdir()
            link = root / "link"
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaises(HarnessError) as raised:
                write_reports(link, result, controller, info)
            self.assertEqual(raised.exception.code, "UNSAFE_PATH")
            self.assertFalse(list(target.iterdir()))

    def test_unknown_language_and_noncanonical_numbers_refuse_rendering(self):
        result, controller, info = sample()
        with self.assertRaises(HarnessError):
            render_passport(result, controller, info, "de")
        result["resources"]["monetary_cost"] = float("nan")
        with self.assertRaises(HarnessError):
            render_passport(result, controller, info)


if __name__ == "__main__":
    unittest.main()
