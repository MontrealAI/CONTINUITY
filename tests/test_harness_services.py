"""Real local process, transaction, interruption and finite ledger controls.

No comparison results are asserted here. These tests exercise bounded software
properties; the finite trace test declares its exact alphabet and horizon.
"""
from copy import deepcopy
import hashlib
import itertools
import json
import os
from pathlib import Path
import selectors
import sqlite3
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from continuity_harness.service import Service, Refusal, canonical, decode, digest


ROOT = Path(__file__).resolve().parents[1]
SPEC = "ab" * 32
CONTRACT = "cd" * 32


def order(oid, quantity=1, deadline=100):
    return {"order_id": oid, "recipient": "CUSTOMER-" + oid, "product": "LABEL-A",
            "spec_sha256": SPEC, "quantity": quantity, "deadline_tick": deadline}


def fixture(capacity=2100):
    a, b, c = order("A", 1000), order("B", 800), order("C", 600)
    events = [{"sequence": i, "type": "ACCEPT", **record} for i, record in enumerate((a, b, c), 1)]
    events.extend([{"sequence": 4, "type": "AMEND", "order_id": "A", "quantity": 1100},
                   {"sequence": 5, "type": "CANCEL", "order_id": "C"}])
    init = {"run_id": "RUN-001", "contract_sha256": CONTRACT,
            "capacities": {"primary": 3000, "backup": capacity},
            "allowed_orders": [order("A", 1100), b], "snapshot": [a, c],
            "window_start": 0, "window_end": 100, "source_sha256": digest(events)}
    return init, events


def reservation(record, key=None, route="backup", now=0, start=0, end=100, expires=20):
    return {"run_id": "RUN-001", "contract_sha256": CONTRACT,
            **{name: record[name] for name in ("order_id", "recipient", "product", "spec_sha256", "quantity")},
            "route": route, "key": key or "KEY-" + record["order_id"], "window_start": start,
            "window_end": end, "expires_tick": expires, "now_tick": now}


class Client:
    def __init__(self, database, artifacts):
        self.process = subprocess.Popen([sys.executable, "-m", "continuity_harness.service", "--db", str(database),
                                         "--artifacts", str(artifacts)], cwd=ROOT, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.counter = 0
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)

    def write(self, value):
        self.process.stdin.write(canonical(value) + b"\n")
        self.process.stdin.flush()

    def send(self, op, args, hooks=()):
        self.counter += 1
        self.write({"id": self.counter, "op": op, "args": args, "hooks": list(hooks)})

    def read(self):
        if not self.selector.select(10):
            self.kill()
            raise AssertionError("Service response timed out")
        raw = self.process.stdout.readline()
        if not raw:
            raise AssertionError("Service exited before a response: " + self.process.stderr.read().decode())
        return json.loads(raw)

    def call(self, op, args):
        self.send(op, args)
        return self.read()

    def resume(self):
        self.write({"continue": True})

    def kill(self):
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait(timeout=10)

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.close()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.kill()
        self.selector.close()
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            if stream and not stream.closed:
                stream.close()


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="continuity-service-")
        self.folder = Path(self.temp.name)
        self.database = self.folder / "service.sqlite"
        self.artifacts = self.folder / "artifacts"
        self.service = Service(self.database, self.artifacts)
        self.init, self.events = fixture()
        self.service.dispatch("init", self.init)

    def tearDown(self):
        if self.service is not None:
            self.service.close()
        self.temp.cleanup()

    def assertRefusal(self, code, op, args):
        with self.assertRaises(Refusal) as caught:
            self.service.dispatch(op, args)
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(set(caught.exception.detail), {"en", "fr"})

    def reserve(self, oid="A", **kwargs):
        record = next(row for row in self.init["allowed_orders"] if row["order_id"] == oid)
        request = reservation(record, **kwargs)
        return self.service.dispatch("reserve", request)

    def fulfill(self, oid="A", now=1):
        key = "KEY-" + oid
        self.service.dispatch("commit", {"key": key, "now_tick": now})
        return self.service.dispatch("fulfill", {"key": key, "now_tick": now})

    def test_recovery_reconstructs_amendment_missing_order_and_cancellation(self):
        result = self.service.dispatch("restore", {"events": self.events, "cutoff": 5})
        self.assertEqual([(o["order_id"], o["quantity"]) for o in result["orders"]], [("A", 1100), ("B", 800)])
        self.assertEqual({(d["order_id"], d["code"]) for d in result["discrepancies"]},
                         {("A", "STALE_ORDER"), ("B", "MISSING_ORDER"), ("C", "RESURRECTED_CANCELLATION")})
        self.assertEqual(self.service.dispatch("orders", {})["orders"], self.init["allowed_orders"])
        self.reserve(route="primary")
        result = self.fulfill()
        self.assertEqual(result["receipt"]["route"], "primary")
        self.assertEqual(json.loads((self.artifacts / "A.json").read_text())["quantity"], 1100)

    def test_primary_requires_actual_recovery(self):
        self.assertRefusal("PRIMARY_NOT_RECOVERED", "reserve", reservation(self.init["allowed_orders"][0], route="primary"))
        self.assertEqual(self.service.dispatch("snapshot", {})["reservations"], [])

    def test_primary_rechecks_recovered_rows_before_fulfillment(self):
        self.service.dispatch("restore", {"events": self.events, "cutoff": 5})
        self.reserve(route="primary")
        self.service.dispatch("commit", {"key": "KEY-A", "now_tick": 1})
        self.service.db.execute("UPDATE orders SET quantity=1099 WHERE order_id='A'")
        self.assertRefusal("PRIMARY_NOT_RECOVERED", "fulfill", {"key": "KEY-A", "now_tick": 2})
        self.assertEqual(self.service.dispatch("snapshot", {})["receipts"], [])

    def test_alternate_route_executes_with_primary_disabled(self):
        self.service.dispatch("disable_route", {"route": "primary"})
        self.assertRefusal("ROUTE_UNAVAILABLE", "restore", {"events": self.events, "cutoff": 5})
        for oid in ("A", "B"):
            self.reserve(oid)
        for oid in ("A", "B"):
            self.fulfill(oid)
        self.assertEqual(sum(json.loads(p.read_text())["quantity"] for p in self.artifacts.glob("*.json")), 1900)
        self.assertEqual(len(self.service.dispatch("snapshot", {})["receipts"]), 2)

    def test_resealed_1850_source_does_not_redefine_protected_obligations(self):
        changed = deepcopy(self.events)
        changed[1]["quantity"] -= 50
        self.assertNotEqual(digest(changed), self.init["source_sha256"])
        self.assertRefusal("SOURCE_MISMATCH", "restore", {"events": changed, "cutoff": 5})
        request = reservation({**self.init["allowed_orders"][1], "quantity": 750})
        self.assertRefusal("UNAUTHORIZED_OBLIGATION", "reserve", request)
        self.assertFalse(list(self.artifacts.glob("*.json")))

    def test_invalid_fields_and_types_do_not_mutate_ledger(self):
        original = self.service.dispatch("snapshot", {})
        good = reservation(self.init["allowed_orders"][0])
        mutations = [("quantity", True, "INVALID_INTEGER"), ("quantity", "1100", "INVALID_INTEGER"),
                     ("quantity", -1, "INVALID_INTEGER"), ("quantity", 1.0, "INVALID_INTEGER"),
                     ("quantity", 10**10, "INVALID_INTEGER"), ("route", [], "INVALID_ROUTE"),
                     ("order_id", "../A", "INVALID_IDENTIFIER"), ("spec_sha256", "abc", "INVALID_DIGEST")]
        for field, value, expected in mutations:
            with self.subTest(field=field, value=value):
                self.assertRefusal(expected, "reserve", {**good, field: value})
        self.assertRefusal("INVALID_FIELDS", "reserve", {**good, "offer_minor": True})
        self.assertEqual(self.service.dispatch("snapshot", {}), original)

    def test_duplicate_nonfinite_and_malformed_json_refused(self):
        for raw, code in [(b'{"x":1,"x":2}', "DUPLICATE_JSON_KEY"), (b'{"x":NaN}', "NONFINITE_VALUE"),
                          (b'{"x":Infinity}', "NONFINITE_VALUE"), (b'{', "MALFORMED_JSON")]:
            with self.subTest(raw=raw), self.assertRaises(Refusal) as caught:
                decode(raw)
            self.assertEqual(caught.exception.code, code)
        self.assertRefusal("INVALID_STRUCTURE", "reserve", None)

    def test_changed_initialization_is_refused(self):
        self.assertEqual(self.service.dispatch("init", self.init)["status"], "ALREADY_INITIALIZED")
        changed = deepcopy(self.init)
        changed["allowed_orders"][0]["quantity"] -= 50
        self.assertRefusal("INIT_CONFLICT", "init", changed)

    def test_missing_update_duplicate_or_reordered_event_refused(self):
        self.assertRefusal("INCOMPLETE_SOURCE", "restore", {"events": self.events[:-1], "cutoff": 5})
        changed = deepcopy(self.events)
        changed[3]["sequence"] = 3
        self.assertRefusal("EVENT_SEQUENCE", "restore", {"events": changed, "cutoff": 5})
        changed = deepcopy(self.events)
        changed[0]["quantity"] = "1000"
        self.assertRefusal("INVALID_INTEGER", "restore", {"events": changed, "cutoff": 5})

    def test_receipt_hash_binds_exact_artifact_bytes_and_retry_is_identical(self):
        self.reserve()
        result = self.fulfill()
        data = (self.artifacts / "A.json").read_bytes()
        self.assertEqual(result["artifact_sha256"], hashlib.sha256(data).hexdigest())
        retry = self.service.dispatch("fulfill", {"key": "KEY-A", "now_tick": 2})
        self.assertEqual(retry["receipt"], result["receipt"])
        self.assertEqual((self.artifacts / "A.json").read_bytes(), data)
        self.assertEqual(len(self.service.dispatch("snapshot", {})["receipts"]), 1)

    def test_matching_artifact_retry_reestablishes_file_and_directory_durability(self):
        self.reserve()
        first = self.fulfill()
        real_sync = os.fsync
        observed = []

        def record_sync(descriptor):
            mode = os.fstat(descriptor).st_mode
            observed.append("file" if stat.S_ISREG(mode) else "directory" if stat.S_ISDIR(mode) else "other")
            return real_sync(descriptor)

        with patch("continuity_harness.service.os.fsync", side_effect=record_sync):
            retry = self.service.dispatch("fulfill", {"key": "KEY-A", "now_tick": 2})
        self.assertEqual(observed, ["file", "directory"])
        self.assertEqual(retry["receipt"], first["receipt"])
        self.assertEqual(retry["artifact_sha256"], first["artifact_sha256"])
        self.assertEqual(len(self.service.dispatch("snapshot", {})["receipts"]), 1)

        # A filesystem sync error cannot be mistaken for a successful retry.
        with patch("continuity_harness.service.os.fsync", side_effect=OSError("INJECTED_SYNC_FAILURE")):
            with self.assertRaises(OSError):
                self.service.dispatch("fulfill", {"key": "KEY-A", "now_tick": 3})
        self.assertEqual((self.artifacts / "A.json").read_bytes(), canonical(first["receipt"]) + b"\n")

    def test_same_key_different_payload_refused(self):
        self.reserve()
        self.assertRefusal("IDEMPOTENCY_CONFLICT", "reserve", reservation(self.init["allowed_orders"][1], key="KEY-A"))
        self.assertEqual(len(self.service.dispatch("snapshot", {})["reservations"]), 1)

    def test_duplicate_obligation_across_routes_refused(self):
        self.reserve()
        self.assertRefusal("OBLIGATION_IN_FLIGHT", "reserve", reservation(self.init["allowed_orders"][0], key="OTHER", route="primary"))
        self.fulfill()
        self.assertRefusal("ALREADY_FULFILLED", "reserve", reservation(self.init["allowed_orders"][0], key="OTHER", route="primary", now=1))
        self.assertEqual(len(self.service.dispatch("snapshot", {})["receipts"]), 1)

    def test_release_is_idempotent_and_completed_capacity_cannot_be_released(self):
        self.reserve()
        first = self.service.dispatch("release", {"key": "KEY-A", "now_tick": 1})
        second = self.service.dispatch("release", {"key": "KEY-A", "now_tick": 2})
        self.assertEqual(first["reservation"], second["reservation"])
        self.assertEqual(first["status"], "RELEASED")
        replacement = reservation(self.init["allowed_orders"][0], key="REPLACEMENT", now=2)
        self.service.dispatch("reserve", replacement)
        self.service.dispatch("commit", {"key": "REPLACEMENT", "now_tick": 3})
        self.service.dispatch("fulfill", {"key": "REPLACEMENT", "now_tick": 3})
        self.assertRefusal("FULFILLED_IMMUTABLE", "release", {"key": "REPLACEMENT", "now_tick": 4})

    def test_expiry_exact_boundary_is_durable_and_committed_does_not_expire(self):
        self.reserve(expires=2)
        self.assertRefusal("RESERVATION_EXPIRED", "commit", {"key": "KEY-A", "now_tick": 2})
        self.assertEqual(self.service.dispatch("lookup", {"key": "KEY-A"})["status"], "EXPIRED")
        self.service.dispatch("reserve", reservation(self.init["allowed_orders"][0], key="NEW", now=2, expires=3))
        self.service.dispatch("commit", {"key": "NEW", "now_tick": 2})
        self.service.dispatch("expire", {"now_tick": 4})
        self.assertEqual(self.service.dispatch("lookup", {"key": "NEW"})["status"], "COMMITTED")
        self.assertEqual(self.service.dispatch("fulfill", {"key": "NEW", "now_tick": 4})["status"], "FULFILLED")

    def test_withdrawal_blocks_commit_but_allows_release(self):
        self.reserve()
        self.service.dispatch("withdraw", {"route": "backup", "now_tick": 1})
        self.assertRefusal("ROUTE_UNAVAILABLE", "commit", {"key": "KEY-A", "now_tick": 1})
        self.assertEqual(self.service.dispatch("release", {"key": "KEY-A", "now_tick": 1})["status"], "RELEASED")

    def test_capacity_cannot_be_lowered_below_encumbrance(self):
        self.reserve()
        self.assertRefusal("CAPACITY_ENCUMBERED", "capacity", {"route": "backup", "new_capacity": 1099, "now_tick": 1})
        self.service.dispatch("release", {"key": "KEY-A", "now_tick": 1})
        result = self.service.dispatch("capacity", {"route": "backup", "new_capacity": 0, "now_tick": 1})
        self.assertEqual(result["capacity"], 0)
        self.assertRefusal("CAPACITY_EXCEEDED", "reserve", reservation(self.init["allowed_orders"][1], now=1))

    def test_overlapping_window_sweep_allows_disjoint_capacity(self):
        self.service.dispatch("capacity", {"route": "backup", "new_capacity": 1100, "now_tick": 0})
        self.service.dispatch("reserve", reservation(self.init["allowed_orders"][0], start=0, end=50, expires=20))
        self.service.dispatch("reserve", reservation(self.init["allowed_orders"][1], start=50, end=100, expires=60))
        self.assertEqual(len(self.service.dispatch("snapshot", {})["reservations"]), 2)

    def test_overlapping_windows_refuse_overallocation(self):
        self.service.dispatch("capacity", {"route": "backup", "new_capacity": 1100, "now_tick": 0})
        self.service.dispatch("reserve", reservation(self.init["allowed_orders"][0], start=0, end=51, expires=20))
        self.assertRefusal("CAPACITY_EXCEEDED", "reserve", reservation(self.init["allowed_orders"][1], start=50, end=100, expires=60))

    def test_deadline_is_inclusive_late_completion_refused(self):
        self.reserve(expires=20)
        self.service.dispatch("commit", {"key": "KEY-A", "now_tick": 1})
        self.assertEqual(self.service.dispatch("fulfill", {"key": "KEY-A", "now_tick": 100})["receipt"]["completed_tick"], 100)
        # A different fresh service proves refusal, rather than retrying an
        # already completed order whose receipt should remain available.
        other = Service(self.folder / "late.sqlite", self.folder / "late-artifacts")
        try:
            other.dispatch("init", self.init)
            other.dispatch("reserve", reservation(self.init["allowed_orders"][1]))
            other.dispatch("commit", {"key": "KEY-B", "now_tick": 1})
            with self.assertRaises(Refusal) as caught:
                other.dispatch("fulfill", {"key": "KEY-B", "now_tick": 101})
            self.assertEqual(caught.exception.code, "DEADLINE_EXCEEDED")
            self.assertEqual(other.dispatch("snapshot", {})["receipts"], [])
        finally:
            other.close()

    def test_clock_regression_refused(self):
        self.reserve()
        self.service.dispatch("commit", {"key": "KEY-A", "now_tick": 2})
        self.assertRefusal("CLOCK_REGRESSION", "fulfill", {"key": "KEY-A", "now_tick": 1})

    def test_changed_artifact_is_preserved_and_reconciliation_incomplete(self):
        self.reserve()
        self.fulfill()
        path = self.artifacts / "A.json"
        path.write_text('{"tampered":true}\n')
        result = self.service.dispatch("reconcile", {})
        self.assertEqual(result["status"], "RECONCILIATION_INCOMPLETE")
        self.assertEqual(result["conflicts"][0]["code"], "ARTIFACT_CONFLICT")
        self.assertEqual(json.loads(path.read_text()), {"tampered": True})

    def test_symlink_paths_and_artifacts_are_refused(self):
        target = self.folder / "outside"
        target.write_text("protected")
        link = self.folder / "unsafe.sqlite"
        link.symlink_to(target)
        with self.assertRaises(Refusal) as caught:
            Service(link, self.folder / "other")
        self.assertEqual(caught.exception.code, "UNSAFE_PATH")
        self.reserve()
        self.service.dispatch("commit", {"key": "KEY-A", "now_tick": 1})
        (self.artifacts / "A.json").symlink_to(target)
        self.assertRefusal("UNSAFE_PATH", "fulfill", {"key": "KEY-A", "now_tick": 1})
        self.assertEqual(target.read_text(), "protected")
        self.assertEqual(self.service.dispatch("lookup", {"key": "KEY-A"})["status"], "FULFILLED")


class ProcessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="continuity-process-")
        self.folder = Path(self.temp.name)
        self.database, self.artifacts = self.folder / "state.sqlite", self.folder / "artifacts"
        self.clients = []
        self.init, self.events = fixture(capacity=1500)
        self.client = self.client_for()
        self.assertTrue(self.client.call("init", self.init)["ok"])

    def tearDown(self):
        for client in self.clients:
            client.close()
        self.temp.cleanup()

    def client_for(self):
        client = Client(self.database, self.artifacts)
        self.clients.append(client)
        self.assertTrue(client.call("ping", {})["ok"])
        return client

    def reserve_commit(self):
        self.assertTrue(self.client.call("reserve", reservation(self.init["allowed_orders"][0]))["ok"])
        self.assertTrue(self.client.call("commit", {"key": "KEY-A", "now_tick": 1})["ok"])

    def test_two_real_processes_compete_for_final_capacity_with_barriers(self):
        other = self.client_for()
        hooks = ["reserve.before_begin", "reserve.after_begin"]
        self.client.send("reserve", reservation(self.init["allowed_orders"][0]), hooks)
        other.send("reserve", reservation(self.init["allowed_orders"][1]), hooks)
        self.assertEqual(self.client.read()["hook"], "reserve.before_begin")
        self.assertEqual(other.read()["hook"], "reserve.before_begin")
        self.client.resume()
        self.assertEqual(self.client.read()["hook"], "reserve.after_begin")
        # The first process holds BEGIN IMMEDIATE while both requests exist.
        # Releasing the second makes it contend for the same durable database.
        other.resume()
        self.client.resume()
        winner = self.client.read()
        self.assertEqual(other.read()["hook"], "reserve.after_begin")
        other.resume()
        loser = other.read()
        self.assertTrue(winner["ok"])
        self.assertEqual(winner["result"]["reservation"]["quantity"], 1100)
        self.assertFalse(loser["ok"])
        self.assertEqual(loser["code"], "CAPACITY_EXCEEDED")
        state = self.client.call("snapshot", {})["result"]
        self.assertEqual(len(state["reservations"]), 1)
        self.assertEqual(sum(r["quantity"] for r in state["reservations"]), 1100)

    def test_opposite_process_wins_when_barrier_order_is_reversed(self):
        other = self.client_for()
        hooks = ["reserve.before_begin", "reserve.after_begin"]
        self.client.send("reserve", reservation(self.init["allowed_orders"][0]), hooks)
        other.send("reserve", reservation(self.init["allowed_orders"][1]), hooks)
        self.assertEqual(self.client.read()["hook"], "reserve.before_begin")
        self.assertEqual(other.read()["hook"], "reserve.before_begin")
        other.resume()
        self.assertEqual(other.read()["hook"], "reserve.after_begin")
        self.client.resume()
        other.resume()
        self.assertTrue(other.read()["ok"])
        self.assertEqual(self.client.read()["hook"], "reserve.after_begin")
        self.client.resume()
        self.assertEqual(self.client.read()["code"], "CAPACITY_EXCEEDED")
        rows = other.call("snapshot", {})["result"]["reservations"]
        self.assertEqual([(r["order_id"], r["quantity"]) for r in rows], [("B", 800)])

    def test_kill_before_reservation_commit_rolls_back(self):
        self.client.send("reserve", reservation(self.init["allowed_orders"][0]), ["reserve.before_commit"])
        self.assertEqual(self.client.read()["hook"], "reserve.before_commit")
        self.client.kill()
        resumed = self.client_for()
        self.assertEqual(resumed.call("snapshot", {})["result"]["reservations"], [])
        self.assertTrue(resumed.call("reserve", reservation(self.init["allowed_orders"][0]))["ok"])

    def test_kill_after_reservation_commit_retains_allocation(self):
        self.client.send("reserve", reservation(self.init["allowed_orders"][0]), ["reserve.after_commit"])
        self.assertEqual(self.client.read()["hook"], "reserve.after_commit")
        self.client.kill()
        resumed = self.client_for()
        result = resumed.call("reserve", reservation(self.init["allowed_orders"][0], now=1))
        self.assertEqual(result["result"]["status"], "RESERVED")
        self.assertEqual(len(resumed.call("snapshot", {})["result"]["reservations"]), 1)

    def test_kill_before_fulfillment_commit_can_retry_once(self):
        self.reserve_commit()
        self.client.send("fulfill", {"key": "KEY-A", "now_tick": 2}, ["fulfill.before_commit"])
        self.assertEqual(self.client.read()["hook"], "fulfill.before_commit")
        self.client.kill()
        resumed = self.client_for()
        state = resumed.call("snapshot", {})["result"]
        self.assertEqual(state["receipts"], [])
        self.assertEqual(state["reservations"][0]["status"], "COMMITTED")
        self.assertTrue(resumed.call("fulfill", {"key": "KEY-A", "now_tick": 2})["ok"])
        self.assertEqual(len(resumed.call("snapshot", {})["result"]["receipts"]), 1)

    def test_lost_acknowledgment_after_durable_fulfillment_reconciles(self):
        self.reserve_commit()
        self.client.send("fulfill", {"key": "KEY-A", "now_tick": 2}, ["fulfill.after_commit"])
        self.assertEqual(self.client.read()["hook"], "fulfill.after_commit")
        self.client.kill()
        self.assertFalse((self.artifacts / "A.json").exists())
        resumed = self.client_for()
        lookup = resumed.call("lookup", {"key": "KEY-A"})["result"]
        self.assertEqual(lookup["status"], "FULFILLED")
        receipt = lookup["receipt"]
        self.assertEqual(resumed.call("reconcile", {})["result"]["status"], "RECONCILED")
        for now in (3, 4):
            retry = resumed.call("fulfill", {"key": "KEY-A", "now_tick": now})["result"]
            self.assertEqual(retry["receipt"], receipt)
        state = resumed.call("snapshot", {})["result"]
        self.assertEqual(len(state["receipts"]), 1)
        self.assertEqual(sum(r["operation"] == "FULFILLED" for r in state["history"]), 1)
        self.assertEqual(len(list(self.artifacts.glob("*.json"))), 1)

    def test_retry_during_unknown_acknowledgment_does_not_duplicate(self):
        self.reserve_commit()
        self.client.send("fulfill", {"key": "KEY-A", "now_tick": 2}, ["fulfill.after_commit"])
        self.assertEqual(self.client.read()["hook"], "fulfill.after_commit")
        other = self.client_for()
        result = other.call("fulfill", {"key": "KEY-A", "now_tick": 3})
        self.assertTrue(result["ok"])
        self.client.kill()
        self.assertEqual(len(other.call("snapshot", {})["result"]["receipts"]), 1)
        self.assertEqual(json.loads((self.artifacts / "A.json").read_text()), result["result"]["receipt"])

    def test_partial_export_then_restart_never_accepts_partial_file(self):
        self.reserve_commit()
        self.client.send("fulfill", {"key": "KEY-A", "now_tick": 2}, ["export.after_half_write"])
        self.assertEqual(self.client.read()["hook"], "export.after_half_write")
        self.client.kill()
        self.assertFalse((self.artifacts / "A.json").exists())
        incomplete = list(self.artifacts.glob("*.tmp"))
        self.assertEqual(len(incomplete), 1)
        with self.assertRaises(json.JSONDecodeError):
            json.loads(incomplete[0].read_text())
        resumed = self.client_for()
        self.assertEqual(resumed.call("reconcile", {})["result"]["status"], "RECONCILED")
        self.assertEqual(len(list(self.artifacts.glob("*.json"))), 1)
        self.assertEqual(json.loads((self.artifacts / "A.json").read_text())["quantity"], 1100)
        self.assertTrue(incomplete[0].exists(), "An interrupted artifact is preserved as evidence")

    def test_process_wire_errors_are_structured_and_service_survives(self):
        self.client.process.stdin.write(b'{"id":1,"op":"ping","op":"snapshot","args":{}}\n')
        self.client.process.stdin.flush()
        self.assertEqual(self.client.read()["code"], "DUPLICATE_JSON_KEY")
        self.assertTrue(self.client.call("ping", {})["ok"])
        self.client.send("reserve", None)
        self.assertEqual(self.client.read()["code"], "INVALID_STRUCTURE")
        self.assertTrue(self.client.call("ping", {})["ok"])


class FiniteLedgerTests(unittest.TestCase):
    def test_exhaustive_three_step_ledger_traces(self):
        """Exhaust all 432 traces in the declared 2-capacity, 6-action, 3-step model.

        Two one-unit obligations share one [0,10) backup window. At ticks 0,1,2,
        each action is RA,RB,CA,FA,LA,or E; uncommitted leases expire at tick 2.
        This is an exhaustive finite invariant check, not a proof beyond it.
        """
        alphabet = ("RA", "RB", "CA", "FA", "LA", "E")
        count = 0
        with tempfile.TemporaryDirectory(prefix="continuity-finite-ledger-") as temp:
            root = Path(temp)
            for capacity in (1, 2):
                for actions in itertools.product(alphabet, repeat=3):
                    count += 1
                    folder = root / str(count)
                    service = Service(folder / "state.sqlite", folder / "artifacts")
                    try:
                        allowed = [order("A", 1, 10), order("B", 1, 10)]
                        service.dispatch("init", {"run_id": "RUN-001", "contract_sha256": CONTRACT,
                            "capacities": {"primary": 2, "backup": capacity}, "allowed_orders": allowed,
                            "snapshot": allowed, "window_start": 0, "window_end": 10})
                        for tick, action in enumerate(actions):
                            try:
                                if action in {"RA", "RB"}:
                                    service.dispatch("reserve", reservation(allowed[action == "RB"], now=tick, end=10, expires=2))
                                elif action == "E":
                                    service.dispatch("expire", {"now_tick": tick})
                                else:
                                    operation = {"CA": "commit", "FA": "fulfill", "LA": "release"}[action]
                                    service.dispatch(operation, {"key": "KEY-A", "now_tick": tick})
                            except Refusal:
                                pass
                            state = service.dispatch("snapshot", {})
                            live = [r for r in state["reservations"] if r["status"] in {"RESERVED", "COMMITTED", "FULFILLED"}]
                            self.assertLessEqual(sum(r["quantity"] for r in live), capacity, (capacity, actions, tick))
                            self.assertEqual(len({r["order_id"] for r in live}), len(live))
                            self.assertEqual(len({r["order_id"] for r in state["receipts"]}), len(state["receipts"]))
                            for receipt in state["receipts"]:
                                self.assertEqual(receipt["payload"]["quantity"], 1)
                                self.assertEqual(next(r["status"] for r in state["reservations"] if r["key"] == receipt["key"]), "FULFILLED")
                    finally:
                        service.close()
        self.assertEqual(count, 432)


if __name__ == "__main__":
    unittest.main()
