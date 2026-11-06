"""A quiescent SQLite snapshot is durable evidence; live WAL files are not.

These tests use new disposable runs/copies. They never repair or reopen a
previous registered experiment for writing. Synthetic test mutations are
separate from the observed comparison whose sidecars exposed this boundary.
"""

from copy import deepcopy
import hashlib
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from continuity_harness.controller import Controller
from continuity_harness.fixtures import make_contract
from continuity_harness.rpc import ServiceClient
from continuity_harness.schema import HarnessError, canonical, strict_load
from continuity_harness.verifier import verify_run


class ObservedController(Controller):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.finalize_calls = 0
        self.process_codes_at_finalization = None

    def finalize_database(self):
        self.finalize_calls += 1
        self.process_codes_at_finalization = [child.process.poll() for child in self.children]
        return super().finalize_database()


def read_rows(path, *, immutable=False):
    suffix = "?mode=ro&immutable=1" if immutable else "?mode=ro"
    connection = sqlite3.connect(Path(path).as_uri() + suffix, uri=True)
    try:
        names = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        result = {}
        for name in names:
            quoted = '"' + name.replace('"', '""') + '"'
            result[name] = sorted(connection.execute("SELECT * FROM " + quoted).fetchall(), key=repr)
        return result
    finally:
        connection.close()


class DatabaseFinalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory(prefix="continuity-finalization-control-")
        cls.root = Path(cls.folder.name)
        cls.controller = ObservedController(make_contract(scenario="constrained"), "harness",
                                            cls.root / "run", cls.root / "authority")
        cls.executed_run = cls.controller.run()
        if cls.executed_run["controller"]["state"] != "COMPLETE":
            raise AssertionError(cls.executed_run["controller"]["errors"])

    @classmethod
    def tearDownClass(cls):
        cls.folder.cleanup()

    def setUp(self):
        self.work = tempfile.TemporaryDirectory(prefix="continuity-finalization-case-")
        self.case = Path(self.work.name)

    def tearDown(self):
        self.work.cleanup()

    def copy_case(self):
        shutil.copytree(self.root / "run", self.case / "run")
        shutil.copytree(self.root / "authority", self.case / "authority")
        return self.case / "run", self.case / "authority"

    def verify(self, run, authority):
        return verify_run(run, authority, expected_reference_sha256=self.executed_run["reference_sha256"])

    def test_all_owned_workers_have_exited_before_snapshot(self):
        codes = self.controller.process_codes_at_finalization
        self.assertEqual(self.controller.finalize_calls, 1)
        self.assertTrue(codes)
        self.assertTrue(all(code is not None for code in codes), codes)
        self.assertIn(-9, codes)  # The declared crash was a real process kill.
        self.assertTrue(all(child.process.poll() is not None for child in self.controller.children))
        self.assertIn("DATABASE_EVIDENCE_FINALIZED", {event["event"] for event in self.executed_run["controller"]["events"]})

    def test_standalone_delete_snapshot_contains_the_durable_source_state(self):
        controller = self.controller
        self.assertEqual(controller.db.parent, controller.run_dir / "runtime")
        self.assertEqual(controller.evidence_db, controller.run_dir / "evidence/service.sqlite")
        self.assertEqual(controller.evidence_db.read_bytes()[18:20], b"\x01\x01")
        self.assertEqual(read_rows(controller.evidence_db, immutable=True), read_rows(controller.db))
        for suffix in ("-wal", "-shm", "-journal"):
            self.assertFalse(Path(str(controller.evidence_db) + suffix).exists())
        result = self.verify(controller.run_dir, controller.authority_dir)
        self.assertEqual(result["assessment"]["test_assertion"], "PASSED", result)
        self.assertEqual(result["totals"]["accepted_units"], 1100)
        self.assertEqual(result["per_obligation"][1]["outcome"], "REFUSED")

    def test_backup_includes_committed_wal_left_by_exited_writer(self):
        controller = ObservedController(deepcopy(self.controller.contract), "harness",
                                        self.case / "run", self.case / "authority")
        shutil.copyfile(self.controller.evidence_db, controller.db)
        program = """import os, sqlite3, sys
c = sqlite3.connect(sys.argv[1])
c.execute('PRAGMA journal_mode=WAL')
c.execute('PRAGMA synchronous=FULL')
c.execute("INSERT INTO metadata VALUES ('snapshot_test_marker', '314159')")
c.commit()
os._exit(0)
"""
        subprocess.run([sys.executable, "-c", program, str(controller.db)], check=True, timeout=10)
        wal = Path(str(controller.db) + "-wal")
        self.assertGreater(wal.stat().st_size, 0)
        before = dict(read_rows(controller.db, immutable=True)["metadata"])
        self.assertNotIn("snapshot_test_marker", before)
        controller.final_service_snapshot = deepcopy(self.controller.final_service_snapshot)
        controller.final_service_snapshot["metadata"]["snapshot_test_marker"] = 314159
        controller.finalize_database()
        after = dict(read_rows(controller.evidence_db, immutable=True)["metadata"])
        self.assertEqual(after["snapshot_test_marker"], "314159")
        self.assertEqual(controller.evidence_db.read_bytes()[18:20], b"\x01\x01")
        self.assertFalse(Path(str(controller.evidence_db) + "-wal").exists())

    def test_later_runtime_wal_cannot_change_sealed_evidence(self):
        run, authority = self.copy_case()
        evidence = run / "evidence/service.sqlite"
        before = hashlib.sha256(evidence.read_bytes()).hexdigest()
        connection = sqlite3.connect(run / "runtime/service.sqlite")
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("UPDATE metadata SET value='999' WHERE key='last_tick'")
            connection.commit()
            self.assertGreater((run / "runtime/service.sqlite-wal").stat().st_size, 0)
            result = self.verify(run, authority)
            self.assertEqual(result["assessment"]["test_assertion"], "PASSED", result)
            self.assertEqual(result["totals"]["accepted_units"], 1100)
            self.assertEqual(hashlib.sha256(evidence.read_bytes()).hexdigest(), before)
            self.assertNotEqual(dict(read_rows(evidence, immutable=True)["metadata"])["last_tick"], "999")
        finally:
            connection.close()

    def test_even_resealed_wal_beside_evidence_is_not_ignored(self):
        run, authority = self.copy_case()
        connection = sqlite3.connect(run / "runtime/service.sqlite")
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("UPDATE metadata SET value='999' WHERE key='last_tick'")
            connection.commit()
            data = (run / "runtime/service.sqlite-wal").read_bytes()
            self.assertTrue(data)
            (run / "evidence/service.sqlite-wal").write_bytes(data)
        finally:
            connection.close()
        # Privileged fixture reseal isolates the verifier's pending-WAL guard.
        # This does not grant the ordinary candidate authority to reseal files.
        seal = strict_load(authority / "execution.json")
        seal["evidence_manifest"]["evidence/service.sqlite-wal"] = hashlib.sha256(data).hexdigest()
        (authority / "execution.json").write_bytes(canonical(seal) + b"\n")
        result = self.verify(run, authority)
        self.assertNotEqual(result["assessment"]["test_assertion"], "PASSED")
        self.assertNotEqual(result["assessment"]["claim_status"], "DEMONSTRATED")
        self.assertIn("DATABASE_NOT_CHECKPOINTED", {item["code"] for item in result["unresolved"]})

    def test_failed_snapshot_never_marks_execution_complete(self):
        class FailedFinalization(ObservedController):
            def finalize_database(self):
                self.finalize_calls += 1
                raise HarnessError("SNAPSHOT_TEST_FAILURE")

        controller = FailedFinalization(make_contract(), "harness", self.case / "run", self.case / "authority")
        result = controller.run()
        self.assertEqual(controller.finalize_calls, 1)
        self.assertEqual(result["controller"]["state"], "ERROR")
        self.assertIn("SNAPSHOT_TEST_FAILURE", {item["code"] for item in result["controller"]["errors"]})
        verified = verify_run(result["run_dir"], result["authority_dir"],
                              expected_reference_sha256=result["reference_sha256"])
        self.assertNotEqual(verified["assessment"]["claim_status"], "DEMONSTRATED")
        self.assertTrue(all(child.process.poll() is not None for child in controller.children))

    def test_postclose_state_change_cannot_replace_captured_service_state(self):
        class ChangedFinalization(ObservedController):
            def finalize_database(self):
                connection = sqlite3.connect(self.db)
                try:
                    connection.execute("UPDATE metadata SET value='999' WHERE key='last_tick'")
                    connection.commit()
                finally:
                    connection.close()
                return super().finalize_database()

        controller = ChangedFinalization(make_contract(), "harness", self.case / "run", self.case / "authority")
        result = controller.run()
        self.assertEqual(result["controller"]["state"], "ERROR")
        self.assertIn("DATABASE_STATE_CHANGED_DURING_FINALIZATION", {item["code"] for item in result["controller"]["errors"]})
        self.assertFalse(controller.evidence_db.exists())
        verified = verify_run(result["run_dir"], result["authority_dir"],
                              expected_reference_sha256=result["reference_sha256"])
        self.assertNotEqual(verified["assessment"]["claim_status"], "DEMONSTRATED")

    def test_backup_progress_deadline_refuses_to_publish_incomplete_snapshot(self):
        controller = ObservedController(deepcopy(self.controller.contract), "harness",
                                        self.case / "run", self.case / "authority")
        shutil.copyfile(self.controller.evidence_db, controller.db)
        controller.final_service_snapshot = deepcopy(self.controller.final_service_snapshot)
        with patch("continuity_harness.controller.time.monotonic_ns", side_effect=[0, 10_000_000_001]):
            with self.assertRaises(HarnessError) as error:
                controller.finalize_database()
        self.assertEqual(error.exception.code, "DATABASE_SNAPSHOT_TIMEOUT")
        self.assertFalse(controller.evidence_db.exists())

    def test_legacy_ok_true_busy_checkpoint_is_refused_before_finalization(self):
        original = ServiceClient.call
        intercepted = []

        def busy_checkpoint(client, op, *args, **kwargs):
            if op == "checkpoint":
                intercepted.append(op)
                return {"ok": True, "result": {"status": "CHECKPOINT_BUSY", "sqlite": [1, 3, 1]}}
            return original(client, op, *args, **kwargs)

        controller = ObservedController(make_contract(), "harness", self.case / "run", self.case / "authority")
        with patch.object(ServiceClient, "call", busy_checkpoint):
            result = controller.run()
        self.assertEqual(intercepted, ["checkpoint"])
        self.assertEqual(result["controller"]["state"], "ERROR")
        self.assertEqual(controller.finalize_calls, 0)
        self.assertTrue(any("CHECKPOINT" in item["code"] for item in result["controller"]["errors"]))
        self.assertFalse(controller.evidence_db.exists())


if __name__ == "__main__":
    unittest.main()
