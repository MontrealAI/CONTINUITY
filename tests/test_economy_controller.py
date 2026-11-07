"""Actual local orchestration, retained failures and independent receipt gating.

Reduced challenge data tests integration. They are not registered method-value
comparisons. The component tests do not turn producer metadata into acceptance.
"""
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from continuity_economy.controller import Controller, database_digest, finalized_database, localized_error, MESSAGES
from continuity_economy.schema import HarnessError, digest, strict_load

ROOT = Path(__file__).resolve().parents[1]


def tiny_fixture(name="primary-recovery"):
    item = strict_load(ROOT / "experiments/economy-v0.2/fixtures" / (name + ".json"))
    c, p = deepcopy(item["contract"]), deepcopy(item["policies"])
    c.update(run_id="component-integration", fixture_id="component-integration", cohort="challenge", lot_size=2)
    for obligation in c["obligations"]:
        if obligation["status"] == "ACTIVE":
            obligation["quantity"] = 4 if obligation["obligation_id"] == "DL-100" else 3
    for event in c["source_events"]:
        if "obligation" in event and event["obligation_id"] in ("DL-100", "DL-200"):
            event["obligation"]["quantity"] = 4 if event["obligation_id"] == "DL-100" else 3
    c["source_sha256"] = digest(c["source_events"])
    for provider in c["providers"]:
        for window in provider["windows"]:
            window["capacity"] = 6 if provider["role"] == "alternative" else 20
    return c, p


def rows(path, table):
    with sqlite3.connect(Path(path).as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        return [dict(r) for r in db.execute("SELECT * FROM " + table)]


class ControllerIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def execute(self, name="primary-recovery", method="harness", modify=None, controller_type=Controller):
        c, p = tiny_fixture(name)
        if modify:
            modify(c, p)
        controller = controller_type(c, p, method, self.root / "run", self.root / "authority")
        result = controller.run()
        return controller, result

    def assert_complete_product(self, controller, result):
        self.assertEqual((result["state"], result["target_verdict"]), ("COMPLETE", "COMPLETED"), result["errors"])
        imports = rows(controller.evidence_dir / "receiver.sqlite", "imported_units")
        self.assertEqual(len(imports), 7)
        self.assertEqual({r["obligation_id"] for r in imports}, {"DL-100", "DL-200"})
        self.assertEqual(len({(r["obligation_id"], r["ordinal"]) for r in imports}), 7)
        self.assertEqual({a["status"] for a in rows(controller.evidence_dir / "participants.sqlite", "agreements") if a["status"] != "CANCELLED"}, {"SETTLED"})
        self.assertEqual(set(result["isolation"]["probe"].values()), {True})
        for relative, checksum in result["db_snapshots"].items():
            self.assertEqual(database_digest(controller.run_dir / relative), checksum)
            self.assertFalse(Path(str(controller.run_dir / relative) + "-wal").exists())
            self.assertFalse(Path(str(controller.run_dir / relative) + "-shm").exists())
        seal = strict_load(controller.authority_dir / "execution.json")
        self.assertEqual(seal["controller_sha256"], digest(result))
        self.assertEqual(digest(strict_load(controller.authority_dir / "reference.json")), controller.reference_sha256)

    def test_real_primary_recovery_materialization_receipt_acceptance_settlement(self):
        controller, result = self.execute()
        self.assert_complete_product(controller, result)
        recovery = [e for e in result["events"] if e["event"] == "PRIMARY_RESTORED"]
        self.assertEqual(len(recovery), 1)
        self.assertTrue({d["code"] for d in recovery[0]["detail"]["discrepancies"]} >= {"MISSING_ORDER", "STALE_ORDER", "RESURRECTED_CANCELLATION"})
        self.assertGreater(result["resources"]["service_requests"], result["resources"]["requests"])

    def test_primary_does_not_need_external_disclosure_permission(self):
        def change(c, p):
            next(x for x in c["providers"] if x["provider_id"] == "PRIMARY")["permissions"]["disclosure"] = False
        controller, result = self.execute(modify=change)
        self.assert_complete_product(controller, result)
        products = rows(controller.evidence_dir / "producer.sqlite", "productions")
        self.assertEqual({p["provider_id"] for p in products}, {"PRIMARY"})

    def test_mid_write_crash_same_id_retry_rejection_and_costed_correction(self):
        controller, result = self.execute("repair-after-rejection")
        self.assert_complete_product(controller, result)
        products = rows(controller.evidence_dir / "producer.sqlite", "productions")
        attempts = rows(controller.evidence_dir / "producer.sqlite", "attempts")
        self.assertEqual(len(attempts), len(products) + 1)
        self.assertEqual(sum(p["generated_units"] for p in products), 9)
        decisions = rows(controller.evidence_dir / "receiver.sqlite", "decisions")
        self.assertEqual(sum(d["decision"] == "REJECTED" for d in decisions), 1)
        self.assertEqual(sum(d["decision"] == "ACCEPTED" for d in decisions), 4)
        costs = rows(controller.evidence_dir / "participants.sqlite", "entries")
        self.assertEqual(sum(e["kind"] == "REWORK_COST" for e in costs), 1)
        self.assertEqual(result["resources"]["worker_restarts"], 1)
        self.assertTrue(list((controller.runtime_dir / "products").glob("*.part")))
        self.assertFalse(list((controller.evidence_dir / "products").glob("*.part")))

    def test_backup_failure_alternative_lost_ack_and_candidate_restart(self):
        controller, result = self.execute("constructed-continuity")
        self.assert_complete_product(controller, result)
        self.assertEqual(result["resources"]["candidate_restarts"], 1)
        self.assertEqual(result["resources"]["worker_restarts"], 1)
        self.assertEqual({f["event"] for f in result["faults_observed"]}, {
            "BACKUP_FAIL_BEFORE_RESERVE", "ACK_LOST_AFTER_ACCEPTANCE", "CANDIDATE_RESTART_AFTER_ACCEPTANCE"})
        self.assertEqual({p["provider_id"] for p in rows(controller.evidence_dir / "producer.sqlite", "productions")}, {"COMPAT-A", "COMPAT-B"})
        agreements = rows(controller.evidence_dir / "participants.sqlite", "agreements")
        self.assertEqual(sorted(a["status"] for a in agreements), ["CANCELLED", "SETTLED"])
        entries = rows(controller.evidence_dir / "participants.sqlite", "entries")
        self.assertEqual(sum(e["amount_minor"] for e in entries if e["kind"] == "COORDINATION_COST"), 400)
        self.assertEqual(len(rows(controller.evidence_dir / "receiver.sqlite", "decisions")), 4)
        telemetry = [e for e in result["events"] if e["event"] == "CANDIDATE_PLANNING"]
        self.assertGreaterEqual(len(telemetry), 2)

    def test_technical_control_produces_but_does_not_create_accepted_trade(self):
        controller, result = self.execute("technical-no-trade")
        self.assert_complete_product(controller, result)
        agreements = rows(controller.evidence_dir / "participants.sqlite", "agreements")
        self.assertEqual({a["kind"] for a in agreements}, {"TECHNICAL"})
        proposals = rows(controller.evidence_dir / "participants.sqlite", "proposals")
        self.assertEqual({p["status"] for p in proposals}, {"REJECTED"})
        entries = rows(controller.evidence_dir / "participants.sqlite", "entries")
        self.assertFalse(any(e["kind"] in ("PROVIDER_PAYMENT", "COORDINATOR_PAYMENT") for e in entries))
        self.assertTrue(any(e["from_party"] == "TECHNICAL-SPONSOR" for e in entries))

    def test_no_action_runs_services_without_manufacturing_products(self):
        controller, result = self.execute(method="outside")
        self.assertEqual((result["state"], result["target_verdict"]), ("COMPLETE", "OUTSIDE_OPTION"))
        self.assertEqual(rows(controller.evidence_dir / "receiver.sqlite", "imported_units"), [])
        self.assertEqual(rows(controller.evidence_dir / "participants.sqlite", "agreements"), [])

    def test_ai_unavailable_is_not_run_with_no_execution(self):
        controller, result = self.execute(method="ai")
        self.assertEqual((result["state"], result["target_verdict"]), ("NOT_RUN", "NOT_RUN"))
        self.assertEqual(controller.children, [])
        self.assertEqual(strict_load(controller.authority_dir / "execution.json")["files"], {})
        self.assertTrue((controller.authority_dir / "contract.json").is_file())

    def test_funding_change_after_proposal_is_preserved_and_prevents_trade(self):
        def change(c, p):
            c["fault_schedule"] = [{"event": "FUNDING_WITHDRAWAL_AFTER_PROPOSE", "trigger": "propose",
                                    "occurrence": 1, "target": "BUYER", "value": p["buyer"]["balance_minor"]}]
            c["bounds"]["max_proposals"] = 2
        controller, result = self.execute(modify=change)
        self.assertEqual(result["state"], "COMPLETE", result["errors"])
        self.assertNotEqual(result["target_verdict"], "COMPLETED")
        self.assertEqual(rows(controller.evidence_dir / "receiver.sqlite", "imported_units"), [])
        proposals = rows(controller.evidence_dir / "participants.sqlite", "proposals")
        self.assertEqual(len(proposals), 1)
        self.assertEqual(result["target_verdict"], "NO_DEAL")
        self.assertEqual({p["status"] for p in proposals}, {"REJECTED"})
        self.assertTrue(any(e["kind"] == "WITHDRAWAL" for e in rows(controller.evidence_dir / "participants.sqlite", "entries")))

    def test_price_change_requires_new_proposal_and_frozen_policy_revision(self):
        def change(c, p):
            c["fault_schedule"] = [{"event": "POLICY_CHANGE_AFTER_PROPOSE", "trigger": "propose",
                                    "occurrence": 1, "target": "PRIMARY", "value": 2}]
        controller, result = self.execute(modify=change)
        self.assert_complete_product(controller, result)
        proposals = rows(controller.evidence_dir / "participants.sqlite", "proposals")
        self.assertEqual([p["status"] for p in proposals], ["REJECTED", "ACCEPTED"])
        self.assertEqual([p["policy_revision"] for p in proposals], [1, 2])
        policies = rows(controller.evidence_dir / "participants.sqlite", "policy_versions")
        self.assertEqual(len(policies), 2)

    def test_malformed_broker_request_cannot_apply_scheduled_effect(self):
        c, p = tiny_fixture()
        c["fault_schedule"] = [{"event": "PERMISSION_REVOKE_BEFORE_TRANSFER", "trigger": "transfer",
                                "occurrence": 1, "target": "BACKUP", "value": 0}]
        controller = Controller(c, p, "harness", self.root / "run", self.root / "authority")
        controller.initialize()
        try:
            with self.assertRaises(HarnessError):
                controller.broker("transfer", {"production_id": "bad", "path": "/tmp/arbitrary"})
            for args, code in (({"provider_id":"UNKNOWN", "window_id":"W0"}, "UNKNOWN_PROVIDER"),
                               ({"provider_id":"PRIMARY", "window_id":"UNKNOWN"}, "UNKNOWN_WINDOW")):
                with self.assertRaises(HarnessError) as error: controller.broker("restore", args)
                self.assertEqual(error.exception.code, code)
            self.assertTrue(controller.effective_permissions["BACKUP"]["disclosure"])
            self.assertEqual(controller.record["faults_observed"], [])
            self.assertEqual(controller.call("participants", "snapshot")["entries"], [])
        finally:
            controller.close_children()

    def test_two_real_capacity_requests_race_for_last_slot_without_overallocation(self):
        def change(c, p):
            c["seed"] = 700
            c["fault_schedule"] = [{"event": "CAPACITY_COMPETITION", "trigger": "reserve",
                                    "occurrence": 1, "target": "PRIMARY", "value": 2}]
        controller, result = self.execute(modify=change)
        self.assertEqual((result["state"], result["target_verdict"]), ("COMPLETE", "PARTIAL"), result["errors"])
        self.assertEqual(len(rows(controller.evidence_dir / "receiver.sqlite", "imported_units")), 2)
        race = next(e["detail"] for e in result["events"] if e["event"] == "CAPACITY_COMPETITION")
        self.assertEqual([r["ok"] for r in race["responses"]], [True, False])
        self.assertEqual(race["responses"][1]["code"], "CAPACITY_EXCEEDED")
        allocations = rows(controller.evidence_dir / "capacity/PRIMARY.W0.sqlite", "reservations")
        self.assertEqual(sum(a["quantity"] for a in allocations if a["status"] in ("RESERVED", "COMMITTED", "FULFILLED")), 2)
        self.assertTrue(any(e["event"] == "CAPACITY_RACE_BARRIER" for e in result["events"]))
        self.assertEqual(rows(controller.evidence_dir / "participants.sqlite", "agreements")[0]["status"], "ACTIVE")
        self.assertTrue(rows(controller.evidence_dir / "participants.sqlite", "holds"))

    def test_broker_cannot_cancel_accrued_recipient_acceptance(self):
        from continuity_economy.planning import choose_plan, make_proposal
        c, p = tiny_fixture()
        controller = Controller(c, p, "harness", self.root / "run", self.root / "authority")
        controller.initialize()
        try:
            state = controller.broker("status", {})
            proposal = make_proposal(state, choose_plan(state)["plan"], 1)
            controller.broker("propose", {"proposal": proposal})
            agreement = controller.broker("decide", {"proposal_id": proposal["proposal_id"]})["agreement"]
            aid = agreement["agreement_id"]; lot = proposal["allocations"][0]
            controller.broker("restore", {"provider_id":lot["provider_id"], "window_id":lot["window_id"]})
            args = {"agreement_id":aid, "lot_id":lot["lot_id"], "attempt":1}
            controller.broker("reserve", args)
            controller.broker("produce", {**args, "supersedes":None})
            pid = aid + "." + lot["lot_id"] + ".A1"
            controller.broker("transfer", {"production_id":pid})
            accepted = controller.broker("inspect", {"delivery_id":pid + ".D"})
            self.assertEqual(accepted["status"], "ACCEPTED")
            before = controller.call("participants", "snapshot")
            with self.assertRaises(HarnessError) as error:
                controller.broker("cancel", {"agreement_id":aid, "reason":"CAPACITY_EXCEEDED"})
            self.assertEqual(error.exception.code, "ACCRUED_ACCEPTANCE")
            self.assertEqual(controller.call("participants", "snapshot"), before)
        finally:
            controller.close_children()

    def test_frozen_consent_revocation_blocks_affected_production(self):
        def change(c, p):
            c["revocations"] = [{"party_id": "PRIMARY", "tick": 15, "action": "produce"}]
            c["fault_schedule"] = [{"event": "CONSENT_REVOKE_BEFORE_PRODUCTION", "trigger": "produce",
                                    "occurrence": 1, "target": "PRIMARY", "value": 0}]
        controller, result = self.execute(modify=change)
        self.assert_complete_product(controller, result)
        self.assertNotIn("PRIMARY", {p["provider_id"] for p in rows(controller.evidence_dir / "producer.sqlite", "productions")})
        refusals = [e for e in result["events"] if e["event"] == "BROKER_REFUSED"]
        self.assertTrue(any(e["detail"]["code"] == "CONSENT_REVOKED" for e in refusals))

    def test_late_inspection_cannot_settle_or_import_units(self):
        def change(c, p):
            c["fault_schedule"] = [{"event": "LATE_ACCEPTANCE", "trigger": "inspect",
                                    "occurrence": 1, "target": "ANY", "value": 1}]
        controller, result = self.execute(modify=change)
        self.assertNotEqual(result["target_verdict"], "COMPLETED")
        self.assertEqual(rows(controller.evidence_dir / "receiver.sqlite", "imported_units"), [])
        self.assertTrue(rows(controller.evidence_dir / "producer.sqlite", "productions"))
        self.assertFalse(any(a["status"] == "SETTLED" for a in rows(controller.evidence_dir / "participants.sqlite", "agreements")))

    def test_bounded_request_exhaustion_preserves_incomplete_state(self):
        def change(c, p):
            c["bounds"]["max_requests"] = 1
        controller, result = self.execute(modify=change)
        self.assertEqual((result["state"], result["target_verdict"]), ("INCOMPLETE", "NOT_ESTABLISHED"), result["errors"])
        self.assertEqual(result["errors"][0]["code"], "REQUEST_BUDGET_EXHAUSTED")
        self.assertEqual(rows(controller.evidence_dir / "receiver.sqlite", "imported_units"), [])

    def test_live_database_change_after_capture_cannot_finalize_favorably(self):
        class ChangedAfterCapture(Controller):
            def capture(self):
                super().capture()
                with sqlite3.connect(self.runtime_dir / "receiver.sqlite") as db:
                    db.execute("UPDATE imported_units SET name_en='unqualified replacement' WHERE ordinal=1")
        controller, result = self.execute(controller_type=ChangedAfterCapture)
        self.assertEqual((result["state"], result["target_verdict"]), ("ERROR", "ERROR"))
        self.assertTrue(any(e["code"] == "DATABASE_STATE_CHANGED" for e in result["errors"]))
        self.assertTrue((controller.run_dir / "runtime/receiver.sqlite").exists())

    def test_authority_must_not_be_inside_candidate_execution_tree(self):
        c, p = tiny_fixture()
        with self.assertRaises(HarnessError):
            Controller(c, p, "harness", self.root / "run", self.root / "run/authority")
        self.assertFalse((self.root / "run").exists())


class DurableSnapshotTests(unittest.TestCase):
    def test_controller_refusals_have_complete_english_and_french_explanations(self):
        for code in (*MESSAGES, "CONSENT_REVOKED", "WRONG_CONTENT", "UNKNOWN_FUTURE_REFUSAL"):
            with self.subTest(code=code):
                translated = localized_error(code)
                self.assertEqual(set(translated), {"en", "fr"})
                self.assertNotEqual(translated["en"], translated["fr"])
                self.assertTrue(all(type(value) is str and len(value) > 10 and value != code for value in translated.values()))

    def test_backup_carries_committed_wal_and_byte_content_without_sidecars(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            source, target = folder / "source.sqlite", folder / "final.sqlite"
            db = sqlite3.connect(source)
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("CREATE TABLE artifacts(id TEXT PRIMARY KEY, content BLOB)")
            db.execute("INSERT INTO artifacts VALUES (?,?)", ("retained", b"substantive content\x00\xff"))
            db.commit()
            expected = database_digest(source)
            finalized_database(source, target, expected)
            self.assertEqual(database_digest(target), expected)
            self.assertEqual(rows(target, "artifacts")[0]["content"], b"substantive content\x00\xff")
            self.assertFalse(Path(str(target) + "-wal").exists())
            self.assertFalse(Path(str(target) + "-shm").exists())
            db.close()


if __name__ == "__main__":
    unittest.main()
