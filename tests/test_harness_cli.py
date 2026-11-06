"""Operator commands and suite coverage cannot turn partial evidence into success."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from continuity_harness.schema import HarnessError, strict_load
from continuity_harness.suite import run_suite, verify_suite


ROOT = Path(__file__).resolve().parents[1]


class HarnessCommandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory(prefix="continuity-cli-test-")
        cls.root = Path(cls.folder.name)
        cls.suite = cls.root / "demo"
        cls.summary = run_suite(cls.suite)
        cls.index = strict_load(cls.suite / "INDEX.json")

    @classmethod
    def tearDownClass(cls):
        cls.folder.cleanup()

    def command(self, *args):
        return subprocess.run([sys.executable, "-m", "continuity_harness", *args], cwd=ROOT,
                              text=True, capture_output=True, timeout=30)

    def copied(self, name):
        destination = self.root / name
        shutil.copytree(self.suite, destination)
        return destination

    def test_both_help_paths_translate_title_and_operator_actions(self):
        for language, title, usage, description in (
            ("en", "CONTINUITY Ω", "usage:", "Execute the three"),
            ("fr", "CONTINUITÉ Ω", "utilisation :", "Exécuter les trois"),
        ):
            result = self.command("--language", language, "--help")
            self.assertEqual(result.returncode, 0, result.stderr)
            for term in (title, usage, description):
                self.assertIn(term, result.stdout)
            sub = self.command("--language", language, "verify", "--help")
            self.assertEqual(sub.returncode, 0)
            self.assertIn("--reference-sha256", sub.stdout)
        equals_form = self.command("--language=fr", "--help")
        self.assertEqual(equals_form.returncode, 0)
        self.assertIn("CONTINUITÉ Ω", equals_form.stdout)

    def test_argument_errors_have_stable_code_and_localized_explanation(self):
        for language, term in (("en", "required"), ("fr", "Arguments invalides")):
            result = self.command("--language", language, "verify")
            self.assertEqual(result.returncode, 2)
            error = json.loads(result.stderr)
            self.assertEqual(error["code"], "CLI_ARGUMENT_ERROR")
            self.assertIn(term, error["message"])

    def test_demo_and_fresh_suite_keep_partial_claim_separate_from_passed_test(self):
        result = self.command("--language", "fr", "verify-suite", "--in-dir", str(self.suite))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["executed_runs"], 3)
        partial = [r for r in self.summary["records"] if r["scenario"] == "constrained"][0]
        self.assertEqual(partial["assessment"]["test_assertion"], "PASSED")
        self.assertEqual(partial["assessment"]["claim_status"], "FAILED")
        self.assertEqual(partial["totals"]["accepted_units"], 1100)

    def test_individual_verification_returns_three_for_partial_promise(self):
        for entry in self.index["entries"]:
            result = self.command("verify", "--run", str(self.suite / entry["run_relative"]),
                                  "--authority", str(self.suite / entry["authority_relative"]),
                                  "--reference-sha256", entry["reference_sha256"])
            self.assertEqual(result.returncode, 3 if entry["scenario"] == "constrained" else 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["assessment"]["test_assertion"], "PASSED")

    def test_no_reference_pin_stays_not_established(self):
        entry = self.index["entries"][0]
        result = self.command("--language", "fr", "verify", "--run", str(self.suite / entry["run_relative"]),
                              "--authority", str(self.suite / entry["authority_relative"]))
        self.assertEqual(result.returncode, 3)
        self.assertEqual(json.loads(result.stdout)["assessment"]["claim_status"], "NOT_ESTABLISHED")

    def test_saved_favorable_results_and_passports_are_not_proof(self):
        destination = self.copied("stale-passport")
        entry = self.index["entries"][0]
        run = destination / entry["run_relative"]
        (run / "RESULT.json").write_text('{"claim_status":"DEMONSTRATED"}')
        (destination / "SUMMARY.json").write_text('{"release_gate":"PASSED"}')
        artifact = next((run / "evidence/artifacts").glob("*.json"))
        artifact.write_bytes(artifact.read_bytes() + b" ")
        result = self.command("verify-suite", "--in-dir", str(destination))
        self.assertEqual(result.returncode, 3, result.stderr)
        fresh = json.loads(result.stdout)
        self.assertEqual(fresh["release_gate"], "FAILED")
        self.assertIn(entry["run_id"], fresh["critical_safety_failures"])

    def test_omitted_or_duplicated_conditions_cannot_pass_a_complete_suite(self):
        for name, change in (
            ("omitted", lambda index: index["entries"].pop()),
            ("duplicated", lambda index: index["entries"].__setitem__(1, deepcopy(index["entries"][0]))),
        ):
            destination = self.copied(name)
            index = deepcopy(self.index)
            change(index)
            (destination / "INDEX.json").write_text(json.dumps(index))
            with self.assertRaises(HarnessError):
                verify_suite(destination)

    def test_incomplete_suite_does_not_gain_a_favorable_gate(self):
        destination = self.copied("incomplete")
        index = deepcopy(self.index)
        index["complete"] = False
        index["entries"] = index["entries"][:1]
        (destination / "INDEX.json").write_text(json.dumps(index))
        self.assertEqual(verify_suite(destination)["release_gate"], "FAILED")

    def test_unsafe_suite_paths_and_unsupported_versions_are_refused(self):
        for name, change in (
            ("escape", lambda index: index["entries"][0].__setitem__("run_relative", "../escape")),
            ("version", lambda index: index.__setitem__("schema", "continuity-harness/suite/v99")),
            ("unknown", lambda index: index.__setitem__("trust_saved_passport", True)),
        ):
            destination = self.copied(name)
            index = deepcopy(self.index)
            change(index)
            (destination / "INDEX.json").write_text(json.dumps(index))
            with self.assertRaises(HarnessError):
                verify_suite(destination)

    def test_reused_output_is_refused_without_changing_prior_evidence(self):
        original = (self.suite / "INDEX.json").read_bytes()
        result = self.command("--language", "fr", "demo", "--out", str(self.suite))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)["code"], "OUTPUT_EXISTS")
        self.assertEqual((self.suite / "INDEX.json").read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
