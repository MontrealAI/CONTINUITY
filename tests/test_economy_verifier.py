"""Fresh semantic, economic, provenance and mutation controls.

Positive evidence is produced by real isolated local service processes.  Each
deliberately corrupted package is a separate copy with new byte seals, so the
negative controls exercise independent semantics rather than only checksums.
"""
from copy import deepcopy
from pathlib import Path
import platform
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

from continuity_harness.schema import canonical, digest, strict_load
from continuity_economy.controller import Controller
from continuity_economy.fixtures import load_fixture
from continuity_economy import verifier
from continuity_economy.challenges import (
    _copy_package, _edit_database, _fixture_for, _replace_intervention_json,
    alter_evidence, registry, reseal_intervention, verify_mutant,
)


SUPPORTED = sys.platform == "linux" and platform.machine() == "x86_64"


@unittest.skipUnless(SUPPORTED, "Qualified candidate confinement requires Linux x86-64; no favorable substitute is used.")
class FreshEconomyVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.storage = tempfile.TemporaryDirectory(prefix="continuity-economy-fresh-verifier-")
        cls.root = Path(cls.storage.name)
        fixture = load_fixture("primary-recovery")
        fixture["contract"]["run_id"] = "VERIFIER-POSITIVE-1900"
        controller = Controller(fixture["contract"], fixture["policies"], "harness", cls.root / "original", cls.root / "original-authority")
        record = controller.run()
        if record["state"] != "COMPLETE":
            raise AssertionError(record["errors"])
        cls.pin = controller.reference_sha256
        cls.valid = verifier.verify_run(cls.root / "original", cls.root / "original-authority", expected_reference_sha256=cls.pin)
        if cls.valid["claims"]["outcome"] != "DEMONSTRATED":
            raise AssertionError((cls.valid["failures"], cls.valid["unresolved"]))

    @classmethod
    def tearDownClass(cls):
        cls.storage.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="case-", dir=self.root)
        self.path = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def clone(self, label="copy"):
        run, authority = self.path / label, self.path / (label + "-authority")
        _copy_package(self.root / "original", self.root / "original-authority", run, authority)
        return run, authority

    def fresh(self, run, authority, pin="original"):
        return verifier.verify_run(run, authority, expected_reference_sha256=self.pin if pin == "original" else pin)

    def codes(self, result):
        return {row["code"] for row in result["failures"] + result["unresolved"]}

    def test_real_positive_import_qualifies_exact_original_obligations(self):
        self.assertEqual(self.valid["claims"], {"outcome": "DEMONSTRATED", "service_feasibility": "DEMONSTRATED", "method_advantage": "NOT_ESTABLISHED"})
        self.assertEqual(self.valid["totals"]["accepted_quantity"], 1900)
        self.assertEqual({row["obligation_id"]: row["accepted_quantity"] for row in self.valid["per_obligation"]},
                         {"DL-100": 1100, "DL-200": 800, "DL-300": 0})
        self.assertEqual(self.valid["assessment"]["test_assertion"], "NOT_EVALUATED")
        self.assertEqual(self.valid["commercial_value"], "NOT_ESTABLISHED")

    def test_resealed_wrong_content_recipient_revision_duplicates_and_truncation_are_rejected(self):
        for mutation in ("wrong_content", "wrong_recipient", "stale_revision", "duplicate_unit", "truncated"):
            with self.subTest(mutation=mutation):
                run, authority = self.clone(mutation)
                alter_evidence(run, authority, mutation)
                result = self.fresh(run, authority)
                self.assertEqual(result["claims"]["outcome"], "FAILED")
                self.assertEqual(result["safety_status"], "FAILED")
                self.assertIn("FALSE_RECIPIENT_ACCEPTANCE", self.codes(result))
                self.assertNotIn("EVIDENCE_CHANGED", self.codes(result))
                self.assertNotIn("DATABASE_FINALIZATION_CHANGED", self.codes(result))

    def test_missing_imported_content_cannot_be_replaced_by_receipts(self):
        run, authority = self.clone()
        alter_evidence(run, authority, "missing_import")
        result = self.fresh(run, authority)
        self.assertEqual(result["claims"]["outcome"], "FAILED")
        self.assertIn("IMPORTED_CONTENT_INCOMPLETE", self.codes(result))

    def test_balanced_funds_do_not_authorize_wrong_payments(self):
        run, authority = self.clone()
        alter_evidence(run, authority, "balanced_wrong_payment")
        result = self.fresh(run, authority)
        self.assertEqual(result["accounting"]["initial_total_minor"], result["accounting"]["final_total_minor"])
        self.assertIn("FINANCIAL_EFFECT_MISMATCH", self.codes(result))
        self.assertEqual(result["safety_status"], "FAILED")

    def test_settlement_requires_actual_receiver_acceptance_ids(self):
        run, authority = self.clone()
        alter_evidence(run, authority, "invented_acceptance")
        result = self.fresh(run, authority)
        self.assertEqual(result["safety_status"], "FAILED")
        self.assertIn("SETTLEMENT_WITHOUT_ACCEPTED_CONTENT", self.codes(result))

    def test_lost_postcommit_observation_is_uncertain_not_timely_success(self):
        run, authority = self.clone()
        alter_evidence(run, authority, "missing_observation")
        result = self.fresh(run, authority)
        self.assertEqual(result["claims"]["outcome"], "NOT_ESTABLISHED")
        self.assertEqual(result["verification_status"], "INCOMPLETE")
        self.assertIn("ACCEPTANCE_OBSERVATION_MISSING", self.codes(result))
        self.assertEqual(result["totals"]["recipient_accepted_quantity"], 1900)
        self.assertLess(result["totals"]["accepted_quantity"], 1900)
        self.assertTrue(all(row["realized_feasibility"] != "DEMONSTRATED" for row in result["per_arrangement"]))

    def test_late_postcommit_observation_does_not_rewrite_original_acceptance(self):
        run, authority = self.clone()
        alter_evidence(run, authority, "late_observation")
        result = self.fresh(run, authority)
        self.assertEqual(result["claims"]["outcome"], "FAILED")
        self.assertIn("LATE_ACCEPTANCE", self.codes(result))
        self.assertEqual(result["totals"]["recipient_accepted_quantity"], 1900)
        self.assertGreater(result["totals"]["late_quantity"], 0)

    def test_three_targeted_mutations_expose_false_positive_and_false_negative_checkers(self):
        for alteration, mutant in (("wrong_content", "ignore_wrong_content"), ("late_observation", "ignore_deadline")):
            with self.subTest(mutant=mutant):
                run, authority = self.clone(mutant)
                alter_evidence(run, authority, alteration)
                reference = self.fresh(run, authority)
                target = verify_mutant(run, authority, self.pin, mutant)
                self.assertEqual(reference["claims"]["outcome"], "FAILED")
                self.assertEqual(target["claims"]["outcome"], "DEMONSTRATED")
                # The mutation context restores the real oracle; this passing
                # test exposes a defective checker rather than qualifying it.
                self.assertEqual(self.fresh(run, authority)["claims"]["outcome"], "FAILED")
        target = verify_mutant(self.root / "original", self.root / "original-authority", self.pin, "reject_valid_content")
        self.assertEqual(target["claims"]["outcome"], "FAILED")
        self.assertEqual(self.valid["claims"]["outcome"], "DEMONSTRATED")

    def test_producer_and_receiver_helpers_are_not_the_fresh_oracle(self):
        with patch("continuity_economy.producer.generate_product", side_effect=AssertionError("circular generator")), \
             patch("continuity_economy.receiver.Receiver.inspect", side_effect=AssertionError("circular consumer")):
            result = self.fresh(self.root / "original", self.root / "original-authority")
        self.assertEqual(result["claims"]["outcome"], "DEMONSTRATED")

    def test_saved_favorable_report_has_no_authority(self):
        run, authority = self.clone()
        alter_evidence(run, authority, "wrong_content")
        (run / "RESULT.json").write_bytes(canonical({"claims": {"outcome": "DEMONSTRATED"}, "accepted_quantity": 1900}))
        (run / "PASSPORT.en.md").write_text("# CONTINUITY Ω\n\nPASS\n", encoding="utf-8")
        (run / "PASSPORT.fr.md").write_text("# CONTINUITÉ Ω\n\nRÉUSSITE\n", encoding="utf-8")
        self.assertEqual(self.fresh(run, authority)["claims"]["outcome"], "FAILED")

    def test_missing_original_pin_preserves_uncertainty(self):
        result = self.fresh(self.root / "original", self.root / "original-authority", pin=None)
        self.assertEqual(result["authority_status"], "NOT_ESTABLISHED")
        self.assertEqual(result["claims"]["outcome"], "NOT_ESTABLISHED")
        self.assertIn("REFERENCE_PIN_MISSING", self.codes(result))

    def test_missing_authority_file_preserves_uncertainty(self):
        run, authority = self.clone()
        (authority / "reference.json").unlink()
        result = self.fresh(run, authority)
        self.assertEqual(result["claims"]["outcome"], "NOT_ESTABLISHED")
        self.assertIn("AUTHORITY_MISSING", self.codes(result))

    def test_actual_coherent_1850_execution_cannot_satisfy_retained_1900_pin(self):
        spec, _ = registry()
        case = next(row for row in spec["cases"] if row["id"] == "coherent-1850-rewrite")
        fixture = _fixture_for(case, spec)
        controller = Controller(fixture["contract"], fixture["policies"], "harness", self.path / "altered", self.path / "altered-authority")
        controller.run()
        own = self.fresh(controller.run_dir, controller.authority_dir, pin=controller.reference_sha256)
        checked = self.fresh(controller.run_dir, controller.authority_dir)
        self.assertEqual(own["claims"]["outcome"], "DEMONSTRATED")
        self.assertEqual(own["totals"]["accepted_quantity"], 1850)
        self.assertEqual(checked["claims"]["outcome"], "FAILED")
        self.assertEqual(checked["totals"]["accepted_quantity"], 0)
        self.assertIn("REFERENCE_PIN_MISMATCH", self.codes(checked))
        self.assertEqual(self.valid["totals"]["accepted_quantity"], 1900)

    def test_duplicate_authority_json_keys_are_rejected(self):
        run, authority = self.clone()
        original = (authority / "contract.json").read_bytes()
        (authority / "contract.json").write_bytes(b'{"revision":1,' + original.lstrip()[1:])
        result = self.fresh(run, authority)
        self.assertNotEqual(result["claims"]["outcome"], "DEMONSTRATED")
        self.assertIn("AUTHORITY_INVALID", self.codes(result))

    def test_incomplete_verifier_never_inherits_a_saved_success(self):
        with patch.object(verifier, "_database", side_effect=RuntimeError("deliberate observer crash")):
            result = self.fresh(self.root / "original", self.root / "original-authority")
        self.assertEqual(result["claims"]["outcome"], "NOT_ESTABLISHED")
        self.assertEqual(result["verification_status"], "INCOMPLETE")
        self.assertIn("VERIFIER_FAILURE", self.codes(result))
        self.assertEqual(result["assessment"]["target_verdict"], "COMPLETED")

    def test_mixed_database_identity_is_detected_even_after_resealing(self):
        run, authority = self.clone()
        _edit_database(run / "evidence/receiver.sqlite", lambda db: db.execute(
            "UPDATE metadata SET value=? WHERE key='run_id'", (canonical("ANOTHER-RUN").decode(),)))
        reseal_intervention(run, authority)
        result = self.fresh(run, authority)
        self.assertEqual(result["claims"]["outcome"], "FAILED")
        self.assertIn("RECEIVER_DATABASE_BINDING", self.codes(result))

    def test_unfinalized_database_is_incomplete_and_cannot_claim_success(self):
        run, authority = self.clone()
        (run / "evidence/receiver.sqlite-wal").write_bytes(b"retained-uncheckpointed-state")
        reseal_intervention(run, authority)
        result = self.fresh(run, authority)
        self.assertNotEqual(result["claims"]["outcome"], "DEMONSTRATED")
        self.assertEqual(result["verification_status"], "INCOMPLETE")

    def test_ai_unavailable_and_false_pass_label_never_claim_execution(self):
        fixture = load_fixture("primary-recovery")
        controller = Controller(fixture["contract"], fixture["policies"], "ai", self.path / "ai", self.path / "ai-authority")
        record = controller.run()
        record["target_verdict"] = "PASS"
        _replace_intervention_json(controller.run_dir / "controller.json", record)
        reseal_intervention(controller.run_dir, controller.authority_dir)
        result = self.fresh(controller.run_dir, controller.authority_dir, pin=controller.reference_sha256)
        self.assertEqual(result["claims"], {"outcome": "NOT_ESTABLISHED", "service_feasibility": "NOT_ESTABLISHED", "method_advantage": "NOT_ESTABLISHED"})
        self.assertEqual(result["assessment"]["test_assertion"], "NOT_RUN")
        self.assertEqual(result["assessment"]["evidence_stage"], "NOT_RUN")
        self.assertEqual(result["totals"]["accepted_quantity"], 0)


class ClockBoundaryControls(unittest.TestCase):
    def test_postcommit_deadline_is_inclusive_and_uses_frozen_origin(self):
        controller = {"started_monotonic_ns": 1_100_000, "finished_monotonic_ns": 3_000_000}
        for tick, stamp, expected in ((10, 2_000_000, True), (11, 2_000_000, False), (10, 2_000_001, False)):
            with self.subTest(tick=tick, stamp=stamp):
                findings = verifier.Findings()
                observed = verifier._observed_clock({"tick": tick, "monotonic_ns": stamp}, controller, 10, 1,
                    findings, obligation_id="ORDER", wall_origin_ns=1_000_000)
                self.assertEqual(observed, expected)


if __name__ == "__main__":
    unittest.main()
