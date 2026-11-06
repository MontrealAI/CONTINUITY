"""Actual digital content, independent importing, interruption and retry controls.

These are engineering controls, not comparative results or physical-label tests.
Process races synchronize at explicit service hooks; no sleeps choose the winner.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from continuity_harness.rpc import ProcessChannel, ServiceClient
from continuity_harness.schema import HarnessError, canonical, digest
from continuity_economy.producer import Producer, FORMAT, generate_product
from continuity_economy.receiver import Receiver

ROOT = Path(__file__).resolve().parents[1]


def contract(quantity=4, lot_size=2, allow_split=True):
    spec = {"format": FORMAT, "sku": "TEA-80", "name_en": "Earl Grey loose leaf tea",
            "name_fr": "Thé Earl Grey en feuilles", "instructions_en": "Store dry. Infuse 3 minutes at 95 C.",
            "instructions_fr": "Conserver au sec. Infuser 3 minutes à 95 C.",
            "lot": "LOT-2026-11", "serial_prefix": "TEA-"}
    obligations = [{"obligation_id": "ORDER-A", "recipient": "BUYER-A", "revision": 2,
                    "quantity": quantity, "deadline_tick": 100, "status": "ACTIVE", "spec": spec},
                   {"obligation_id": "ORDER-C", "recipient": "BUYER-C", "revision": 1,
                    "quantity": 2, "deadline_tick": 100, "status": "CANCELLED", "spec": deepcopy(spec)}]
    source = [{"sequence": 1, "type": "ACCEPT", "obligation_id": "ORDER-A", "obligation": deepcopy(obligations[0])},
              {"sequence": 2, "type": "ACCEPT", "obligation_id": "ORDER-C",
               "obligation": {**deepcopy(obligations[1]), "status": "ACTIVE"}},
              {"sequence": 3, "type": "CANCEL", "obligation_id": "ORDER-C"}]
    return {"schema": "continuity-economy/contract/v1", "run_id": "PRODUCT-RUN", "contract_id": "DIGITAL-PROMISE",
            "experiment_id": "PRODUCT-CONTROL", "fixture_id": "product-component", "cohort": "challenge",
            "revision": 1, "start_ns": time.monotonic_ns(), "deadline_tick": 100, "wall_deadline_ms": 60000,
            "observation_cutoff_tick": 150, "lease_ticks": 10, "seed": 721,
            "authority_kind": "SYNTHETIC_EXERCISE", "source_id": "AUTHORED-PRODUCT-CONTROL",
            "source_complete": True, "source_events": source, "source_sha256": digest(source),
            "cutoff_sequence": 3, "max_attempts": 2, "permissible_recovery_loss_units": 0,
            "lot_size": lot_size, "allow_split": allow_split,
            "obligations": obligations,
            "providers": [{"provider_id": "PROVIDER-A", "role": "primary", "dependency": "DEPENDENCY-A",
                           "permissions": {"production": True, "disclosure": True},
                           "windows": [{"window_id": "W0", "start": 0, "end": 100, "capacity": 4000}]}],
            "blocked_dependencies": [], "revocations": [], "fault_schedule": [], "mode": "market",
            "disclosure_fields": ["recipient", "sku", "name_en", "name_fr", "instructions_en",
                                  "instructions_fr", "lot", "serial_prefix"],
            "permitted_actions": ["restore", "propose", "decide", "technical", "reserve", "produce",
                                  "transfer", "inspect", "settle", "cancel", "status"],
            "bounds": {"max_requests": 64, "max_plans": 64, "max_proposals": 4, "service_timeout_ms": 5000}}


def request(c, lot=1, attempt=1, arrangement="ARR-1", defect="none", supersedes=None, obligation_id="ORDER-A"):
    obligation = next(o for o in c["obligations"] if o["obligation_id"] == obligation_id)
    size = c["lot_size"] if c["allow_split"] else obligation["quantity"]
    lot_id = obligation_id + f".L{lot:03d}"
    key = arrangement + "." + lot_id + ".A" + str(attempt)
    return {"production_id": key, "capacity_key": key, "lot_id": lot_id, "attempt": attempt,
            "arrangement_id": arrangement, "provider_id": "PROVIDER-A", "delivery_id": key + ".D",
            "obligation_id": obligation_id, "first_unit": (lot - 1) * size + 1,
            "last_unit": min(lot * size, obligation["quantity"]), "supersedes": supersedes,
            "now_tick": 1, "defect": defect}


def durable_copy(source, destination):
    with open(destination, "wb", buffering=0) as stream:
        stream.write(Path(source).read_bytes())
        os.fsync(stream.fileno())
    descriptor = os.open(Path(destination).parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


class Client(ServiceClient):
    """Reuse qualified bounded RPC framing, with this experiment's service module."""
    def __init__(self, module, directory, cpath, label="main"):
        folder_option = "--artifacts" if module == "producer" else "--inbox"
        folder_name = "products" if module == "producer" else "inbox"
        ProcessChannel.__init__(self, [sys.executable, "-m", "continuity_economy." + module,
                                      "--db", str(directory / (module + ".sqlite")), folder_option,
                                      str(directory / folder_name), "--contract", str(cpath)],
                                ROOT, directory / (module + "-" + label + ".stderr"))
        self.counter = 0


class ProductControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="continuity-digital-product-")
        self.directory = Path(self.temp.name)
        self.contract = contract()
        self.producer = Producer(self.directory / "producer.sqlite", self.directory / "products", self.contract)
        self.receiver = Receiver(self.directory / "receiver.sqlite", self.directory / "inbox", self.contract)

    def tearDown(self):
        self.producer.close()
        self.receiver.close()
        self.temp.cleanup()

    def deliver(self, req, mutate=None, inspect_tick=3):
        produced = self.producer.dispatch("produce", req)
        destination = self.directory / "inbox" / (req["delivery_id"] + ".json")
        durable_copy(self.directory / "products" / produced["artifact_name"], destination)
        if mutate:
            raw = mutate(destination.read_bytes())
            destination.write_bytes(raw)
        received = self.receiver.dispatch("receive", {"delivery_id": req["delivery_id"], "obligation_id": req["obligation_id"], "now_tick": 2})
        self.assertEqual(received["status"], "RECEIVED")
        self.assertEqual(received["accepted_units"], 0)
        return self.receiver.dispatch("inspect", {"delivery_id": req["delivery_id"], "now_tick": inspect_tick})

    def refusal(self, code, operation, args, service=None):
        with self.assertRaises(HarnessError) as caught:
            (service or self.producer).dispatch(operation, args)
        self.assertEqual(caught.exception.code, code)

    def test_positive_materialized_content_is_imported_in_separate_acceptance_state(self):
        for lot in (1, 2):
            result = self.deliver(request(self.contract, lot=lot))
            self.assertEqual(result["status"], "ACCEPTED")
            self.assertTrue(result["timely"])
            self.assertEqual(result["accepted_units"], 2)
            self.assertGreaterEqual(result["observation"]["observed_ns"], result["decision"]["inspected_ns"])
        rows = list(self.receiver.db.execute("SELECT * FROM imported_units ORDER BY ordinal"))
        self.assertEqual([r["serial"] for r in rows], ["TEA-000001", "TEA-000002", "TEA-000003", "TEA-000004"])
        self.assertTrue(all(r["instructions_fr"] == self.contract["obligations"][0]["spec"]["instructions_fr"] for r in rows))
        self.assertEqual(self.receiver.snapshot()["imported_units"], 4)
        self.assertEqual(self.producer.snapshot()["generated_units"], 4)

    def test_wrong_content_rejection_and_explicit_repair_retain_both_attempts(self):
        first = request(self.contract, defect="wrong_content")
        rejected = self.deliver(first)
        self.assertEqual((rejected["status"], rejected["decision"]["code"]), ("REJECTED", "CONTENT_MISMATCH"))
        original = bytes(self.receiver.db.execute("SELECT raw FROM receipts WHERE delivery_id=?", (first["delivery_id"],)).fetchone()[0])
        second = request(self.contract, attempt=2, supersedes=first["delivery_id"])
        accepted = self.deliver(second)
        self.assertEqual(accepted["status"], "ACCEPTED")
        self.assertEqual(self.producer.snapshot()["generated_units"], 4)
        self.assertEqual(self.receiver.snapshot()["imported_units"], 2)
        self.assertEqual(self.receiver.db.execute("SELECT count(*) FROM decisions").fetchone()[0], 2)
        self.assertEqual(bytes(self.receiver.db.execute("SELECT raw FROM receipts WHERE delivery_id=?", (first["delivery_id"],)).fetchone()[0]), original)
        self.assertEqual(accepted["decision"]["supersedes"], first["delivery_id"])

    def test_malformed_incomplete_stale_wrong_recipient_and_corrupt_products_rejected(self):
        cases = {"missing_unit": "UNIT_COVERAGE_MISMATCH", "duplicate_unit": "UNIT_COVERAGE_MISMATCH",
                 "stale_revision": "STALE_REVISION", "wrong_recipient": "WRONG_RECIPIENT",
                 "wrong_serial": "SERIAL_MISMATCH", "truncated": "INVALID_JSON", "corrupt": "INVALID_JSON"}
        for index, (defect, expected) in enumerate(cases.items()):
            with self.subTest(defect=defect):
                result = self.deliver(request(self.contract, arrangement="BAD-" + str(index), defect=defect))
                self.assertEqual((result["status"], result["decision"]["code"]), ("REJECTED", expected))
                self.assertEqual(result["accepted_units"], 0)
        self.assertEqual(self.receiver.snapshot()["imported_units"], 0)

    def test_truncated_delivery_can_be_repaired_without_overwriting_raw_history(self):
        first = request(self.contract, defect="truncated")
        bad = self.deliver(first)
        self.assertEqual(bad["decision"]["code"], "INVALID_JSON")
        second = request(self.contract, attempt=2, supersedes=first["delivery_id"])
        self.assertEqual(self.deliver(second)["status"], "ACCEPTED")
        self.assertEqual(self.receiver.db.execute("SELECT count(*) FROM receipts").fetchone()[0], 2)

    def test_correct_hash_metadata_does_not_replace_literal_content_inspection(self):
        def change(raw):
            value = json.loads(raw)
            value["labels"][0]["name_fr"] = "Produit incorrect"
            return canonical(value)
        result = self.deliver(request(self.contract), change)
        self.assertEqual(result["decision"]["code"], "CONTENT_MISMATCH")
        raw = self.receiver.db.execute("SELECT raw FROM receipts").fetchone()[0]
        self.assertEqual(result["content_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result["accepted_units"], 0)

    def test_product_binding_unknown_fields_and_noninteger_units_fail(self):
        changes = [("run_id", "OTHER-RUN", "WRONG_RUN"), ("contract_id", "OTHER-CONTRACT", "WRONG_CONTRACT"),
                   ("contract_sha256", "ff" * 32, "WRONG_CONTRACT"), ("schema", "unsupported/v99", "UNSUPPORTED_PRODUCT"),
                   ("revision", True, "INVALID_TYPE"), ("first_unit", "1", "INVALID_TYPE"),
                   ("surprise", "unsupported", "INVALID_FIELDS")]
        for index, (key, value, expected) in enumerate(changes):
            with self.subTest(key=key):
                def mutate(raw, k=key, v=value):
                    body = json.loads(raw); body[k] = v; return canonical(body)
                result = self.deliver(request(self.contract, arrangement="BIND-" + str(index)), mutate)
                self.assertEqual(result["decision"]["code"], expected)
                self.assertEqual(result["accepted_units"], 0)

    def test_duplicate_json_keys_are_retained_as_rejected_bytes(self):
        result = self.deliver(request(self.contract), lambda raw: raw[:-1] + b',"schema":"duplicate"}')
        self.assertEqual(result["decision"]["code"], "DUPLICATE_KEY")
        self.assertEqual(result["status"], "REJECTED")

    def test_cancelled_obligation_is_refused_by_producer_and_receiver(self):
        req = request(self.contract, obligation_id="ORDER-C")
        self.refusal("CANCELLED_OBLIGATION", "produce", req)
        # Privileged negative control constructs actual bytes for a cancelled job;
        # receiver acceptance must still be independently denied.
        obligation = next(o for o in self.contract["obligations"] if o["obligation_id"] == "ORDER-C")
        raw, _ = generate_product(self.contract, obligation, req)
        (self.directory / "inbox" / (req["delivery_id"] + ".json")).write_bytes(raw)
        self.receiver.dispatch("receive", {"delivery_id": req["delivery_id"], "obligation_id": "ORDER-C", "now_tick": 2})
        result = self.receiver.dispatch("inspect", {"delivery_id": req["delivery_id"], "now_tick": 3})
        self.assertEqual(result["decision"]["code"], "CANCELLED_OBLIGATION")
        self.assertEqual(result["accepted_units"], 0)

    def test_invalid_production_requests_do_not_mutate_state(self):
        before = self.producer.snapshot()
        base = request(self.contract)
        for key, value, expected in [("first_unit", True, "INVALID_TYPE"), ("last_unit", "2", "INVALID_TYPE"),
                                     ("attempt", False, "INVALID_TYPE"), ("production_id", "../escape", "INVALID_IDENTIFIER"),
                                     ("unexpected", 1, "INVALID_FIELDS"), ("defect", [], "UNSUPPORTED_PRODUCT")]:
            with self.subTest(key=key):
                self.refusal(expected, "produce", {**base, key: value})
        self.assertEqual(self.producer.snapshot(), before)

    def test_production_retries_are_idempotent_and_aliases_conflict(self):
        req = request(self.contract)
        first = self.producer.dispatch("produce", req)
        repeated = self.producer.dispatch("produce", {**req, "now_tick": 5})
        self.assertEqual(first["observation"], repeated["observation"])
        self.assertEqual(first["payload_sha256"], repeated["payload_sha256"])
        self.assertEqual(self.producer.snapshot()["generated_units"], 2)
        self.assertEqual(self.producer.db.execute("SELECT count(*) FROM productions").fetchone()[0], 1)
        self.assertEqual(self.producer.db.execute("SELECT count(*) FROM events WHERE event='CONTENT_GENERATED'").fetchone()[0], 1)
        self.refusal("IDEMPOTENCY_CONFLICT", "produce", {**req, "provider_id": "OTHER-PROVIDER"})
        self.refusal("PRODUCTION_BINDING_MISMATCH", "produce", {**req, "production_id": "ALIAS"})

    def test_receipt_and_acceptance_retries_preserve_original_bytes_and_time(self):
        req = request(self.contract)
        first = self.deliver(req)
        self.receiver.dispatch("receive", {"delivery_id": req["delivery_id"], "obligation_id": "ORDER-A", "now_tick": 90})
        replay = self.receiver.dispatch("inspect", {"delivery_id": req["delivery_id"], "now_tick": 101})
        self.assertEqual(first["decision"], replay["decision"])
        self.assertEqual(first["observation"], replay["observation"])
        self.assertTrue(replay["timely"])
        self.assertEqual(self.receiver.snapshot()["imported_units"], 2)
        (self.directory / "inbox" / (req["delivery_id"] + ".json")).write_bytes(b"changed")
        self.refusal("IDEMPOTENCY_CONFLICT", "receive", {"delivery_id": req["delivery_id"], "obligation_id": "ORDER-A", "now_tick": 102}, self.receiver)

    def test_duplicate_completed_work_from_a_new_arrangement_is_not_imported(self):
        self.assertEqual(self.deliver(request(self.contract))["status"], "ACCEPTED")
        other = self.deliver(request(self.contract, arrangement="ARR-2"))
        self.assertEqual(other["decision"]["code"], "DUPLICATE_FULFILLMENT")
        self.assertEqual(other["accepted_units"], 0)
        self.assertEqual(self.receiver.snapshot()["imported_units"], 2)

    def test_correction_requires_rejected_predecessor_and_cannot_erase_history(self):
        first = request(self.contract, defect="wrong_content")
        self.deliver(first)
        self.refusal("INVALID_CORRECTION", "produce", request(self.contract, attempt=2))
        corrected = self.deliver(request(self.contract, attempt=2, supersedes=first["delivery_id"]))
        self.assertEqual(corrected["status"], "ACCEPTED")
        self.assertEqual(self.receiver.db.execute("SELECT count(*) FROM decisions").fetchone()[0], 2)
        self.assertEqual(self.receiver.snapshot()["imported_units"], 2)
        retained = self.receiver.status(first["delivery_id"])
        self.assertEqual((retained["status"], retained["decision"]["code"]), ("REJECTED", "CONTENT_MISMATCH"))

    def test_new_agreement_a1_is_content_checked_separately_and_old_rejection_is_retained(self):
        # This service does not authorize an agreement. Broker/verifier controls
        # separately require prior cancellation, no prior acceptance, distinct
        # funding and capacity. The receiver must allow a correct new A1's
        # content instead of confusing it with an unsupported A2 correction.
        first = request(self.contract, defect="wrong_content")
        self.assertEqual(self.deliver(first)["status"], "REJECTED")
        original = self.receiver.status(first["delivery_id"])
        replacement = request(self.contract, arrangement="REPLACEMENT")
        result = self.deliver(replacement)
        self.assertEqual(result["status"], "ACCEPTED")
        self.assertIsNone(result["decision"]["supersedes"])
        self.assertEqual(self.producer.snapshot()["generated_units"], 4)
        self.assertEqual(self.receiver.snapshot()["imported_units"], 2)
        self.assertEqual(self.receiver.status(first["delivery_id"]), original)
        duplicate = self.deliver(request(self.contract, arrangement="UNSUPPORTED-THIRD"))
        self.assertEqual(duplicate["decision"]["code"], "DUPLICATE_FULFILLMENT")
        self.assertEqual(self.receiver.snapshot()["imported_units"], 2)

    def test_correction_limit_and_wrong_range_are_enforced(self):
        first = request(self.contract, defect="wrong_content")
        self.deliver(first)
        second = request(self.contract, attempt=2, supersedes=first["delivery_id"], defect="wrong_content")
        self.deliver(second)
        third = request(self.contract, arrangement="ARR-3", attempt=2, supersedes=second["delivery_id"])
        self.refusal("INVALID_CORRECTION", "produce", third)
        self.refusal("INVALID_RANGE", "produce", request(self.contract, attempt=3, supersedes=second["delivery_id"]))
        wrong_range = request(self.contract, lot=2, attempt=2, supersedes=first["delivery_id"])
        self.refusal("INVALID_CORRECTION", "produce", wrong_range)
        self.assertEqual(self.receiver.snapshot()["imported_units"], 0)

    def test_initial_attempt_two_and_cross_agreement_correction_are_independently_rejected(self):
        req = request(self.contract, attempt=2, supersedes=None)
        self.refusal("INVALID_CORRECTION", "produce", req)
        # A privileged adversarial producer can still supply bytes; the receiving
        # service must not rely on the producer's corrected admission function.
        raw, _ = generate_product(self.contract, self.contract["obligations"][0], req)
        (self.directory / "inbox" / (req["delivery_id"] + ".json")).write_bytes(raw)
        self.receiver.dispatch("receive", {"delivery_id": req["delivery_id"], "obligation_id": "ORDER-A", "now_tick": 2})
        result = self.receiver.dispatch("inspect", {"delivery_id": req["delivery_id"], "now_tick": 3})
        self.assertEqual(result["decision"]["code"], "INVALID_CORRECTION")
        self.assertEqual(result["accepted_units"], 0)

    def test_deadline_boundary_is_inclusive_and_late_new_acceptance_is_rejected(self):
        exact = self.deliver(request(self.contract), inspect_tick=100)
        late = self.deliver(request(self.contract, lot=2), inspect_tick=101)
        self.assertTrue(exact["timely"])
        self.assertEqual(late["decision"]["code"], "DEADLINE_EXPIRED")
        self.assertEqual(late["accepted_units"], 0)

    def test_postcommit_observation_not_precommit_timestamp_controls_timeliness(self):
        req = request(self.contract)
        produced = self.producer.dispatch("produce", req)
        durable_copy(self.directory / "products" / produced["artifact_name"], self.directory / "inbox" / (req["delivery_id"] + ".json"))
        self.receiver.dispatch("receive", {"delivery_id": req["delivery_id"], "obligation_id": "ORDER-A", "now_tick": 2})
        deadline = self.contract["start_ns"] + self.contract["wall_deadline_ms"] * 1_000_000
        clock = [deadline]
        def hook(name):
            if name == "inspect.after_commit":
                clock[0] = deadline + 1
        self.receiver.hook = hook
        with patch("continuity_economy.receiver.time.monotonic_ns", side_effect=lambda: clock[0]):
            result = self.receiver.dispatch("inspect", {"delivery_id": req["delivery_id"], "now_tick": 3})
        self.assertEqual(result["status"], "ACCEPTED")
        self.assertEqual(result["decision"]["inspected_ns"], deadline)
        self.assertEqual(result["observation"]["observed_ns"], deadline + 1)
        self.assertFalse(result["timely"])

    def test_receiver_does_not_use_producer_generation_as_its_oracle(self):
        original = generate_product
        def defective(c, o, r):
            raw, count = original(c, o, r)
            value = json.loads(raw); value["labels"][0]["instructions_en"] = "Wrong generated instruction."
            return canonical(value), count
        with patch("continuity_economy.producer.generate_product", side_effect=defective):
            result = self.deliver(request(self.contract))
        self.assertEqual(result["decision"]["code"], "CONTENT_MISMATCH")
        self.assertEqual(result["accepted_units"], 0)

    def test_missing_completeness_does_not_obtain_recipient_acceptance(self):
        c = contract(); c["source_complete"] = False
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            p = Producer(folder / "p.sqlite", folder / "products", c)
            r = Receiver(folder / "r.sqlite", folder / "inbox", c)
            try:
                req = request(c); produced = p.dispatch("produce", req)
                durable_copy(folder / "products" / produced["artifact_name"], folder / "inbox" / (req["delivery_id"] + ".json"))
                r.dispatch("receive", {"delivery_id": req["delivery_id"], "obligation_id": "ORDER-A", "now_tick": 2})
                result = r.dispatch("inspect", {"delivery_id": req["delivery_id"], "now_tick": 3})
                self.assertEqual(result["decision"]["code"], "SOURCE_NOT_ESTABLISHED")
                self.assertEqual(result["accepted_units"], 0)
            finally:
                p.close(); r.close()

    def test_unsplit_whole_obligation_larger_than_lot_size_is_supported(self):
        c = contract(quantity=5, lot_size=2, allow_split=False)
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp); p = Producer(folder / "p.sqlite", folder / "products", c); r = Receiver(folder / "r.sqlite", folder / "inbox", c)
            try:
                req = request(c); output = p.dispatch("produce", req)
                self.assertEqual(output["quantity"], 5)
                durable_copy(folder / "products" / output["artifact_name"], folder / "inbox" / (req["delivery_id"] + ".json"))
                r.dispatch("receive", {"delivery_id": req["delivery_id"], "obligation_id": "ORDER-A", "now_tick": 2})
                accepted = r.dispatch("inspect", {"delivery_id": req["delivery_id"], "now_tick": 3})
                self.assertEqual(accepted["accepted_units"], 5)
            finally:
                p.close(); r.close()

    def test_supported_1900_unit_content_and_snapshots_fit_wire_bounds(self):
        c = contract(quantity=1900, lot_size=1900)
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp); p = Producer(folder / "p.sqlite", folder / "products", c); r = Receiver(folder / "r.sqlite", folder / "inbox", c)
            try:
                req = request(c); output = p.dispatch("produce", req)
                self.assertGreater(output["byte_count"], 100000)
                durable_copy(folder / "products" / output["artifact_name"], folder / "inbox" / (req["delivery_id"] + ".json"))
                r.dispatch("receive", {"delivery_id": req["delivery_id"], "obligation_id": "ORDER-A", "now_tick": 2})
                self.assertEqual(r.dispatch("inspect", {"delivery_id": req["delivery_id"], "now_tick": 3})["accepted_units"], 1900)
                self.assertLess(len(canonical(r.snapshot())), 10000)
                self.assertLess(len(canonical(p.snapshot())), 10000)
            finally:
                p.close(); r.close()

    def test_retained_contract_changes_and_unsupported_features_fail_before_reuse(self):
        changed = deepcopy(self.contract); changed["obligations"][0]["recipient"] = "OTHER"
        changed["source_events"][0]["obligation"]["recipient"] = "OTHER"
        changed["source_sha256"] = digest(changed["source_events"])
        for cls, directory in ((Producer, "products"), (Receiver, "inbox")):
            with self.subTest(service=cls.__name__), self.assertRaises(HarnessError) as caught:
                cls(self.directory / ("producer.sqlite" if cls is Producer else "receiver.sqlite"), self.directory / directory, changed)
            self.assertEqual(caught.exception.code, "CONTRACT_MISMATCH")
        changed = deepcopy(self.contract); changed["obligations"][0]["spec"]["font"] = "unsupported"
        with self.assertRaises(HarnessError) as caught:
            Producer(self.directory / "new.sqlite", self.directory / "other", changed)
        self.assertEqual(caught.exception.code, "INVALID_FIELDS")
        self.assertFalse((self.directory / "new.sqlite").exists())

    def test_full_service_contract_admission_refuses_unknown_fields_types_and_ranges_before_writing(self):
        changes = [
            ("unknown-root", lambda c: c.update(unsupported_root_field=True), "INVALID_FIELDS"),
            ("version", lambda c: c.update(schema="continuity-economy/contract/v99"), "UNSUPPORTED_VERSION"),
            ("run-identity", lambda c: c.update(run_id="../unsafe"), "INVALID_IDENTIFIER"),
            ("attempt-limit", lambda c: c.update(max_attempts=3), "INVALID_RANGE"),
            ("boolean-time", lambda c: c.update(start_ns=True), "INVALID_TYPE"),
            ("bool-completeness", lambda c: c.update(source_complete="true"), "INVALID_TYPE"),
            ("missing-source", lambda c: c.pop("source_events"), "INVALID_FIELDS"),
            ("source-digest", lambda c: c.update(source_sha256="0"*64), "SOURCE_DIGEST_MISMATCH"),
            ("provider-identity", lambda c: c["providers"][0].update(provider_id="../unsafe"), "INVALID_IDENTIFIER"),
            ("window-quantity", lambda c: c["providers"][0]["windows"][0].update(capacity="4"), "INVALID_TYPE"),
            ("unknown-bound", lambda c: c["bounds"].update(extra=1), "INVALID_FIELDS"),
        ]
        for name, mutate, expected in changes:
            for cls in (Producer, Receiver):
                with self.subTest(case=name, service=cls.__name__):
                    invalid = deepcopy(self.contract); mutate(invalid)
                    folder = self.directory / (name + "-" + cls.__name__)
                    with self.assertRaises(HarnessError) as caught:
                        cls(folder / "state.sqlite", folder / "content", invalid)
                    self.assertEqual(caught.exception.code, expected)
                    self.assertFalse(folder.exists())

    def test_services_retain_a_copy_of_the_admitted_contract(self):
        original_sha = self.producer.contract_sha256
        self.contract["obligations"][0]["spec"]["name_fr"] = "Modification externe"
        self.assertNotEqual(self.contract["obligations"][0]["spec"]["name_fr"],
                            self.receiver.contract["obligations"][0]["spec"]["name_fr"])
        self.assertEqual(digest(self.producer.contract), original_sha)
        self.assertEqual(digest(self.receiver.contract), original_sha)

    def test_direct_process_contract_refusal_is_bilingual_and_creates_no_state(self):
        raw = canonical(self.contract)
        cases = {
            "unknown": (canonical({**self.contract, "unknown": 1}), "INVALID_FIELDS"),
            "duplicate": (raw[:-1] + b',"schema":"continuity-economy/contract/v1"}', "DUPLICATE_KEY"),
            "malformed": (b'{"schema":', "INVALID_JSON"),
        }
        for module, option in (("producer", "--artifacts"), ("receiver", "--inbox")):
            for name, (data, expected) in cases.items():
                with self.subTest(service=module, case=name):
                    cpath = self.directory / (module + "-" + name + ".json"); cpath.write_bytes(data)
                    folder = self.directory / (module + "-" + name)
                    result = subprocess.run([sys.executable, "-m", "continuity_economy." + module,
                        "--contract", str(cpath), "--db", str(folder / "state.sqlite"),
                        option, str(folder / "content")], cwd=ROOT, input="", text=True, capture_output=True, timeout=5)
                    self.assertEqual(result.returncode, 2)
                    message = json.loads(result.stdout)
                    self.assertEqual(message["code"], expected)
                    self.assertEqual(set(message["detail"]), {"en", "fr"})
                    self.assertNotEqual(message["detail"]["en"], message["detail"]["fr"])
                    self.assertFalse(folder.exists())

    def test_internal_process_help_has_bilingual_help_instruction(self):
        for module in ("producer", "receiver"):
            result = subprocess.run([sys.executable, "-m", "continuity_economy." + module, "--help"],
                                    cwd=ROOT, text=True, capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Show complete help and exit", result.stdout)
            self.assertIn("Afficher l’aide complète", result.stdout)
            self.assertNotIn("show this help message and exit", result.stdout)


class ProductProcessControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="continuity-digital-process-")
        self.directory = Path(self.temp.name)
        self.contract = contract()
        self.cpath = self.directory / "contract.json"
        self.cpath.write_bytes(canonical(self.contract))
        self.clients = []

    def tearDown(self):
        for client in self.clients:
            client.close()
        self.temp.cleanup()

    def client(self, module, directory=None, label=None):
        folder = directory or self.directory
        folder.mkdir(exist_ok=True)
        client = Client(module, folder, self.cpath, label or str(len(self.clients)))
        self.clients.append(client)
        return client

    def result(self, response):
        self.assertTrue(response.get("ok"), response)
        return response["result"]

    def prepare(self, folder=None, req=None):
        folder = folder or self.directory
        producer = self.client("producer", folder)
        req = req or request(self.contract)
        produced = self.result(producer.call("produce", req))
        receiver = self.client("receiver", folder)
        self.result(receiver.call("snapshot", {}))
        durable_copy(folder / "products" / produced["artifact_name"], folder / "inbox" / (req["delivery_id"] + ".json"))
        return producer, receiver, req

    def test_real_production_crashes_reconcile_payload_and_preserve_partial_writes(self):
        for hook in ("produce.after_intent", "produce.before_commit", "produce.after_commit", "produce.after_half_write", "produce.after_replace", "produce.after_observation"):
            with self.subTest(hook=hook):
                folder = self.directory / hook.replace(".", "-")
                client = self.client("producer", folder)
                req = request(self.contract)
                client.start_request("produce", req, [hook])
                barrier = client.receive(); self.assertEqual(barrier.get("hook"), hook)
                client.kill()
                if hook == "produce.after_half_write":
                    partials = list((folder / "products").glob("*.part")) + list((folder / "products").glob(".*.part"))
                    self.assertTrue(partials)
                    self.assertTrue(any(0 < p.stat().st_size for p in partials))
                restarted = self.client("producer", folder)
                result = self.result(restarted.call("produce", {**req, "now_tick": 2}))
                self.assertEqual(result["status"], "MATERIALIZED")
                self.assertEqual(result["request_count"], 2)
                with sqlite3.connect(folder / "producer.sqlite") as db:
                    self.assertEqual(db.execute("SELECT count(*) FROM productions").fetchone()[0], 1)
                    self.assertEqual(db.execute("SELECT count(*) FROM events WHERE event='CONTENT_GENERATED'").fetchone()[0], 1)
                    raw = db.execute("SELECT payload FROM productions").fetchone()[0]
                self.assertEqual((folder / "products" / result["artifact_name"]).read_bytes(), raw)

    def test_receipt_crashes_before_and_after_commit_leave_distinct_durable_states(self):
        for hook in ("receive.before_commit", "receive.after_commit"):
            with self.subTest(hook=hook):
                folder = self.directory / hook.replace(".", "-")
                _, receiver, req = self.prepare(folder)
                args = {"delivery_id": req["delivery_id"], "obligation_id": "ORDER-A", "now_tick": 2}
                receiver.start_request("receive", args, [hook])
                self.assertEqual(receiver.receive().get("hook"), hook)
                receiver.kill()
                with sqlite3.connect(folder / "receiver.sqlite") as db:
                    self.assertEqual(db.execute("SELECT count(*) FROM receipts").fetchone()[0], 0 if hook.endswith("before_commit") else 1)
                    self.assertEqual(db.execute("SELECT count(*) FROM decisions").fetchone()[0], 0)
                restarted = self.client("receiver", folder)
                self.result(restarted.call("receive", args))
                accepted = self.result(restarted.call("inspect", {"delivery_id": req["delivery_id"], "now_tick": 3}))
                self.assertEqual(accepted["accepted_units"], 2)

    def test_acceptance_crashes_and_lost_ack_preserve_uncertainty_and_original_observation(self):
        for hook in ("inspect.before_commit", "inspect.after_commit", "inspect.after_observation"):
            with self.subTest(hook=hook):
                folder = self.directory / hook.replace(".", "-")
                _, receiver, req = self.prepare(folder)
                self.result(receiver.call("receive", {"delivery_id": req["delivery_id"], "obligation_id": "ORDER-A", "now_tick": 2}))
                receiver.start_request("inspect", {"delivery_id": req["delivery_id"], "now_tick": 3}, [hook])
                self.assertEqual(receiver.receive().get("hook"), hook)
                receiver.kill()
                restarted = self.client("receiver", folder)
                status = self.result(restarted.call("status", {"delivery_id": req["delivery_id"]}))
                if hook == "inspect.before_commit":
                    self.assertIsNone(status["decision"]); self.assertEqual(status["accepted_units"], 0)
                    replay_tick = 4
                else:
                    self.assertEqual(status["status"], "ACCEPTED"); self.assertEqual(status["accepted_units"], 2)
                    replay_tick = 101
                if hook == "inspect.after_commit":
                    self.assertIsNone(status["observation"]); self.assertIsNone(status["timely"])
                replay = self.result(restarted.call("inspect", {"delivery_id": req["delivery_id"], "now_tick": replay_tick}))
                self.assertEqual(replay["accepted_units"], 2)
                if hook == "inspect.after_commit":
                    self.assertEqual(replay["observation"]["observed_tick"], 101)
                    self.assertFalse(replay["timely"])
                else:
                    self.assertTrue(replay["timely"])
                if hook == "inspect.after_observation":
                    self.assertEqual(status["observation"], replay["observation"])

    def test_two_concurrent_deliveries_cannot_both_accept_the_same_units(self):
        producer = self.client("producer")
        first, second = request(self.contract), request(self.contract, arrangement="ARR-2")
        receivers = [self.client("receiver"), self.client("receiver")]
        for receiver, req in zip(receivers, (first, second)):
            self.result(receiver.call("snapshot", {}))
            output = self.result(producer.call("produce", req))
            durable_copy(self.directory / "products" / output["artifact_name"], self.directory / "inbox" / (req["delivery_id"] + ".json"))
            self.result(receiver.call("receive", {"delivery_id": req["delivery_id"], "obligation_id": "ORDER-A", "now_tick": 2}))
        a, b = receivers
        a.start_request("inspect", {"delivery_id": first["delivery_id"], "now_tick": 3}, ["inspect.after_begin"])
        self.assertEqual(a.receive().get("hook"), "inspect.after_begin")
        b.start_request("inspect", {"delivery_id": second["delivery_id"], "now_tick": 3}, ["inspect.before_begin"])
        self.assertEqual(b.receive().get("hook"), "inspect.before_begin")
        b.send({"continue": True}); a.send({"continue": True})
        accepted, rejected = self.result(a.receive()), self.result(b.receive())
        self.assertEqual(accepted["status"], "ACCEPTED")
        self.assertEqual(rejected["decision"]["code"], "DUPLICATE_FULFILLMENT")
        self.assertEqual(self.result(a.call("snapshot", {}))["imported_units"], 2)

    def test_two_producer_processes_reconcile_one_capacity_key(self):
        a, b = self.client("producer"), self.client("producer")
        self.result(a.call("snapshot", {})); self.result(b.call("snapshot", {}))
        req = request(self.contract)
        a.start_request("produce", req, ["produce.before_begin", "produce.after_commit"])
        self.assertEqual(a.receive().get("hook"), "produce.before_begin")
        b.start_request("produce", req, ["produce.before_begin"])
        self.assertEqual(b.receive().get("hook"), "produce.before_begin")
        a.send({"continue": True}); self.assertEqual(a.receive().get("hook"), "produce.after_commit")
        a.send({"continue": True}); b.send({"continue": True})
        one, two = self.result(a.receive()), self.result(b.receive())
        self.assertEqual(one["payload_sha256"], two["payload_sha256"])
        with sqlite3.connect(self.directory / "producer.sqlite") as db:
            self.assertEqual(db.execute("SELECT count(*) FROM productions").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT count(*) FROM events WHERE event='CONTENT_GENERATED'").fetchone()[0], 1)

    def test_rpc_errors_are_structured_and_bilingual(self):
        for module in ("producer", "receiver"):
            with self.subTest(module=module):
                client = self.client(module)
                response = client.call("unsupported", {})
                self.assertFalse(response["ok"])
                self.assertEqual(response["code"], "UNSUPPORTED_OPERATION")
                self.assertEqual(set(response["detail"]), {"en", "fr"})
                self.assertNotEqual(response["detail"]["en"], response["detail"]["fr"])


if __name__ == "__main__":
    unittest.main()
