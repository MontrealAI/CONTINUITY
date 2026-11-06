"""Independent adversarial controls for broker authority and process bounds.

The intentionally malicious subprocesses below are protocol tests, not AI
performance results. They use the real seccomp mechanism and real service.
"""
import fcntl
import hashlib
import json
from pathlib import Path
import platform
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from continuity_harness.controller import Controller
from continuity_harness.fixtures import make_contract
from continuity_harness.rpc import ProcessChannel
from continuity_harness.schema import HarnessError, canonical, expected_obligations
from continuity_harness.verifier import verify_run


ROOT = Path(__file__).resolve().parents[1]
LINUX_X86 = sys.platform == "linux" and platform.machine() == "x86_64"


class PipeBoundaryTests(unittest.TestCase):
    def test_large_write_to_nonreading_process_times_out(self):
        """A ready child intentionally never reads; the parent must not hang."""
        program = "import sys,select; print('{\"event\":\"ready\"}',flush=True); select.select([],[],[])"
        with tempfile.TemporaryDirectory(prefix="continuity-pipe-boundary-") as td:
            channel = ProcessChannel([sys.executable, "-c", program], ROOT, Path(td) / "stderr", timeout_ms=2000)
            try:
                self.assertEqual(channel.receive(), {"event": "ready"})
                capacity = fcntl.fcntl(channel.process.stdin.fileno(), fcntl.F_GETPIPE_SZ)
                channel.timeout_ms = 100
                payload = {"payload": "x" * min(1_000_000, capacity + 1024)}
                started = time.monotonic_ns()
                with self.assertRaises(HarnessError) as caught:
                    # The normal Linux pipe is smaller than one bounded JSON
                    # frame. A second frame also covers a larger configured pipe.
                    channel.send(payload)
                    channel.send(payload)
                elapsed = time.monotonic_ns() - started
                self.assertEqual(caught.exception.code, "PROCESS_WRITE_TIMEOUT")
                self.assertLess(elapsed, 5_000_000_000)
                self.assertIsNone(channel.process.poll())
            finally:
                channel.kill()
                channel.close()

    def test_large_frame_survives_real_partial_pipe_writes(self):
        program = ("import sys,json,hashlib; print('{\"event\":\"ready\"}',flush=True); "
                   "data=sys.stdin.buffer.readline(); "
                   "print(json.dumps({'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}),flush=True)")
        with tempfile.TemporaryDirectory(prefix="continuity-pipe-positive-") as td:
            channel = ProcessChannel([sys.executable, "-c", program], ROOT, Path(td) / "stderr", timeout_ms=5000)
            try:
                self.assertEqual(channel.receive(), {"event": "ready"})
                value = {"payload": "z" * 900_000}
                raw = canonical(value) + b"\n"
                channel.send(value)
                result = channel.receive()
                self.assertEqual(result, {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
            finally:
                channel.close()


class BrokerBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="continuity-broker-boundary-")
        self.folder = Path(self.temp.name)
        self.controllers = []

    def tearDown(self):
        for controller in self.controllers:
            for child in controller.children:
                child.close()
        self.temp.cleanup()

    def controller(self, contract=None):
        contract = contract or make_contract()
        count = str(len(self.controllers))
        controller = Controller(contract, "harness", self.folder / count / "run", self.folder / count / "authority")
        self.controllers.append(controller)
        controller.initialize()
        return controller

    def reserve(self, controller):
        obligation = expected_obligations(controller.contract)[0]
        request = {key: obligation[key] for key in ("order_id", "recipient", "product", "spec_sha256", "quantity")}
        request.update(route="backup", key="BROKER-KEY")
        response = controller.broker({"op": "reserve_batch", "args": {"requests": [request]}})
        self.assertTrue(response["ok"])
        self.assertTrue(response["result"]["results"][0]["ok"])
        return "BROKER-KEY"

    def test_malicious_restore_is_refused_when_activation_is_not_authorized(self):
        contract = make_contract()
        contract["permissions"]["activation"] = False
        controller = self.controller(contract)
        before = controller.service.call("snapshot", {})["result"]
        with self.assertRaises(HarnessError) as caught:
            controller.broker({"op": "restore", "args": {"events": contract["source_events"], "cutoff": contract["cutoff_sequence"]}})
        self.assertEqual(caught.exception.code, "PERMISSION_MISSING")
        after = controller.service.call("snapshot", {})["result"]
        self.assertEqual(after["orders"], before["orders"])
        self.assertEqual(after["history"], before["history"])
        self.assertNotIn("recovery_cutoff", after["metadata"])

    def test_primary_restore_requires_an_authorized_route(self):
        contract = make_contract()
        contract["allowed_routes"] = ["backup"]
        controller = self.controller(contract)
        with self.assertRaises(HarnessError) as caught:
            controller.broker({"op": "restore", "args": {"events": contract["source_events"], "cutoff": contract["cutoff_sequence"]}})
        self.assertEqual(caught.exception.code, "ROUTE_NOT_AUTHORIZED")
        self.assertNotIn("recovery_cutoff", controller.service.call("snapshot", {})["result"]["metadata"])

    def test_revocation_after_reserve_blocks_commit_and_allows_safe_release(self):
        controller = self.controller()
        key = self.reserve(controller)
        controller.revoke_permission("activation")
        with self.assertRaises(HarnessError) as caught:
            controller.broker({"op": "commit", "args": {"key": key}})
        self.assertEqual(caught.exception.code, "PERMISSION_MISSING")
        state = controller.service.call("snapshot", {})["result"]
        self.assertEqual(state["reservations"][0]["status"], "RESERVED")
        self.assertEqual(state["receipts"], [])
        released = controller.broker({"op": "release", "args": {"key": key}})
        self.assertTrue(released["ok"])
        self.assertEqual(released["result"]["status"], "RELEASED")
        self.assertTrue(any(e["event"] == "PERMISSION_REVOKED" for e in controller.record["events"]))

    def test_revocation_after_commit_blocks_fulfillment(self):
        controller = self.controller()
        key = self.reserve(controller)
        self.assertTrue(controller.broker({"op": "commit", "args": {"key": key}})["ok"])
        controller.revoke_permission("sharing")
        with self.assertRaises(HarnessError) as caught:
            controller.broker({"op": "fulfill", "args": {"key": key}})
        self.assertEqual(caught.exception.code, "PERMISSION_MISSING")
        state = controller.service.call("snapshot", {})["result"]
        self.assertEqual(state["reservations"][0]["status"], "COMMITTED")
        self.assertEqual(state["receipts"], [])
        self.assertFalse(list(controller.artifacts.glob("*.json")))

    def test_changed_dependency_blocks_later_commit(self):
        controller = self.controller()
        key = self.reserve(controller)
        controller.blocked_dependencies.add(controller.contract["dependencies"]["backup"])
        with self.assertRaises(HarnessError) as caught:
            controller.broker({"op": "commit", "args": {"key": key}})
        self.assertEqual(caught.exception.code, "DEPENDENCY_UNAVAILABLE")
        self.assertEqual(controller.service.call("snapshot", {})["result"]["receipts"], [])

    def test_malformed_action_arguments_are_structured_refusals(self):
        controller = self.controller()
        for operation in ("commit", "fulfill", "restore", "reserve_batch"):
            for bad in (None, [], 0, "invalid"):
                with self.subTest(operation=operation, bad=bad), self.assertRaises(HarnessError):
                    controller.broker({"op": operation, "args": bad})
        self.assertEqual(controller.service.call("snapshot", {})["result"]["receipts"], [])


@unittest.skipUnless(LINUX_X86, "The registered candidate isolation requires Linux x86-64.")
class CandidateProcessBoundaryTests(unittest.TestCase):
    HEADER = '''
import json,sys
from continuity_harness.sandbox import activate
from continuity_harness.schema import canonical,strict_loads
def emit(value):
 sys.stdout.buffer.write(canonical(value)+b"\\n")
 sys.stdout.buffer.flush()
emit({"event":"sandbox","isolation":activate(sys.argv[1],sys.argv[2])})
initial=strict_loads(sys.stdin.buffer.readline(1048577))
'''

    def run_candidate(self, body):
        temp = tempfile.TemporaryDirectory(prefix="continuity-candidate-boundary-")
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        original = ProcessChannel
        def channel(command, cwd, stderr_path, **kwargs):
            authority = command[command.index("--authority-probe") + 1]
            workspace = command[command.index("--workspace-probe") + 1]
            return original([sys.executable, "-c", self.HEADER + body, authority, workspace], cwd, stderr_path, **kwargs)
        controller = Controller(make_contract(), "harness", root / "run", root / "authority")
        with patch("continuity_harness.controller.ProcessChannel", side_effect=channel):
            result = controller.run()
        for child in controller.children:
            self.assertIsNotNone(child.process.poll(), "The controller must clean up each owned process")
        return result

    def test_endless_valid_requests_stop_at_the_declared_budget(self):
        body = '''
while True:
 emit({"op":"orders","args":{}})
 data=sys.stdin.buffer.readline(1048577)
 if not data: break
'''
        result = self.run_candidate(body)
        record = result["controller"]
        self.assertEqual(record["state"], "ERROR")
        self.assertEqual(record["target_verdict"], "ERROR")
        self.assertIn("REQUEST_BUDGET_EXCEEDED", [item["code"] for item in record["errors"]])
        self.assertEqual(record["resources"]["requests"], 129)
        self.assertTrue(Path(result["run_dir"], "controller.json").is_file())
        self.assertTrue(Path(result["authority_dir"], "execution.json").is_file())
        verdict = verify_run(result["run_dir"], result["authority_dir"], expected_reference_sha256=result["reference_sha256"])
        self.assertNotEqual(verdict["assessment"]["claim_status"], "DEMONSTRATED")

    def test_malformed_candidate_frame_cannot_become_complete(self):
        result = self.run_candidate("emit(None)\n")
        self.assertEqual(result["controller"]["state"], "ERROR")
        self.assertTrue(result["controller"]["errors"])

    def test_malformed_done_verdict_cannot_become_complete(self):
        result = self.run_candidate('emit({"event":"done","result":{"verdict":True,"reason":"invalid","outcomes":[]}})\n')
        self.assertEqual(result["controller"]["state"], "ERROR")
        self.assertTrue(result["controller"]["errors"])

    def test_done_frame_followed_by_nonzero_exit_is_an_error(self):
        result = self.run_candidate('emit({"event":"done","result":{"verdict":"COMPLETED","reason":"DECLARED_ONLY","outcomes":[]}})\nraise SystemExit(7)\n')
        self.assertEqual(result["controller"]["state"], "ERROR")
        self.assertIn("CANDIDATE_EXIT_ERROR", [item["code"] for item in result["controller"]["errors"]])

    def test_restart_reconciliation_conflict_is_not_target_completion(self):
        with tempfile.TemporaryDirectory(prefix="continuity-reconcile-boundary-") as td:
            root = Path(td)
            controller = Controller(make_contract(scenario="constrained"), "harness", root / "run", root / "authority")
            original_start = controller.start_candidate
            changed = []

            def corrupt_before_restart(restart=False):
                if restart:
                    outputs = list(controller.artifacts.glob("*.json"))
                    self.assertEqual(len(outputs), 1)
                    outputs[0].write_bytes(b"CONFLICTING ARTIFACT\n")
                    changed.append(outputs[0])
                original_start(restart)

            with patch.object(controller, "start_candidate", side_effect=corrupt_before_restart):
                result = controller.run()
            self.assertEqual(len(changed), 1)
            self.assertEqual(changed[0].read_bytes(), b"CONFLICTING ARTIFACT\n")
            self.assertNotEqual(result["controller"]["target_verdict"], "COMPLETED")
            finished = [event for event in result["controller"]["events"] if event["event"] == "CANDIDATE_FINISHED"]
            self.assertEqual(finished[-1]["detail"]["reason"], "RECONCILIATION_INCOMPLETE")
            verified = verify_run(root / "run", root / "authority", expected_reference_sha256=result["reference_sha256"])
            self.assertNotEqual(verified["assessment"]["claim_status"], "DEMONSTRATED")

    def test_backup_only_authorization_transfers_to_both_competent_methods(self):
        with tempfile.TemporaryDirectory(prefix="continuity-backup-authority-") as td:
            root = Path(td)
            for method in ("conventional", "harness"):
                with self.subTest(method=method):
                    contract = make_contract(method=method)
                    contract["allowed_routes"] = ["backup"]
                    controller = Controller(contract, method, root / method / "run", root / method / "authority")
                    result = controller.run()
                    self.assertEqual(result["controller"]["target_verdict"], "COMPLETED")
                    outputs = [json.loads(path.read_bytes()) for path in controller.artifacts.glob("*.json")]
                    self.assertEqual(sum(output["quantity"] for output in outputs), 1900)
                    self.assertEqual({output["route"] for output in outputs}, {"backup"})


if __name__ == "__main__":
    unittest.main()
