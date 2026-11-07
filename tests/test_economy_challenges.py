"""Registered challenge coverage, fresh observation and honest mutant results."""
from copy import deepcopy
from pathlib import Path
import platform
import sys
import tempfile
import unittest

from continuity_harness.schema import HarnessError, canonical, strict_load
from continuity_economy.challenges import registry, run_challenges, verify_challenges


@unittest.skipUnless(sys.platform == "linux" and platform.machine() == "x86_64",
                     "Registered live challenges require qualified Linux x86-64 confinement.")
class RegisteredChallengeControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.storage = tempfile.TemporaryDirectory(prefix="continuity-economy-challenges-")
        cls.root = Path(cls.storage.name) / "registered"
        cls.result = run_challenges(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.storage.cleanup()

    def test_all_registered_controls_reexecute_and_freshly_verify(self):
        spec, _ = registry()
        self.assertEqual(self.result["test_assertion"], "PASSED",
                         [row for row in self.result["records"] if row["test_assertion"] != "PASSED"])
        fresh = verify_challenges(self.root)
        self.assertTrue(fresh["fresh"])
        self.assertEqual(fresh["test_assertion"], "PASSED")
        self.assertEqual({row["case_id"] for row in fresh["records"]}, {row["id"] for row in spec["cases"]})
        self.assertEqual(len(fresh["records"]), 26)

    def test_outer_pass_never_qualifies_any_defective_checker(self):
        mutants = [row for row in self.result["records"] if row["case_id"].startswith("mutant-")]
        self.assertEqual(len(mutants), 3)
        for row in mutants:
            with self.subTest(case=row["case_id"]):
                self.assertEqual(row["test_assertion"], "PASSED")
                self.assertEqual(row["claims"]["checker_qualification"], "FAILED")
                self.assertEqual(row["assessment"]["claim_status"], "FAILED")
                self.assertEqual(row["assessment"]["evidence_stage"], "TARGETED_VERIFIER_MUTATION")
        self.assertEqual(self.result["defective_checkers_qualified"], 0)

    def test_saved_favorable_challenge_labels_are_ignored(self):
        target = self.root / "runs/wrong-content-resealed/TARGET.json"
        before = target.read_bytes()
        try:
            target.write_bytes(canonical({"claims": {"outcome": "DEMONSTRATED"}, "accepted_quantity": 1900}))
            fresh = verify_challenges(self.root)
            wrong = next(row for row in fresh["records"] if row["case_id"] == "wrong-content-resealed")
            self.assertEqual(wrong["claims"]["outcome"], "FAILED")
            self.assertEqual(wrong["test_assertion"], "PASSED")
        finally:
            target.write_bytes(before)

    def test_missing_case_or_reassigned_original_pin_cannot_preserve_coverage(self):
        index_path = self.root / "INDEX.json"
        before, original = index_path.read_bytes(), strict_load(index_path)
        try:
            for mutation in ("missing_case", "rewrite_pin"):
                index = deepcopy(original)
                if mutation == "missing_case":
                    index["entries"].pop()
                else:
                    altered = next(row for row in index["entries"] if row["case_id"] == "coherent-1850-rewrite")
                    from continuity_harness.schema import digest
                    altered["reference_sha256"] = digest(strict_load(self.root / altered["authority"] / "reference.json"))
                index_path.write_bytes(canonical(index))
                with self.subTest(mutation=mutation), self.assertRaises(HarnessError):
                    verify_challenges(self.root)
        finally:
            index_path.write_bytes(before)


if __name__ == "__main__":
    unittest.main()
