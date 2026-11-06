"""Regression controls for route permissions and lease-aware queue scheduling."""
from pathlib import Path
import tempfile
import unittest

from continuity_harness.controller import Controller, run_exercise
from continuity_harness.fixtures import make_contract
from continuity_harness.schema import HarnessError, digest, expected_obligations
from continuity_harness.verifier import verify_run


class RouteQueueRegressionTests(unittest.TestCase):
    def run_control(self, contract, method):
        folder = tempfile.TemporaryDirectory(prefix="continuity-route-queue-")
        self.addCleanup(folder.cleanup)
        root = Path(folder.name)
        run = run_exercise(contract, method, root / "run", root / "authority")
        result = verify_run(run["run_dir"], run["authority_dir"], expected_reference_sha256=run["reference_sha256"])
        return run, result

    def queue_contract(self, count, scenario, lease=20):
        c = make_contract(scenario=scenario)
        c["source_events"] = [dict(sequence=i, type="ACCEPT", order_id=f"ORDER-{i:02}",
            recipient=f"CUSTOMER-{i:02}", product="LABEL-A", spec_sha256="ab" * 32,
            quantity=10, deadline_tick=100) for i in range(1, count + 1)]
        c["cutoff_sequence"] = count
        c["source_sha256"] = digest(c["source_events"])
        c["lease_ticks"] = lease
        return c

    def test_primary_without_backup_sharing_completes_for_both_methods(self):
        for method in ("conventional", "harness"):
            with self.subTest(method=method):
                c = make_contract()
                c["permissions"]["sharing"] = False
                run, result = self.run_control(c, method)
                self.assertEqual(result["assessment"]["claim_status"], "DEMONSTRATED", result)
                self.assertEqual(result["totals"]["accepted_units"], 1900)
                self.assertEqual({x["route"] for x in result["per_obligation"]}, {"primary"})

    def test_backup_without_sharing_is_refused_before_reservation(self):
        for method in ("conventional", "harness"):
            with self.subTest(method=method):
                c = make_contract(scenario="alternate")
                c["permissions"]["sharing"] = False
                run, result = self.run_control(c, method)
                self.assertEqual(result["totals"]["accepted_units"], 0)
                self.assertNotEqual(result["assessment"]["claim_status"], "DEMONSTRATED")
                requests = [e["detail"]["op"] for e in run["controller"]["events"] if e["event"] == "CANDIDATE_REQUEST"]
                self.assertNotIn("reserve_batch", requests)

    def test_feasible_queues_complete_without_extending_leases(self):
        for method in ("conventional", "harness"):
            for scenario in ("recovery", "alternate"):
                for count, lease in ((7, 20), (20, 20), (7, 3), (7, 6)):
                    with self.subTest(method=method, scenario=scenario, count=count, lease=lease):
                        run, result = self.run_control(self.queue_contract(count, scenario, lease), method)
                        self.assertEqual(result["assessment"]["claim_status"], "DEMONSTRATED", result)
                        self.assertEqual(result["totals"]["accepted_units"], count * 10)
                        self.assertEqual(result["totals"]["duplicate_obligations"], 0)
                        self.assertLessEqual(run["controller"]["resources"]["requests"], 128)
                        import sqlite3
                        with sqlite3.connect(Path(run["run_dir"]) / "evidence/service.sqlite") as db:
                            rows = db.execute("SELECT expires_tick-created_tick,status FROM reservations").fetchall()
                        self.assertEqual(rows, [(lease, "FULFILLED")] * count)

    def test_too_short_lease_remains_real_expiry(self):
        for method in ("conventional", "harness"):
            for lease in (1, 2):
                with self.subTest(method=method, lease=lease):
                    run, result = self.run_control(self.queue_contract(1, "alternate", lease), method)
                    self.assertEqual(result["totals"]["accepted_units"], 0)
                    self.assertNotEqual(result["assessment"]["claim_status"], "DEMONSTRATED")
                    codes = [e["detail"]["response"].get("code") for e in run["controller"]["events"] if e["event"] == "BROKER_RESULT"]
                    self.assertIn("RESERVATION_EXPIRED", codes)


class RoutePermissionBrokerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="continuity-route-permissions-")
        self.c = Controller(make_contract(), "harness", Path(self.tmp.name) / "run", Path(self.tmp.name) / "authority")
        self.c.initialize()
        self.c.broker({"op": "restore", "args": {"events": self.c.contract["source_events"], "cutoff": self.c.contract["cutoff_sequence"]}})

    def tearDown(self):
        for child in self.c.children:
            child.close()
        self.tmp.cleanup()

    def request(self, route, index=0):
        order = expected_obligations(self.c.contract)[index]
        return {k: order[k] for k in ("order_id", "recipient", "product", "spec_sha256", "quantity")} | {"route": route, "key": f"KEY-{index}"}

    def test_sharing_revocation_does_not_block_primary_transitions(self):
        request = self.request("primary")
        self.c.broker({"op": "reserve_batch", "args": {"requests": [request]}})
        self.c.revoke_permission("sharing")
        for op in ("commit", "fulfill"):
            self.assertTrue(self.c.broker({"op": op, "args": {"key": request["key"]}})["ok"])
        self.assertEqual(len(self.c.service.call("snapshot", {})["result"]["receipts"]), 1)

    def test_mixed_batch_has_no_service_effect_when_backup_is_forbidden(self):
        self.c.revoke_permission("sharing")
        before = self.c.service.call("snapshot", {})["result"]
        with self.assertRaises(HarnessError) as caught:
            self.c.broker({"op": "reserve_batch", "args": {"requests": [self.request("primary"), self.request("backup", 1)]}})
        self.assertEqual(caught.exception.code, "PERMISSION_MISSING")
        after = self.c.service.call("snapshot", {})["result"]
        self.assertEqual(after["reservations"], before["reservations"])
        self.assertEqual(after["history"], before["history"])
        self.assertEqual(self.c.reservations, {})

    def test_conflicting_key_in_batch_has_no_partial_service_effect(self):
        first = self.request("primary")
        for second in (self.request("primary", 1), self.request("backup")):
            with self.subTest(second=second):
                second["key"] = first["key"]
                with self.assertRaises(HarnessError) as caught:
                    self.c.broker({"op": "reserve_batch", "args": {"requests": [first, second]}})
                self.assertEqual(caught.exception.code, "IDEMPOTENCY_CONFLICT")
                self.assertEqual(self.c.reservations, {})
                self.assertEqual(self.c.service.call("snapshot", {})["result"]["reservations"], [])

    def test_sharing_revocation_blocks_backup_commit_and_allows_release(self):
        request = self.request("backup")
        self.c.broker({"op": "reserve_batch", "args": {"requests": [request]}})
        self.c.revoke_permission("sharing")
        with self.assertRaises(HarnessError) as caught:
            self.c.broker({"op": "commit", "args": {"key": request["key"]}})
        self.assertEqual(caught.exception.code, "PERMISSION_MISSING")
        self.assertTrue(self.c.broker({"op": "release", "args": {"key": request["key"]}})["ok"])
        self.assertEqual(self.c.service.call("snapshot", {})["result"]["receipts"], [])
