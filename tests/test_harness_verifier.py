"""Fresh-verifier controls and deliberately resealed evidence mutations.

Integration bases execute actual local subprocesses.  A mutation test may change
the *trusted test fixture's* execution seal to isolate a semantic guard.  That is
not a claim that a sandboxed candidate can change the real retained authority.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
from types import FunctionType
import unittest
from unittest.mock import patch

from continuity_harness.controller import run_exercise
from continuity_harness.fixtures import candidate_view, make_contract
from continuity_harness.schema import (
    HarnessError, MAX_JSON_BYTES, canonical, digest, expected_obligations,
    strict_load, strict_loads, validate_contract,
)
from continuity_harness.verifier import verify_run


def put(path, value):
    Path(path).write_bytes(canonical(value) + b"\n")


class StrictAdmissionTests(unittest.TestCase):
    def test_original_contract_reconstructs_final_obligations(self):
        contract = make_contract()
        result = expected_obligations(contract)
        self.assertEqual([(r["order_id"], r["quantity"]) for r in result], [("LBL-100", 1100), ("LBL-200", 800)])
        self.assertEqual(result[0]["spec_sha256"], contract["source_events"][3]["spec_sha256"])
        self.assertEqual(result[0]["recipient"], "CUSTOMER-A")

    def test_invalid_contract_fields_are_structured_refusals(self):
        edits = [
            lambda c: c.update(budget_minor=True),
            lambda c: c["source_events"][0].update(quantity=True),
            lambda c: c["source_events"][0].update(quantity="1000"),
            lambda c: c["source_events"][0].update(quantity=0),
            lambda c: c["source_events"][0].update(quantity=1_000_000_001),
            lambda c: c["source_events"][0].update(order_id="../outside"),
            lambda c: c["source_events"][0].update(recipient="customer/other"),
            lambda c: c["source_events"][0].update(spec_sha256="not-a-digest"),
            lambda c: c["source_events"][1].update(sequence=1),
            lambda c: c["source_events"].pop(3),
            lambda c: c.update(version=True),
            lambda c: c.update(version=2),
            lambda c: c.update(schema="continuity-harness/contract/v9"),
            lambda c: c.update(unrecognized_field="ignored?"),
            lambda c: c["permissions"].update(activation="yes"),
            lambda c: c.update(allowed_routes=[{}]),
            lambda c: c.update(allowed_routes=["primary", "primary"]),
            lambda c: c.update(cutoff_sequence=4),
            lambda c: c.update(deadline_tick=1_000_000_001),
            lambda c: c["window"].update(end=0),
            lambda c: c.update(source_complete="true"),
            lambda c: c["capacities"].update(backup=True),
            lambda c: c["comparison"].update(information="PRIVILEGED"),
        ]
        for index, edit in enumerate(edits):
            with self.subTest(mutation=index):
                contract = make_contract()
                edit(contract)
                with self.assertRaises(HarnessError):
                    validate_contract(contract)
        for value in (None, True, [], "contract"):
            with self.subTest(top_level=value), self.assertRaises(HarnessError):
                validate_contract(value)

    def test_duplicate_nonfinite_fractional_deep_and_oversized_json(self):
        values = [b'{"money":1,"money":2}', b'{"x":NaN}', b'{"x":Infinity}', b'{"x":-Infinity}',
                  b'{"x":1.0}', b'{"x":1e2}', b'{"x":"\\ud800"}', b'{"x":',
                  b'[' * 40 + b'0' + b']' * 40, b' ' * (MAX_JSON_BYTES + 1)]
        for data in values:
            with self.subTest(prefix=data[:40]), self.assertRaises(HarnessError):
                strict_loads(data)

    def test_canonical_serialization_and_minor_units(self):
        self.assertEqual(canonical({"b": 10, "a": "é"}), canonical({"a": "é", "b": 10}))
        c = make_contract()
        c["budget_minor"] = 12345
        self.assertEqual(validate_contract(c)["budget_minor"], 12345)
        with self.assertRaises(HarnessError):
            canonical({"money": 1.5})

    def test_symbolic_link_is_not_an_authoritative_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            put(root / "actual.json", {})
            (root / "link.json").symlink_to(root / "actual.json")
            with self.assertRaises(HarnessError) as found:
                strict_load(root / "link.json")
            self.assertEqual(found.exception.code, "UNSAFE_PATH")

    def test_historical_fulfillment_and_cancellation_are_replayed(self):
        c = make_contract()
        c["source_events"].append({"sequence": 6, "type": "FULFILL", "order_id": "LBL-100", "quantity": 100})
        c["cutoff_sequence"] = 6
        c["source_sha256"] = digest(c["source_events"])
        self.assertEqual([o["quantity"] for o in expected_obligations(c)], [1000, 800])
        c["source_events"].append({"sequence": 7, "type": "AMEND", "order_id": "LBL-100", "quantity": 50})
        c["cutoff_sequence"] = 7
        c["source_sha256"] = digest(c["source_events"])
        with self.assertRaises(HarnessError):
            validate_contract(c)


class FreshVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bases = tempfile.TemporaryDirectory(prefix="continuity-verifier-controls-")
        cls.base = Path(cls.bases.name)
        for scenario in ("recovery", "alternate", "constrained"):
            root = cls.base / scenario
            result = run_exercise(make_contract(scenario=scenario), "harness", root / "run", root / "authority")
            if result["controller"]["state"] != "COMPLETE":
                raise AssertionError("The real-process positive-control setup failed: " + json.dumps(result["controller"]["errors"]))

    @classmethod
    def tearDownClass(cls):
        cls.bases.cleanup()

    def setUp(self):
        self.work = tempfile.TemporaryDirectory(prefix="continuity-verifier-case-")
        self.root = Path(self.work.name)
        self.copy_case("recovery")

    def tearDown(self):
        self.work.cleanup()

    def copy_case(self, scenario):
        for name in ("run", "authority"):
            destination = self.root / name
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(self.base / scenario / name, destination)
        self.run = self.root / "run"
        self.authority = self.root / "authority"
        self.pin = digest(strict_load(self.authority / "reference.json"))

    def verify(self):
        return verify_run(self.run, self.authority, expected_reference_sha256=self.pin)

    def codes(self, result):
        return {r["code"] for r in result["failures"] + result["unresolved"]}

    def test_shared_producer_replay_mutation_cannot_change_reference_acceptance(self):
        """One mutated producer helper must not also mutate the reference oracle.

        Mutating the function's code affects all aliases of that *same* helper,
        reproducing the common dependency that originally yielded false success
        for 1,850 units against a retained 1,900-unit contract. This is a test
        mutation, never a qualified implementation or comparative result.
        """
        import continuity_harness.schema as schema_module

        helper = schema_module.expected_obligations
        original = FunctionType(helper.__code__, helper.__globals__, helper.__name__,
                                helper.__defaults__, helper.__closure__)

        def omit_fifty_units(contract):
            orders = _unmutated_expected_obligations(contract)
            for order in orders:
                if order["order_id"] == "LBL-200":
                    order["quantity"] -= 50
            return orders

        contract = make_contract(scenario="alternate")
        view = candidate_view(contract)
        view["contract"]["source_events"][1]["quantity"] -= 50
        view["contract"]["source_sha256"] = digest(view["contract"]["source_events"])
        directory = self.root / "producer-replay-mutant"
        with patch.dict(helper.__globals__, {"_unmutated_expected_obligations": original}):
            try:
                helper.__code__ = omit_fifty_units.__code__
                run = run_exercise(contract, "harness", directory / "run", directory / "authority",
                                   candidate_visible=view)
                result = verify_run(run["run_dir"], run["authority_dir"],
                                    expected_reference_sha256=run["reference_sha256"])
            finally:
                helper.__code__ = original.__code__
        self.assertEqual(run["controller"]["target_verdict"], "COMPLETED")
        self.assertEqual(result["totals"]["observed_units"], 1850)
        self.assertEqual(result["totals"]["expected_units"], 1900)
        self.assertEqual(result["assessment"]["claim_status"], "FAILED")
        self.assertIn("AUTHORIZED_ORDERS_CHANGED", self.codes(result))
        self.assertIn("WRONG_QUANTITY", self.codes(result))

    def test_independent_reference_replay_retains_historical_fulfillment_and_later_amendment(self):
        contract = make_contract(scenario="recovery")
        final_spec = digest({"label_revision": 3})
        contract["source_events"].extend([
            {"sequence": 6, "type": "FULFILL", "order_id": "LBL-100", "quantity": 100},
            {"sequence": 7, "type": "AMEND", "order_id": "LBL-100", "quantity": 1250,
             "recipient": "CUSTOMER-REVISED", "spec_sha256": final_spec, "deadline_tick": 90},
        ])
        contract["cutoff_sequence"] = len(contract["source_events"])
        contract["source_sha256"] = digest(contract["source_events"])
        directory = self.root / "historical-fulfillment"
        run = run_exercise(contract, "harness", directory / "run", directory / "authority")
        result = verify_run(run["run_dir"], run["authority_dir"],
                            expected_reference_sha256=run["reference_sha256"])
        self.assertEqual(result["assessment"]["claim_status"], "DEMONSTRATED", result)
        self.assertEqual(result["totals"]["accepted_units"], 1950)
        first = next(row for row in result["per_obligation"] if row["order_id"] == "LBL-100")
        self.assertEqual((first["expected_quantity"], first["accepted_quantity"]), (1150, 1150))
        self.assertEqual(first["recipient"], "CUSTOMER-REVISED")
        self.assertEqual(first["spec_sha256"], final_spec)
        self.assertEqual(first["deadline_tick"], 90)
        self.assertNotIn("LBL-300", {row["order_id"] for row in result["per_obligation"]})

    def reseal(self):
        seal = strict_load(self.authority / "execution.json")
        seal["controller_sha256"] = digest(strict_load(self.run / "controller.json"))
        seal["evidence_manifest"] = {p.relative_to(self.run).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in sorted((self.run / "evidence").rglob("*")) if p.is_file()}
        put(self.authority / "execution.json", seal)

    def change_artifact(self, changes, *, synchronize_receipt=True, reseal=True):
        path = self.run / "evidence/artifacts/LBL-100.json"
        value = strict_load(path)
        value.update(changes)
        put(path, value)
        if synchronize_receipt:
            db = sqlite3.connect(self.run / "evidence/service.sqlite")
            try:
                db.execute("UPDATE receipts SET payload=?,sha256=?,completed_tick=?,completed_monotonic_ns=? WHERE order_id='LBL-100'",
                           (canonical(value).decode(), hashlib.sha256(canonical(value) + b"\n").hexdigest(), value["completed_tick"], value["completed_monotonic_ns"]))
                db.commit()
            finally:
                db.close()
        if reseal:
            self.reseal()
        return value

    def test_actual_recovery_positive_control(self):
        result = self.verify()
        self.assertEqual(result["assessment"]["claim_status"], "DEMONSTRATED")
        self.assertEqual(result["assessment"]["test_assertion"], "PASSED")
        self.assertEqual(result["totals"]["accepted_units"], 1900)
        self.assertTrue(result["ledger"]["primary_recovery_verified"])

    def test_actual_alternate_positive_control(self):
        self.copy_case("alternate")
        result = self.verify()
        self.assertEqual(result["assessment"]["claim_status"], "DEMONSTRATED")
        self.assertEqual(result["assessment"]["test_assertion"], "PASSED")
        self.assertTrue(all(o["route"] == "backup" for o in result["per_obligation"]))
        self.assertFalse(result["ledger"]["primary_recovery_verified"])
        self.assertIsNone(result["recovery_ms"])

    def test_constrained_safety_success_is_not_complete_promise(self):
        self.copy_case("constrained")
        result = self.verify()
        self.assertEqual(result["assessment"]["claim_status"], "FAILED")
        self.assertEqual(result["assessment"]["test_assertion"], "PASSED")
        self.assertEqual(result["safety_status"], "DEMONSTRATED")
        self.assertFalse(result["all_obligations_completed"])
        self.assertEqual(result["totals"]["accepted_units"], 1100)
        self.assertEqual(result["totals"]["missing_units"], 800)
        self.assertEqual([o["outcome"] for o in result["per_obligation"]], ["COMPLETED", "REFUSED"])
        self.assertIn("CAPACITY_EXCEEDED", result["per_obligation"][1]["reason_codes"])

    def test_missing_reference_pin_never_qualifies_internal_consistency(self):
        result = verify_run(self.run, self.authority)
        self.assertEqual(result["assessment"]["claim_status"], "NOT_ESTABLISHED")
        self.assertEqual(result["totals"]["accepted_units"], 0)
        self.assertIn("REFERENCE_PIN_MISSING", self.codes(result))

    def test_wrong_reference_pin_fails(self):
        self.pin = "0" * 64
        result = self.verify()
        self.assertEqual(result["assessment"]["claim_status"], "FAILED")
        self.assertIn("REFERENCE_PIN_MISMATCH", self.codes(result))

    def test_missing_authority_is_not_established(self):
        (self.authority / "reference.json").unlink()
        result = self.verify()
        self.assertEqual(result["assessment"]["claim_status"], "NOT_ESTABLISHED")
        self.assertIn("AUTHORITY_MISSING", self.codes(result))
        for key in ("expected_obligations", "expected_units", "missing_units", "unsupported_obligations"):
            self.assertIsNone(result["totals"][key])

    def test_missing_run_is_a_verification_attempt_without_invented_execution(self):
        result = verify_run(self.root / "absent-run", self.root / "absent-authority")
        self.assertEqual(result["assessment"]["claim_status"], "NOT_ESTABLISHED")
        self.assertEqual(result["assessment"]["evidence_stage"], "VERIFICATION_ATTEMPT")
        self.assertEqual(result["safety_status"], "NOT_ESTABLISHED")
        self.assertIsNone(result["totals"]["expected_units"])

    def test_every_required_isolation_probe_is_needed_for_qualification(self):
        for key in ("authority_open_denied", "workspace_open_denied", "network_denied", "spawn_denied", "process_inspection_denied"):
            with self.subTest(probe=key):
                self.copy_case("recovery")
                controller = strict_load(self.run / "controller.json")
                del controller["isolation"]["probe"][key]
                put(self.run / "controller.json", controller)
                self.reseal()
                result = self.verify()
                self.assertEqual(result["assessment"]["claim_status"], "NOT_ESTABLISHED")
                self.assertEqual(result["safety_status"], "NOT_ESTABLISHED")
                self.assertEqual(result["totals"]["accepted_units"], 0)
                self.assertIn("ISOLATION_NOT_ESTABLISHED", self.codes(result))

    def test_malformed_artifact_does_not_produce_a_favorable_safety_assessment(self):
        self.change_artifact({"quantity": "1100"}, synchronize_receipt=False)
        result = self.verify()
        self.assertIn("ARTIFACT_INVALID", self.codes(result))
        self.assertEqual(result["assessment"]["claim_status"], "FAILED")
        self.assertEqual(result["safety_status"], "NOT_ESTABLISHED")

    def test_inconsistent_receipt_does_not_produce_a_favorable_safety_assessment(self):
        db = sqlite3.connect(self.run / "evidence/service.sqlite")
        try:
            db.execute("UPDATE receipts SET sha256=? WHERE order_id='LBL-100'", ("0" * 64,))
            db.commit()
        finally:
            db.close()
        self.reseal()
        result = self.verify()
        self.assertIn("RECEIPT_MISMATCH", self.codes(result))
        self.assertEqual(result["safety_status"], "NOT_ESTABLISHED")

    def test_controller_environment_metadata_is_strictly_bounded(self):
        for value in ({"not": "argv"}, [True], ["x" * 4097], ["x"] * 129):
            with self.subTest(argv=value):
                self.copy_case("recovery")
                controller = strict_load(self.run / "controller.json")
                controller["implementation"]["environment"]["argv"] = value
                put(self.run / "controller.json", controller)
                self.reseal()
                result = self.verify()
                self.assertIn("CONTROLLER_INVALID", self.codes(result))
                self.assertEqual(result["assessment"]["claim_status"], "FAILED")

    def test_missing_protected_journal_is_not_established(self):
        (self.authority / "journal.json").unlink()
        result = self.verify()
        self.assertEqual(result["assessment"]["claim_status"], "NOT_ESTABLISHED")
        self.assertIn("SOURCE_JOURNAL_MISSING", self.codes(result))

    def test_incomplete_source_is_not_established(self):
        root = self.root / "incomplete"
        contract = make_contract(run_id="incomplete-source")
        contract["source_complete"] = False
        run = run_exercise(contract, "harness", root / "run", root / "authority")
        result = verify_run(root / "run", root / "authority", expected_reference_sha256=run["reference_sha256"])
        self.assertEqual(result["assessment"]["claim_status"], "NOT_ESTABLISHED")
        self.assertIn("SOURCE_INCOMPLETE", self.codes(result))

    def test_1850_rewrite_cannot_satisfy_original_1900_authority(self):
        changed = make_contract(run_id="revised-1850-exercise")
        changed["contract_id"] = "REVISED-CONTRACT-1850"
        changed["source_events"][1]["quantity"] -= 50
        changed["source_sha256"] = digest(changed["source_events"])
        root = self.root / "revised"
        run = run_exercise(changed, "harness", root / "run", root / "authority")
        own = verify_run(root / "run", root / "authority", expected_reference_sha256=run["reference_sha256"])
        self.assertEqual(own["assessment"]["claim_status"], "DEMONSTRATED")
        self.assertEqual(own["totals"]["accepted_units"], 1850)
        original = verify_run(root / "run", self.authority, expected_reference_sha256=self.pin)
        self.assertEqual(original["assessment"]["claim_status"], "FAILED")
        self.assertEqual(original["totals"]["expected_units"], 1900)
        self.assertIn("CONTROLLER_BINDING", self.codes(original))

    def test_changed_protected_journal_fails(self):
        journal = strict_load(self.authority / "journal.json")
        journal[1]["quantity"] -= 50
        put(self.authority / "journal.json", journal)
        result = self.verify()
        self.assertEqual(result["assessment"]["claim_status"], "FAILED")
        self.assertIn("SOURCE_JOURNAL_MISMATCH", self.codes(result))

    def test_stale_favorable_passport_does_not_replace_fresh_evidence(self):
        put(self.run / "PASSPORT.json", {"claim_status": "DEMONSTRATED", "accepted_units": 1900})
        self.change_artifact({"quantity": 1}, synchronize_receipt=False, reseal=False)
        result = self.verify()
        self.assertEqual(result["assessment"]["claim_status"], "FAILED")
        self.assertIn("EVIDENCE_CHANGED", self.codes(result))
        self.assertIn("WRONG_QUANTITY", self.codes(result))

    def test_semantic_artifact_mutations_are_detected_even_after_test_reseal(self):
        mutations = [({"recipient": "WRONG-CUSTOMER"}, "WRONG_RECIPIENT"),
                     ({"product": "WRONG-PRODUCT"}, "WRONG_PRODUCT"),
                     ({"spec_sha256": "0" * 64}, "WRONG_SPECIFICATION"),
                     ({"quantity": 1050}, "WRONG_QUANTITY"),
                     ({"run_id": "MIXED-RUN"}, "ARTIFACT_BINDING"),
                     ({"order_id": "LBL-300"}, "UNKNOWN_OBLIGATION")]
        for mutation, code in mutations:
            with self.subTest(code=code):
                self.copy_case("recovery")
                self.change_artifact(mutation)
                result = self.verify()
                self.assertEqual(result["assessment"]["claim_status"], "FAILED")
                self.assertIn(code, self.codes(result))

    def test_duplicate_completed_output_is_detected(self):
        source = self.run / "evidence/artifacts/LBL-100.json"
        shutil.copyfile(source, source.with_name("LBL-100-copy.json"))
        self.reseal()
        result = self.verify()
        self.assertEqual(result["safety_status"], "FAILED")
        self.assertIn("DUPLICATE_FULFILLMENT", self.codes(result))

    def test_late_logical_completion_is_not_accepted(self):
        c = strict_load(self.authority / "contract.json")
        self.change_artifact({"completed_tick": c["deadline_tick"] + 1})
        result = self.verify()
        self.assertIn("LATE_COMPLETION", self.codes(result))
        self.assertEqual(result["per_obligation"][0]["outcome"], "LATE")
        self.assertEqual(result["per_obligation"][0]["accepted_quantity"], 0)

    def test_measured_clock_outside_run_is_detected(self):
        controller = strict_load(self.run / "controller.json")
        self.change_artifact({"completed_monotonic_ns": controller["started_monotonic_ns"] - 1})
        result = self.verify()
        self.assertIn("CLOCK_OUTSIDE_RUN", self.codes(result))
        self.assertNotEqual(result["assessment"]["claim_status"], "DEMONSTRATED")

    def test_real_wall_deadline_is_checked_separately_from_ticks(self):
        controller = strict_load(self.run / "controller.json")
        contract = strict_load(self.authority / "contract.json")
        late = controller["started_monotonic_ns"] + (contract["wall_deadline_ms"] + 1) * 1_000_000
        self.change_artifact({"completed_monotonic_ns": late})
        result = self.verify()
        self.assertIn("WALL_DEADLINE_EXCEEDED", self.codes(result))

    def test_exact_recovery_objective_boundary_is_inclusive(self):
        controller = strict_load(self.run / "controller.json")
        contract = strict_load(self.authority / "contract.json")
        observation = next(event["monotonic_ns"] for event in controller["events"]
                           if event["event"] == "PRIMARY_RECOVERED")
        # A synthetic clock-boundary fixture, without a timing-sensitive sleep.
        controller["started_monotonic_ns"] = observation - contract["recovery_objective_ms"] * 1_000_000
        controller["recovery_ms"] = contract["recovery_objective_ms"]
        controller["resources"]["wall_ns"] = controller["finished_monotonic_ns"] - controller["started_monotonic_ns"]
        put(self.run / "controller.json", controller)
        self.reseal()
        result = self.verify()
        self.assertEqual(result["assessment"]["claim_status"], "DEMONSTRATED", result)
        self.assertNotIn("RECOVERY_OBJECTIVE_EXCEEDED", self.codes(result))

    def test_one_nanosecond_late_recovery_cannot_use_rounded_milliseconds(self):
        controller = strict_load(self.run / "controller.json")
        contract = strict_load(self.authority / "contract.json")
        observation = next(event["monotonic_ns"] for event in controller["events"]
                           if event["event"] == "PRIMARY_RECOVERED")
        controller["started_monotonic_ns"] = observation - contract["recovery_objective_ms"] * 1_000_000 - 1
        controller["recovery_ms"] = contract["recovery_objective_ms"]
        controller["resources"]["wall_ns"] = controller["finished_monotonic_ns"] - controller["started_monotonic_ns"]
        put(self.run / "controller.json", controller)
        self.reseal()
        result = self.verify()
        self.assertEqual(result["assessment"]["claim_status"], "FAILED")
        self.assertIn("RECOVERY_OBJECTIVE_EXCEEDED", self.codes(result))
        self.assertNotIn("WALL_DEADLINE_EXCEEDED", self.codes(result))

    def test_missing_recovery_observation_keeps_rounded_time_unestablished(self):
        controller = strict_load(self.run / "controller.json")
        self.assertIsNotNone(controller["recovery_ms"])
        controller["events"] = [event for event in controller["events"] if event["event"] != "PRIMARY_RECOVERED"]
        put(self.run / "controller.json", controller)
        self.reseal()
        result = self.verify()
        self.assertEqual(result["assessment"]["claim_status"], "NOT_ESTABLISHED")
        self.assertIn("RECOVERY_TIME_MISSING", self.codes(result))

    def test_recovery_observation_must_lie_within_the_run(self):
        for boundary, delta in (("started_monotonic_ns", -1), ("finished_monotonic_ns", 1)):
            with self.subTest(boundary=boundary):
                self.copy_case("recovery")
                controller = strict_load(self.run / "controller.json")
                for event in controller["events"]:
                    if event["event"] == "PRIMARY_RECOVERED":
                        event["monotonic_ns"] = controller[boundary] + delta
                put(self.run / "controller.json", controller)
                self.reseal()
                result = self.verify()
                self.assertEqual(result["assessment"]["claim_status"], "FAILED")
                self.assertIn("CLOCK_OUTSIDE_RUN", self.codes(result))

    def test_completion_time_is_a_post_export_upper_bound(self):
        result = self.verify()
        for row in result["per_obligation"]:
            self.assertGreaterEqual(row["completion_ns"], row["transition_ns"])
            self.assertIsInstance(row["durable_observed_monotonic_ns"], int)

    def test_post_export_observation_at_wall_deadline_is_accepted(self):
        controller = strict_load(self.run / "controller.json")
        contract = strict_load(self.authority / "contract.json")
        boundary = controller["started_monotonic_ns"] + contract["wall_deadline_ms"] * 1_000_000
        for event in controller["events"]:
            if event.get("event") == "BROKER_RESULT" and event.get("detail", {}).get("op") in ("fulfill", "reconcile"):
                event["monotonic_ns"] = boundary
        controller["finished_monotonic_ns"] = boundary + 1
        controller["resources"]["wall_ns"] = boundary + 1 - controller["started_monotonic_ns"]
        put(self.run / "controller.json", controller)
        self.reseal()
        result = self.verify()
        self.assertEqual(result["assessment"]["claim_status"], "DEMONSTRATED")
        self.assertTrue(all(row["completion_ns"] == contract["wall_deadline_ms"] * 1_000_000 for row in result["per_obligation"]))

    def test_missing_post_export_observation_preserves_uncertainty(self):
        controller = strict_load(self.run / "controller.json")
        controller["events"] = [event for event in controller["events"] if not
                                (event.get("event") == "BROKER_RESULT" and event.get("detail", {}).get("op") in ("fulfill", "reconcile"))]
        put(self.run / "controller.json", controller)
        self.reseal()
        result = self.verify()
        self.assertIn("DURABLE_OBSERVATION_MISSING", self.codes(result))
        self.assertEqual(result["assessment"]["claim_status"], "NOT_ESTABLISHED")
        self.assertTrue(all(row["outcome"] == "UNRESOLVED" and row["completion_ns"] is None for row in result["per_obligation"]))

    def test_late_post_export_observation_cannot_use_an_early_transition_timestamp(self):
        controller = strict_load(self.run / "controller.json")
        contract = strict_load(self.authority / "contract.json")
        late = controller["started_monotonic_ns"] + (contract["wall_deadline_ms"] + 1) * 1_000_000
        for event in controller["events"]:
            if event.get("event") == "BROKER_RESULT" and event.get("detail", {}).get("op") in ("fulfill", "reconcile"):
                event["monotonic_ns"] = late
        controller["finished_monotonic_ns"] = late + 1
        put(self.run / "controller.json", controller)
        self.reseal()
        result = self.verify()
        self.assertTrue(any(row["code"] == "WALL_DEADLINE_EXCEEDED" and row["detail"] == "post_export_upper_bound" for row in result["failures"]))
        self.assertEqual(result["assessment"]["claim_status"], "FAILED")
        self.assertTrue(all(row["outcome"] == "LATE" for row in result["per_obligation"]))

    def test_primary_must_be_recovered_before_its_allocation(self):
        db = sqlite3.connect(self.run / "evidence/service.sqlite")
        try:
            db.row_factory = sqlite3.Row
            rows = [dict(row) for row in db.execute("SELECT * FROM history ORDER BY sequence")]
            restored = next(row for row in rows if row["operation"] == "RESTORED")
            rows.remove(restored)
            rows.append(restored)
            db.execute("UPDATE history SET sequence=sequence+1000")
            previous_tick = 0
            for seq, row in enumerate(rows, 1):
                tick = max(previous_tick, row["tick"])
                db.execute("UPDATE history SET sequence=?,tick=? WHERE sequence=?", (seq, tick, row["sequence"] + 1000))
                previous_tick = tick
            db.commit()
        finally:
            db.close()
        self.reseal()
        result = self.verify()
        self.assertIn("PRIMARY_NOT_RECOVERED", self.codes(result))
        self.assertEqual(result["totals"]["accepted_units"], 0)

    def test_completion_must_fit_the_individual_reserved_window(self):
        db = sqlite3.connect(self.run / "evidence/service.sqlite")
        try:
            db.row_factory = sqlite3.Row
            row = dict(db.execute("SELECT * FROM reservations WHERE order_id='LBL-100'").fetchone())
            row["window_end"] = row["updated_tick"] - 1
            row["expires_tick"] = row["window_end"]
            request = {key: value for key, value in row.items() if key not in {"status", "request_sha256", "created_tick", "updated_tick"}}
            row["request_sha256"] = digest(request)
            db.execute("UPDATE reservations SET window_end=?,expires_tick=?,request_sha256=? WHERE key=?", (row["window_end"], row["expires_tick"], row["request_sha256"], row["key"]))
            for history in db.execute("SELECT sequence,detail FROM history WHERE order_id='LBL-100'").fetchall():
                detail = strict_loads(history["detail"])
                detail["reservation"].update(window_end=row["window_end"], expires_tick=row["expires_tick"], request_sha256=row["request_sha256"])
                db.execute("UPDATE history SET detail=? WHERE sequence=?", (canonical(detail).decode(), history["sequence"]))
            db.commit()
        finally:
            db.close()
        self.reseal()
        result = self.verify()
        self.assertTrue(any(item["code"] == "LATE_COMPLETION" and item["detail"] == "reserved_window" for item in result["failures"]))
        self.assertEqual(result["per_obligation"][0]["accepted_quantity"], 0)

    def test_missing_artifact_after_durable_receipt_is_unresolved_when_run_incomplete(self):
        (self.run / "evidence/artifacts/LBL-100.json").unlink()
        controller = strict_load(self.run / "controller.json")
        controller["state"] = "INCOMPLETE"
        put(self.run / "controller.json", controller)
        self.reseal()
        result = self.verify()
        self.assertEqual(result["assessment"]["claim_status"], "NOT_ESTABLISHED")
        self.assertIn("ARTIFACT_MISSING", self.codes(result))
        self.assertEqual(result["per_obligation"][0]["outcome"], "UNRESOLVED")

    def test_a_pending_sqlite_journal_does_not_become_a_stale_positive(self):
        (self.run / "evidence/service.sqlite-wal").write_bytes(b"pending-journal")
        self.reseal()
        result = self.verify()
        self.assertEqual(result["assessment"]["claim_status"], "NOT_ESTABLISHED")
        self.assertIn("DATABASE_NOT_CHECKPOINTED", self.codes(result))

    def test_missing_execution_seal_is_not_established(self):
        (self.authority / "execution.json").unlink()
        result = self.verify()
        self.assertEqual(result["assessment"]["claim_status"], "NOT_ESTABLISHED")
        self.assertIn("EXECUTION_SEAL_MISSING", self.codes(result))

    def test_unsealed_extra_evidence_and_unsafe_manifest_paths_fail(self):
        (self.run / "evidence/unsealed.json").write_text("{}")
        result = self.verify()
        self.assertIn("UNSEALED_EVIDENCE", self.codes(result))
        seal = strict_load(self.authority / "execution.json")
        seal["evidence_manifest"]["../authority/contract.json"] = "0" * 64
        put(self.authority / "execution.json", seal)
        result = self.verify()
        self.assertIn("UNSAFE_EVIDENCE_PATH", self.codes(result))

    def test_missing_history_transition_is_detected(self):
        db = sqlite3.connect(self.run / "evidence/service.sqlite")
        db.execute("DELETE FROM history WHERE operation='COMMITTED'")
        db.commit()
        db.close()
        self.reseal()
        result = self.verify()
        self.assertIn("LEDGER_HISTORY_INVALID", self.codes(result))
        self.assertNotEqual(result["assessment"]["claim_status"], "DEMONSTRATED")

    def test_revoked_permission_is_checked_against_completion_time(self):
        controller = strict_load(self.run / "controller.json")
        controller["events"].append({"event": "PERMISSION_REVOKED", "tick": 0,
                                     "monotonic_ns": controller["started_monotonic_ns"] + 1,
                                     "detail": {"permission": "activation"}})
        put(self.run / "controller.json", controller)
        self.reseal()
        result = self.verify()
        self.assertEqual(result["safety_status"], "FAILED")
        self.assertIn("UNAUTHORIZED_ACTIVATION", self.codes(result))

    def test_missing_fault_observation_prevents_control_pass(self):
        self.copy_case("constrained")
        controller = strict_load(self.run / "controller.json")
        controller["faults_observed"].pop()
        put(self.run / "controller.json", controller)
        self.reseal()
        result = self.verify()
        self.assertIn("FAULT_NOT_OBSERVED", self.codes(result))
        self.assertEqual(result["assessment"]["test_assertion"], "FAILED")

    def test_unknown_resource_costs_remain_unknown(self):
        result = self.verify()
        for key in ("peak_rss_bytes", "preparation_labor_seconds", "integration_labor_seconds", "monetary_cost"):
            self.assertIsNone(result["resources"][key])

    def test_verifier_exception_is_a_structured_nonfavorable_result(self):
        with patch("continuity_harness.verifier._read_database", side_effect=RuntimeError("injected verifier failure")):
            result = self.verify()
        self.assertEqual(result["assessment"]["claim_status"], "NOT_ESTABLISHED")
        self.assertEqual(result["verification_status"], "INCOMPLETE")
        self.assertIn("VERIFICATION_ERROR", self.codes(result))

    def test_ai_absence_is_not_run_not_a_mock_performance_result(self):
        root = self.root / "ai"
        run = run_exercise(make_contract(method="ai"), "ai", root / "run", root / "authority")
        result = verify_run(root / "run", root / "authority", expected_reference_sha256=run["reference_sha256"])
        self.assertEqual(result["assessment"]["test_assertion"], "NOT_RUN")
        self.assertEqual(result["assessment"]["evidence_stage"], "NOT_RUN")
        self.assertEqual(result["assessment"]["claim_status"], "NOT_ESTABLISHED")

    def test_mutation_disabling_byte_integrity_is_killed_by_changed_evidence_assertion(self):
        path = self.run / "evidence/artifacts/LBL-100.json"
        path.write_bytes(path.read_bytes() + b" ")  # same JSON meaning, different sealed bytes
        self.assertIn("EVIDENCE_CHANGED", self.codes(self.verify()))
        hashes = strict_load(self.authority / "execution.json")["evidence_manifest"]
        def ignore_current_bytes(p):
            return hashes[Path(p).relative_to(self.run).as_posix()]
        with patch("continuity_harness.verifier._file_hash", side_effect=ignore_current_bytes):
            mutant = self.verify()
        self.assertEqual(mutant["assessment"]["claim_status"], "DEMONSTRATED")
        with self.assertRaises(AssertionError):
            self.assertIn("EVIDENCE_CHANGED", self.codes(mutant))

    def test_mutation_disabling_revocation_is_killed_by_authority_assertion(self):
        controller = strict_load(self.run / "controller.json")
        controller["events"].append({"event": "PERMISSION_REVOKED", "tick": 0,
                                     "monotonic_ns": controller["started_monotonic_ns"] + 1,
                                     "detail": {"permission": "activation"}})
        put(self.run / "controller.json", controller)
        self.reseal()
        self.assertIn("UNAUTHORIZED_ACTIVATION", self.codes(self.verify()))
        with patch("continuity_harness.verifier._revoked", return_value=None):
            mutant = self.verify()
        self.assertEqual(mutant["assessment"]["claim_status"], "DEMONSTRATED")
        with self.assertRaises(AssertionError):
            self.assertIn("UNAUTHORIZED_ACTIVATION", self.codes(mutant))

    def test_mutation_rejecting_every_primary_recovery_is_killed_by_positive_control(self):
        self.assertEqual(self.verify()["assessment"]["claim_status"], "DEMONSTRATED")
        with patch("continuity_harness.verifier._source_rows", return_value=[]):
            mutant = self.verify()
        self.assertEqual(mutant["assessment"]["claim_status"], "FAILED")
        with self.assertRaises(AssertionError):
            self.assertEqual(mutant["assessment"]["claim_status"], "DEMONSTRATED")


if __name__ == "__main__":
    unittest.main()
