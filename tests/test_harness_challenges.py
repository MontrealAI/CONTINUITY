"""Retained noncomparative challenges preserve target and reference verdicts."""

import hashlib
from pathlib import Path
import platform
import sys
import tempfile
import unittest
from unittest.mock import patch

from continuity_harness.challenges import DEFINITIONS, run_challenges
from continuity_harness.schema import digest, expected_obligations, strict_load, strict_loads
from continuity_harness.verifier import verify_run


LINUX_X86 = sys.platform == "linux" and platform.machine() == "x86_64"


@unittest.skipUnless(LINUX_X86, "The registered candidate isolation requires Linux x86-64.")
class PreservedChallengeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="continuity-preserved-challenges-")
        cls.root = Path(cls.temp.name) / "challenges"
        cls.summary = run_challenges(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def case(self, name):
        folder = self.root / "cases" / name
        return (folder, strict_load(folder / "CHALLENGE.json"),
                strict_load(folder / "TARGET_RESULT.json"), strict_load(folder / "REFERENCE_RESULT.json"))

    def test_all_eight_registered_challenges_complete_and_every_attempt_is_retained(self):
        self.assertTrue(self.summary["complete"])
        self.assertTrue(self.summary["noncomparative"])
        self.assertEqual(self.summary["release_gate"], "PASSED")
        self.assertEqual(len(self.summary["records"]), len(DEFINITIONS))
        self.assertEqual(self.summary["executed_runs"], 4)
        self.assertEqual(len(self.summary["mutants_exposed"]), 3)
        self.assertEqual(self.summary["failed_test_assertions"], [])
        spec = strict_load(self.root / "CHALLENGE_SPEC.json")
        self.assertEqual(digest(spec), self.summary["specification_sha256"])
        attempts = [strict_loads(line) for line in (self.root / "ATTEMPTS.jsonl").read_bytes().splitlines()]
        self.assertEqual(sum(row["event"] == "START_CHALLENGE" for row in attempts), 8)
        self.assertEqual(sum(row["event"] == "FINISH_CHALLENGE" for row in attempts), 8)
        self.assertEqual(attempts[0]["event"], "START_POSITIVE_CONTROL")

    def test_outer_record_never_relabels_original_target_or_reference_results(self):
        for entry in self.summary["records"]:
            folder, outer, target, reference = self.case(entry["id"])
            with self.subTest(challenge=entry["id"]):
                self.assertEqual(digest(target), outer["target_result_sha256"])
                self.assertEqual(digest(reference), outer["reference_result_sha256"])
                self.assertEqual(outer["per_obligation"], reference["per_obligation"])
                self.assertEqual(outer["totals"], reference["totals"])
                self.assertEqual(outer["challenge"]["underlying_claim_status"], reference["assessment"]["claim_status"])
                self.assertEqual(reference["schema"], "continuity-harness/verification/v1")
                self.assertEqual(target["schema"], "continuity-harness/verification/v1")
                self.assertEqual(outer["schema"], "continuity-harness/challenge/v1")
                self.assertTrue((folder / "run/evidence/service.sqlite").is_file())
                self.assertEqual(entry["reference_pin_sha256"], outer["reference_pin_sha256"])
                if entry["id"] == "missing-reference-pin":
                    self.assertIsNone(entry["reference_pin_sha256"])
                else:
                    self.assertEqual(entry["reference_pin_sha256"], reference["reference_sha256"])

    def test_false_acceptance_is_passing_adversarial_test_and_failed_checker_qualification(self):
        for name in ("mutant-ignores-byte-integrity", "mutant-ignores-revocation"):
            _, outer, target, reference = self.case(name)
            with self.subTest(challenge=name):
                self.assertEqual(outer["assessment"], {"test_assertion": "PASSED", "target_verdict": "DEMONSTRATED",
                                                      "evidence_stage": "CHECKER_MUTATION_EXERCISE", "claim_status": "FAILED"})
                self.assertEqual(target["assessment"]["claim_status"], "DEMONSTRATED")
                self.assertEqual(reference["assessment"]["claim_status"], "FAILED")
                self.assertEqual(target["totals"]["accepted_units"], 1900)
                self.assertEqual(outer["totals"]["accepted_units"], 0)

    def test_false_negative_mutant_is_detected_by_real_positive_control(self):
        _, outer, target, reference = self.case("mutant-rejects-valid-recovery")
        self.assertEqual(outer["assessment"]["test_assertion"], "PASSED")
        self.assertEqual(outer["assessment"]["claim_status"], "FAILED")
        self.assertEqual(target["assessment"]["claim_status"], "FAILED")
        self.assertEqual(reference["assessment"]["claim_status"], "DEMONSTRATED")
        self.assertEqual(outer["totals"]["accepted_units"], 1900)

    def test_resealed_1850_candidate_package_preserves_1900_authority(self):
        folder, outer, _, reference = self.case("rewritten-1850")
        candidate = strict_load(folder / "run/candidate/view.json")
        original = strict_load(folder / "authority/contract.json")
        self.assertEqual(sum(row["quantity"] for row in expected_obligations(candidate["contract"])), 1850)
        self.assertEqual(sum(row["quantity"] for row in expected_obligations(original)), 1900)
        self.assertEqual(candidate["package_seals"]["contract_sha256"], digest(candidate["contract"]))
        self.assertEqual(candidate["package_seals"]["source_sha256"], digest(candidate["contract"]["source_events"]))
        unsigned_view = {key: value for key, value in candidate.items() if key != "package_seals"}
        self.assertEqual(candidate["package_seals"]["view_sha256"], digest(unsigned_view))
        self.assertEqual(outer["assessment"]["test_assertion"], "PASSED")
        self.assertEqual(reference["totals"]["expected_units"], 1900)
        self.assertEqual(reference["totals"]["accepted_units"], 1100)
        self.assertNotEqual(reference["assessment"]["claim_status"], "DEMONSTRATED")

    def test_missing_pin_retains_underlying_uncertainty(self):
        _, outer, target, reference = self.case("missing-reference-pin")
        self.assertEqual(outer["assessment"]["test_assertion"], "PASSED")
        self.assertEqual(outer["assessment"]["target_verdict"], "NOT_ESTABLISHED")
        self.assertEqual(outer["assessment"]["claim_status"], "DEMONSTRATED")
        self.assertEqual(target["assessment"]["claim_status"], "NOT_ESTABLISHED")
        self.assertEqual(reference["assessment"]["claim_status"], "NOT_ESTABLISHED")

    def test_ablation_and_failed_shared_dependency_are_not_hidden_as_fulfillment(self):
        for name in ("no-journal-ablation", "shared-failed-dependency"):
            _, outer, target, reference = self.case(name)
            with self.subTest(challenge=name):
                self.assertEqual(outer["assessment"]["test_assertion"], "PASSED")
                self.assertEqual(reference["totals"]["accepted_units"], 0)
                self.assertEqual(reference["assessment"]["claim_status"], "FAILED")
                self.assertFalse(target["all_obligations_completed"])
                self.assertEqual(target["assessment"], reference["assessment"])

    def test_changed_evidence_keeps_stale_passport_and_original_positive_control(self):
        base_run = self.root / "positive-control/run"
        base_authority = self.root / "positive-control/authority"
        base_artifact = (base_run / "evidence/artifacts/LBL-100.json").read_bytes()
        folder, outer, _, reference = self.case("changed-artifact")
        self.assertEqual((folder / "run/evidence/artifacts/LBL-100.json").read_bytes(), base_artifact + b" ")
        self.assertEqual((folder / "run/PASSPORT.en.md").read_bytes(), (base_run / "PASSPORT.en.md").read_bytes())
        self.assertEqual((folder / "run/RESULT.json").read_bytes(), (base_run / "RESULT.json").read_bytes())
        pin = digest(strict_load(base_authority / "reference.json"))
        fresh = verify_run(base_run, base_authority, expected_reference_sha256=pin)
        self.assertEqual(fresh["assessment"]["claim_status"], "DEMONSTRATED")
        self.assertIn("EVIDENCE_CHANGED", {item["code"] for item in reference["failures"]})
        self.assertEqual(outer["resource_origin"], "COPIED_POSITIVE_CONTROL_EXECUTION")
        from continuity_harness.verifier import _file_hash
        changed = folder / "run/evidence/artifacts/LBL-100.json"
        self.assertEqual(_file_hash(changed), hashlib.sha256(changed.read_bytes()).hexdigest())

    def test_both_complete_passports_preserve_all_assessment_fields_and_outcomes(self):
        for entry in self.summary["records"]:
            folder, outer, _, _ = self.case(entry["id"])
            for language in ("en", "fr"):
                with self.subTest(challenge=entry["id"], language=language):
                    text = (folder / f"PASSPORT.{language}.md").read_text()
                    self.assertIn(digest(outer), text)
                    self.assertIn(outer["challenge"]["claim"][language], text)
                    for value in outer["assessment"].values():
                        self.assertIn("`" + value + "`", text)
                    for order in outer["per_obligation"]:
                        self.assertIn(order["order_id"], text)
                        self.assertIn(str(order["expected_quantity"]), text)
                        self.assertIn(str(order["accepted_quantity"]), text)
                    self.assertIn("TARGET_RESULT.json", text)
                    self.assertIn("REFERENCE_RESULT.json", text)
                    if language == "fr":
                        self.assertTrue(text.startswith("# CONTINUITÉ Ω"))
        self.assertIn("CHECKER_MUTATION_EXERCISE", (self.root / "SUMMARY.fr.md").read_text())

    def test_existing_output_is_not_overwritten(self):
        before = (self.root / "SUMMARY.json").read_bytes()
        with self.assertRaises(FileExistsError):
            run_challenges(self.root)
        self.assertEqual((self.root / "SUMMARY.json").read_bytes(), before)


@unittest.skipUnless(LINUX_X86, "The registered candidate isolation requires Linux x86-64.")
class InterruptedChallengeTests(unittest.TestCase):
    def test_interrupted_suite_keeps_actual_service_evidence_and_incomplete_record(self):
        with tempfile.TemporaryDirectory(prefix="continuity-interrupted-challenges-") as td:
            root = Path(td) / "out"
            with patch("continuity_harness.challenges._verify", side_effect=OSError("INJECTED_VERIFIER_FAILURE")):
                with self.assertRaises(OSError):
                    run_challenges(root)
            summary = strict_load(root / "SUMMARY.json")
            self.assertFalse(summary["complete"])
            self.assertEqual(summary["release_gate"], "FAILED")
            self.assertTrue((root / "positive-control/run/evidence/service.sqlite").is_file())
            self.assertTrue((root / "cases/no-journal-ablation/run/evidence/service.sqlite").is_file())
            self.assertTrue((root / "cases/no-journal-ablation/authority/execution.json").is_file())
            attempts = (root / "ATTEMPTS.jsonl").read_text()
            self.assertIn("START_CHALLENGE", attempts)
            self.assertNotIn("FINISH_CHALLENGE", attempts)


if __name__ == "__main__":
    unittest.main()
