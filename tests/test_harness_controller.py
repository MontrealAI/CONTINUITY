"""End-to-end executable controls and common-adapter boundaries."""

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from continuity_harness.adapters import LocalAIAdapter
from continuity_harness.controller import Controller, run_exercise
from continuity_harness.fixtures import make_contract
from continuity_harness.schema import HarnessError, digest, strict_load
from continuity_harness.verifier import verify_run


class ExecutedControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory(prefix="continuity-controls-test-")
        cls.root = Path(cls.folder.name)
        cls.runs = {}
        for method in ("conventional", "harness"):
            for scenario in ("recovery", "alternate", "constrained"):
                name = f"{method}-{scenario}"
                contract = make_contract(scenario=scenario, method=method)
                run = run_exercise(contract, method, cls.root / name / "run", cls.root / name / "authority")
                result = verify_run(run["run_dir"], run["authority_dir"], expected_reference_sha256=run["reference_sha256"])
                cls.runs[(method, scenario)] = (run, result)

    @classmethod
    def tearDownClass(cls):
        cls.folder.cleanup()

    def test_both_competent_methods_execute_primary_recovery(self):
        for method in ("conventional", "harness"):
            run, result = self.runs[(method, "recovery")]
            self.assertEqual(result["assessment"]["claim_status"], "DEMONSTRATED", result)
            self.assertEqual(result["totals"]["accepted_units"], 1900)
            self.assertEqual({x["route"] for x in result["per_obligation"]}, {"primary"})
            self.assertTrue(result["ledger"]["primary_recovery_verified"])
            self.assertGreater(run["controller"]["recovery_ms"], 0)

    def test_both_methods_execute_alternate_without_claiming_primary_recovery(self):
        for method in ("conventional", "harness"):
            run, result = self.runs[(method, "alternate")]
            self.assertEqual(result["assessment"]["claim_status"], "DEMONSTRATED", result)
            self.assertEqual(result["totals"]["accepted_units"], 1900)
            self.assertEqual({x["route"] for x in result["per_obligation"]}, {"backup"})
            self.assertFalse(result["ledger"]["primary_recovery_verified"])
            self.assertIsNone(result["recovery_ms"])

    def test_constrained_test_pass_is_not_complete_promise(self):
        for method in ("conventional", "harness"):
            run, result = self.runs[(method, "constrained")]
            self.assertEqual(result["assessment"]["test_assertion"], "PASSED", result)
            self.assertEqual(result["assessment"]["claim_status"], "FAILED")
            self.assertEqual(result["safety_status"], "DEMONSTRATED")
            self.assertEqual(result["totals"]["accepted_units"], 1100)
            self.assertEqual(result["totals"]["missing_units"], 800)
            self.assertEqual(result["per_obligation"][1]["outcome"], "REFUSED")
            self.assertIn("CAPACITY_EXCEEDED", result["per_obligation"][1]["reason_codes"])

    def test_lost_ack_retry_real_kill_and_restart_are_observed(self):
        run, result = self.runs[("harness", "constrained")]
        faults = {x["event"] for x in run["controller"]["faults_observed"]}
        self.assertTrue({"CONCURRENT_FINAL_CAPACITY", "ACK_LOST_AFTER_DURABLE_FULFILLMENT",
                         "RETRY_WHILE_OUTCOME_UNKNOWN", "SERVICE_KILLED_AFTER_COMMIT",
                         "CANDIDATE_KILLED_AFTER_REQUEST", "RESTART_RECONCILIATION"} <= faults)
        self.assertEqual(run["controller"]["resources"]["worker_restarts"], 2)
        self.assertEqual(run["controller"]["resources"]["retries"], 1)
        self.assertEqual(result["totals"]["duplicate_obligations"], 0)
        self.assertEqual(len(list((Path(run["run_dir"]) / "evidence/artifacts").glob("*.json"))), 1)

    def test_kernel_isolation_is_actually_probed_for_each_method(self):
        for method in ("conventional", "harness"):
            isolation = self.runs[(method, "recovery")][0]["controller"]["isolation"]
            self.assertTrue(isolation["applied"])
            for probe in ("authority_open_denied", "workspace_open_denied", "network_denied", "spawn_denied", "process_inspection_denied"):
                self.assertIs(isolation["probe"][probe], True)

    def test_comparator_receives_same_business_conditions_and_tools(self):
        a, b = [self.runs[(m, "constrained")][0] for m in ("conventional", "harness")]
        ca = strict_load(Path(a["authority_dir"]) / "contract.json")
        cb = strict_load(Path(b["authority_dir"]) / "contract.json")
        for c in (ca, cb):
            c.pop("run_id")
        self.assertEqual(ca, cb)
        self.assertEqual(a["controller"]["faults_observed"], b["controller"]["faults_observed"])
        self.assertEqual(a["controller"]["resources"]["requests"], b["controller"]["resources"]["requests"])

    def test_no_monetary_or_labor_observation_is_invented(self):
        r = self.runs[("harness", "recovery")][1]["resources"]
        for field in ("monetary_cost", "preparation_labor_seconds", "integration_labor_seconds", "peak_rss_bytes"):
            self.assertIsNone(r[field])
        self.assertGreater(r["cpu_user_ns"] + r["cpu_system_ns"], 0)
        self.assertGreater(r["storage_bytes"], 0)


class AdapterAndTransferTests(unittest.TestCase):
    def test_same_executor_transfers_to_changed_ids_recipients_specs_and_quantities(self):
        with tempfile.TemporaryDirectory(prefix="continuity-transfer-test-") as tmp:
            c = make_contract("labels-transfer-a", "alternate")
            mapping = {"LBL-100": "NEW-ALPHA", "LBL-200": "NEW-BETA", "LBL-300": "NEW-CANCELLED"}
            for e in c["source_events"]:
                e["order_id"] = mapping[e["order_id"]]
                if "recipient" in e:
                    e["recipient"] = "OTHER-" + e["recipient"]
            c["source_sha256"] = digest(c["source_events"])
            run = run_exercise(c, "harness", Path(tmp) / "run", Path(tmp) / "authority")
            result = verify_run(run["run_dir"], run["authority_dir"], expected_reference_sha256=run["reference_sha256"])
            self.assertEqual(result["assessment"]["claim_status"], "DEMONSTRATED", result)
            self.assertEqual(result["totals"]["accepted_units"], 1600)
            self.assertEqual({x["order_id"] for x in result["per_obligation"]}, {"NEW-ALPHA", "NEW-BETA"})

    def test_coherent_candidate_rewrite_cannot_redefine_retained_contract(self):
        with tempfile.TemporaryDirectory(prefix="continuity-rewrite-test-") as tmp:
            from continuity_harness.fixtures import candidate_view
            c = make_contract(scenario="alternate")
            view = candidate_view(c)
            view["contract"]["source_events"][1]["quantity"] -= 50
            view["contract"]["source_sha256"] = digest(view["contract"]["source_events"])
            run = run_exercise(c, "harness", Path(tmp) / "run", Path(tmp) / "authority", candidate_visible=view)
            result = verify_run(run["run_dir"], run["authority_dir"], expected_reference_sha256=run["reference_sha256"])
            self.assertNotEqual(result["assessment"]["claim_status"], "DEMONSTRATED")
            self.assertEqual(result["totals"]["expected_units"], 1900)
            self.assertLess(result["totals"]["accepted_units"], 1900)

    def test_shared_failed_dependency_cannot_be_a_working_backup(self):
        with tempfile.TemporaryDirectory(prefix="continuity-dependency-test-") as tmp:
            c = make_contract(scenario="alternate")
            c["dependencies"]["backup"] = c["dependencies"]["primary"]
            run = run_exercise(c, "harness", Path(tmp) / "run", Path(tmp) / "authority")
            result = verify_run(run["run_dir"], run["authority_dir"], expected_reference_sha256=run["reference_sha256"])
            self.assertNotEqual(result["assessment"]["claim_status"], "DEMONSTRATED")
            self.assertEqual(result["totals"]["accepted_units"], 0)

    def test_ai_absence_is_not_run_not_a_mock_performance(self):
        response = LocalAIAdapter().run({}, lambda *_: self.fail("No tool should run"))
        self.assertEqual(response["verdict"], "NOT_RUN")

    def test_ai_protocol_plumbing_uses_same_tool_contract_only(self):
        calls = []
        def stub(context, history):
            # Test double only; never included in AI comparative results.
            return {"op": "orders", "args": {}} if not history else {"event": "done", "result": {"verdict": "NOT_ESTABLISHED", "reason": "PLUMBING_TEST_ONLY", "outcomes": []}}
        adapter = LocalAIAdapter(stub, capability_id="UNIT_TEST_STUB_NOT_A_MODEL")
        result = adapter.run({}, lambda op, args: calls.append((op, args)) or {"ok": True, "result": {"orders": []}})
        self.assertEqual(calls, [("orders", {})])
        self.assertEqual(result["verdict"], "NOT_ESTABLISHED")

    def test_ai_protocol_cannot_call_controller_administration(self):
        adapter = LocalAIAdapter(lambda *_: {"op": "init", "args": {}}, capability_id="UNIT_TEST_STUB_NOT_A_MODEL")
        with self.assertRaises(HarnessError):
            adapter.run({}, lambda *_: self.fail("Forbidden operation reached broker"))

    def test_existing_run_is_never_overwritten(self):
        with tempfile.TemporaryDirectory(prefix="continuity-preserve-test-") as tmp:
            folder = Path(tmp) / "run"
            folder.mkdir()
            marker = folder / "prior-evidence.txt"
            marker.write_text("preserve")
            with self.assertRaises(FileExistsError):
                run_exercise(make_contract(), "harness", folder, Path(tmp) / "authority")
            self.assertEqual(marker.read_text(), "preserve")


if __name__ == "__main__":
    unittest.main()
