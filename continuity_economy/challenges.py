"""Registered live challenges and deliberately defective-verifier controls.

The observer reopens durable evidence on every invocation.  Altered packages are
separate, explicitly trusted test interventions; protected originals survive.
No saved assertion, component PASS, or Passport is an acceptance oracle.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import shutil
import sqlite3
import time
from unittest.mock import patch
import uuid

from continuity_harness.schema import HarnessError, canonical, digest, object_fields, strict_load, strict_loads
from .controller import Controller, database_digest, fresh_directory, write_json
from .fixtures import EXPERIMENT, load_fixture
from .reporting import write_passports
from . import verifier


REGISTRY = EXPERIMENT / "challenges.json"


def registry():
    value = strict_load(REGISTRY)
    if value.get("schema") != "continuity-economy/challenge-spec/v1" or value.get("version") != "0.2.0":
        raise HarnessError("UNSUPPORTED_VERSION", "challenge registration")
    return value, hashlib.sha256(REGISTRY.read_bytes()).hexdigest()


def _safe_relative(root, relative):
    if type(relative) is not str or not relative or "\\" in relative:
        raise HarnessError("UNSAFE_PATH")
    path = Path(relative)
    if path.is_absolute() or path.as_posix() != relative or any(piece in {".", ".."} for piece in path.parts):
        raise HarnessError("UNSAFE_PATH")
    result = Path(root) / path
    if any(p.is_symlink() for p in (result, *result.parents)):
        raise HarnessError("UNSAFE_PATH")
    return result


def _rows(run, service, table):
    if service not in {"receiver", "producer", "participants"}:
        raise HarnessError("INVALID_TYPE", "challenge service")
    if table not in {"receipts", "decisions", "observations", "productions", "events", "agreements"}:
        raise HarnessError("INVALID_TYPE", "challenge table")
    db = sqlite3.connect((Path(run) / ("evidence/" + service + ".sqlite")).as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in db.execute("SELECT * FROM " + table)]
    finally:
        db.close()


def _edit_database(path, callback):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA journal_mode=DELETE")
        with db:
            callback(db)
    finally:
        db.close()


def _copy_package(source_run, source_authority, run, authority):
    fresh_directory(run)
    fresh_directory(authority)
    shutil.copytree(Path(source_run) / "evidence", Path(run) / "evidence")
    shutil.copy2(Path(source_run) / "controller.json", Path(run) / "controller.json")
    for name in ("contract.json", "policies.json", "capacity-inputs.json", "reference.json", "execution.json"):
        shutil.copy2(Path(source_authority) / name, Path(authority) / name)


def _replace_intervention_json(path, value):
    """Replace only a separately copied test package; preserve its source."""
    path = Path(path)
    temporary = path.with_name("." + path.name + ".challenge-intervention")
    with temporary.open("xb") as stream:
        stream.write(canonical(value) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    descriptor = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def reseal_intervention(run, authority):
    """Explicit test privilege: rebind byte seals without changing authority.

    Ordinary candidate adapters have no access to this helper or these files.
    This distinguishes semantic checking from incidental checksum rejection.
    """
    run, authority = Path(run), Path(authority)
    controller = strict_load(run / "controller.json")
    for relative in controller["db_snapshots"]:
        controller["db_snapshots"][relative] = database_digest(_safe_relative(run, relative))
    _replace_intervention_json(run / "controller.json", controller)
    seal = strict_load(authority / "execution.json")
    seal["controller_sha256"] = digest(controller)
    seal["files"] = {p.relative_to(run).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted((run / "evidence").rglob("*")) if p.is_file()}
    _replace_intervention_json(authority / "execution.json", seal)


def _event_content_hashes(db, identity, value, checksum, size):
    for row in db.execute("SELECT sequence,detail FROM events WHERE " + identity + "=?", (value,)).fetchall():
        detail = strict_loads(row["detail"])
        if "sha256" in detail:
            detail["sha256"] = checksum
        if "bytes" in detail:
            detail["bytes"] = size
        db.execute("UPDATE events SET detail=? WHERE sequence=?", (canonical(detail).decode(), row["sequence"]))


def alter_product(run, mutation):
    """Coherently rewrite raw bytes, producer claims and recipient-side hashes."""
    run = Path(run)
    receipt = min(_rows(run, "receiver", "receipts"), key=lambda row: row["delivery_id"])
    did, original = receipt["delivery_id"], receipt["raw"]
    document = strict_loads(original)
    if mutation == "wrong_content":
        document["labels"][0]["name_en"] = "A different digital product"
    elif mutation == "wrong_recipient":
        document["recipient"] = "WRONG-RECIPIENT"
    elif mutation == "stale_revision":
        document["revision"] = 1
    elif mutation == "duplicate_unit":
        document["labels"][-1] = deepcopy(document["labels"][0])
    elif mutation != "truncated":
        raise HarnessError("UNSUPPORTED_OPERATION", mutation)
    raw = canonical(document)
    if mutation == "truncated":
        raw = raw[:len(raw) // 2]
    checksum, pid = hashlib.sha256(raw).hexdigest(), document["production_id"]

    def producer_change(db):
        db.execute("UPDATE productions SET payload=?,payload_sha256=?,byte_count=? WHERE production_id=?", (raw, checksum, len(raw), pid))
        db.execute("UPDATE observations SET payload_sha256=?,byte_count=? WHERE production_id=?", (checksum, len(raw), pid))
        _event_content_hashes(db, "production_id", pid, checksum, len(raw))

    def receiver_change(db):
        db.execute("UPDATE receipts SET raw=?,content_sha256=?,byte_count=? WHERE delivery_id=?", (raw, checksum, len(raw), did))
        db.execute("UPDATE decisions SET content_sha256=?,recipient=?,revision=? WHERE delivery_id=?", (checksum, document["recipient"], document["revision"], did))
        db.execute("UPDATE observations SET content_sha256=? WHERE delivery_id=?", (checksum, did))
        _event_content_hashes(db, "delivery_id", did, checksum, len(raw))
        if mutation == "wrong_content":
            db.execute("UPDATE imported_units SET name_en=? WHERE obligation_id=? AND ordinal=?", (document["labels"][0]["name_en"], document["obligation_id"], document["labels"][0]["ordinal"]))

    _edit_database(run / "evidence/producer.sqlite", producer_change)
    _edit_database(run / "evidence/receiver.sqlite", receiver_change)
    (run / "evidence/products" / (pid + ".json")).write_bytes(raw)
    (run / "evidence/inbox" / (did + ".json")).write_bytes(raw)
    return {"delivery_id": did, "original_sha256": hashlib.sha256(original).hexdigest(),
            "altered_sha256": checksum, "mutation": mutation}


def alter_evidence(run, authority, mutation, *, other_run=None):
    run, authority = Path(run), Path(authority)
    detail = {"mutation": mutation, "trust": "DELIBERATE_TEST_INTERVENTION"}
    if mutation in {"wrong_content", "wrong_recipient", "stale_revision", "duplicate_unit", "truncated"}:
        detail.update(alter_product(run, mutation))
    elif mutation == "missing_import":
        def change(db):
            row = db.execute("SELECT obligation_id,ordinal FROM imported_units ORDER BY obligation_id,ordinal LIMIT 1").fetchone()
            db.execute("DELETE FROM imported_units WHERE obligation_id=? AND ordinal=?", tuple(row))
        _edit_database(run / "evidence/receiver.sqlite", change)
    elif mutation == "balanced_wrong_payment":
        def change(db):
            provider = db.execute("SELECT * FROM entries WHERE kind='PROVIDER_PAYMENT' ORDER BY sequence LIMIT 1").fetchone()
            coordinator = db.execute("SELECT * FROM entries WHERE kind='COORDINATOR_PAYMENT' ORDER BY sequence LIMIT 1").fetchone()
            db.execute("UPDATE entries SET amount_minor=amount_minor+1 WHERE sequence=?", (provider["sequence"],))
            db.execute("UPDATE entries SET amount_minor=amount_minor-1 WHERE sequence=?", (coordinator["sequence"],))
            db.execute("UPDATE accounts SET balance_minor=balance_minor+1 WHERE party_id=?", (provider["to_party"],))
            db.execute("UPDATE accounts SET balance_minor=balance_minor-1 WHERE party_id=?", (coordinator["to_party"],))
        _edit_database(run / "evidence/participants.sqlite", change)
    elif mutation == "invented_acceptance":
        def change(db):
            agreement = db.execute("SELECT * FROM agreements WHERE status='SETTLED' LIMIT 1").fetchone()
            refs = ["INVENTED-ACCEPTANCE-" + str(i) for i, _ in enumerate(strict_loads(agreement["acceptance_ids"]), 1)]
            db.execute("UPDATE agreements SET acceptance_ids=? WHERE agreement_id=?", (canonical(refs).decode(), agreement["agreement_id"]))
            for row in db.execute("SELECT sequence,detail FROM entries WHERE agreement_id=?", (agreement["agreement_id"],)).fetchall():
                data = strict_loads(row["detail"])
                if "acceptance_ids" in data:
                    data["acceptance_ids"] = refs
                    db.execute("UPDATE entries SET detail=? WHERE sequence=?", (canonical(data).decode(), row["sequence"]))
            for row in db.execute("SELECT sequence,payload FROM events WHERE kind='RECIPIENT_ACCEPTANCE_REFERENCES'").fetchall():
                data = strict_loads(row["payload"])
                data["acceptance_ids"] = refs
                db.execute("UPDATE events SET payload=? WHERE sequence=?", (canonical(data).decode(), row["sequence"]))
        _edit_database(run / "evidence/participants.sqlite", change)
    elif mutation in {"missing_observation", "late_observation"}:
        decision = max(_rows(run, "receiver", "decisions"), key=lambda row: row["inspected_ns"])
        did = decision["delivery_id"]
        if mutation == "missing_observation":
            _edit_database(run / "evidence/receiver.sqlite", lambda db: db.execute("DELETE FROM observations WHERE delivery_id=?", (did,)))
        else:
            contract = strict_load(authority / "contract.json")
            observation = next(row for row in _rows(run, "receiver", "observations") if row["delivery_id"] == did)
            observed_ns = contract["start_ns"] + contract["wall_deadline_ms"] * 1_000_000 + 1
            delta = max(1, observed_ns - observation["observed_ns"])
            def change(db):
                db.execute("UPDATE observations SET observed_ns=? WHERE delivery_id=?", (observed_ns, did))
                rows = db.execute("SELECT * FROM events ORDER BY sequence").fetchall()
                for row in rows:
                    data = strict_loads(row["detail"])
                    stamp = row["observed_ns"]
                    if row["event"] == "DECISION_OBSERVED" and row["delivery_id"] == did:
                        data["observed_ns"] = observed_ns
                    if stamp >= observation["observed_ns"]:
                        stamp += delta
                    db.execute("UPDATE events SET observed_ns=?,detail=? WHERE sequence=?", (stamp, canonical(data).decode(), row["sequence"]))
            _edit_database(run / "evidence/receiver.sqlite", change)
            controller = strict_load(run / "controller.json")
            for event in controller["events"]:
                if event["monotonic_ns"] >= observation["observed_ns"]:
                    event["monotonic_ns"] += delta
            controller["finished_monotonic_ns"] += delta
            _replace_intervention_json(run / "controller.json", controller)
            detail["observed_ns"] = observed_ns
    elif mutation == "mixed_receiver":
        if other_run is None:
            raise HarnessError("MISSING_FILE", "second actual run")
        shutil.copy2(Path(other_run) / "evidence/receiver.sqlite", run / "evidence/receiver.sqlite")
    elif mutation == "missing_pin":
        pass
    else:
        raise HarnessError("UNSUPPORTED_OPERATION", mutation)
    reseal_intervention(run, authority)
    return detail


def _fixture_for(case, registration):
    fixture = load_fixture(case["fixture"])
    contract, policies = fixture["contract"], fixture["policies"]
    contract.update(fixture_id=case["id"], cohort="challenge", seed=registration["seed"],
                    run_id=case["id"] + "." + uuid.uuid4().hex[:10], start_ns=0)
    contract["fault_schedule"] = [deepcopy(case["fault"])] if "fault" in case else []
    mutation = case.get("mutation")
    if mutation == "source_incomplete":
        contract["source_complete"] = False
    elif mutation == "quantity_1850_original_pin":
        for order in contract["obligations"]:
            if order["obligation_id"] == "DL-100":
                order["quantity"] = 1050
        for event in contract["source_events"]:
            if event["type"] == "AMEND" and event["obligation_id"] == "DL-100":
                event["obligation"]["quantity"] = 1050
        contract["source_sha256"] = digest(contract["source_events"])
    elif mutation == "withdraw_buyer_available_balance":
        contract["fault_schedule"] = [{"event": "FUNDING_WITHDRAWAL_AFTER_PROPOSE", "trigger": "propose", "occurrence": 1,
                                        "target": policies["buyer"]["party_id"], "value": policies["buyer"]["balance_minor"]}]
    elif mutation == "backup_shares_primary_dependency":
        primary = next(p for p in contract["providers"] if p["role"] == "primary")
        next(p for p in contract["providers"] if p["provider_id"] == "BACKUP")["dependency"] = primary["dependency"]
    elif mutation == "revoke_primary_production_at_tick_10":
        contract["revocations"] = [{"tick": 10, "party_id": "PRIMARY", "action": "produce"}]
        contract["fault_schedule"] = [{"event": "CONSENT_REVOKE_BEFORE_PRODUCTION", "trigger": "produce", "occurrence": 1,
                                        "target": "PRIMARY", "value": 0}]
    return fixture


def verify_mutant(run, authority, pin, mutation):
    """Invoke explicit defective checkers; callers must qualify them as FAILED."""
    original = verifier._inspect_product
    if mutation == "ignore_wrong_content":
        def unchecked(raw, contract):
            result = original(raw, contract)
            result["codes"] = [code for code in result["codes"] if code != "WRONG_CONTENT"]
            result["valid"] = not result["codes"]
            return result
        target, replacement = "_inspect_product", unchecked
    elif mutation == "ignore_deadline":
        target, replacement = "_observed_clock", lambda *args, **kwargs: True
    elif mutation == "reject_valid_content":
        def reject(raw, contract):
            result = original(raw, contract)
            result["valid"] = False
            result["codes"] = [*result["codes"], "MUTANT_REJECTS_VALID_CONTENT"]
            return result
        target, replacement = "_inspect_product", reject
    else:
        raise HarnessError("UNSUPPORTED_OPERATION", mutation)
    with patch.object(verifier, target, replacement):
        return verifier.verify_run(run, authority, expected_reference_sha256=pin)


def _assertion(case, result, run, authority, *, target=None, controller=None):
    criterion = case["criterion"]
    codes = {row["code"] for row in result["failures"] + result["unresolved"]}
    outcome, safety = result["claims"]["outcome"], result["safety_status"]
    accepted = result["totals"]["accepted_quantity"]
    controller = controller or strict_load(Path(run) / "controller.json")
    if criterion == "VALID_1900_COMPLETION":
        ok = outcome == result["claims"]["service_feasibility"] == safety == "DEMONSTRATED" and accepted == 1900
    elif criterion == "FALSE_ACCEPTANCE_DETECTED":
        ok = outcome == safety == "FAILED" and "FALSE_RECIPIENT_ACCEPTANCE" in codes
    elif criterion == "IMPORTED_CONTENT_DETECTED":
        ok = outcome == "FAILED" and "IMPORTED_CONTENT_INCOMPLETE" in codes
    elif criterion == "PAYMENT_SEMANTICS_DETECTED":
        ok = safety == "FAILED" and "FINANCIAL_EFFECT_MISMATCH" in codes and result["accounting"]["initial_total_minor"] == result["accounting"]["final_total_minor"]
    elif criterion == "SETTLEMENT_REPLAY_DETECTED":
        ok = safety == "FAILED" and "SETTLEMENT_WITHOUT_ACCEPTED_CONTENT" in codes
    elif criterion == "AUTHORITY_NOT_ESTABLISHED":
        ok = result["authority_status"] == "NOT_ESTABLISHED" and outcome == result["claims"]["service_feasibility"] == "NOT_ESTABLISHED"
    elif criterion == "ORIGINAL_1900_PIN_PRESERVED":
        quantity = sum(o["quantity"] for o in strict_load(Path(authority) / "contract.json")["obligations"] if o["status"] == "ACTIVE")
        ok = quantity == 1850 and "REFERENCE_PIN_MISMATCH" in codes and outcome == "FAILED" and accepted == 0
    elif criterion == "MIXED_RUN_DETECTED":
        ok = outcome == "FAILED" and "RECEIVER_DATABASE_BINDING" in codes
    elif criterion == "TIMELINESS_NOT_ESTABLISHED":
        ok = "ACCEPTANCE_OBSERVATION_MISSING" in codes and outcome == "NOT_ESTABLISHED"
    elif criterion == "LATE_ACCEPTANCE_DETECTED":
        ok = outcome == "FAILED" and "LATE_ACCEPTANCE" in codes
    elif criterion == "SAVED_PASS_IGNORED":
        ok = outcome == "FAILED" and accepted == 0 and (Path(run) / "RESULT.stale.json").is_file()
    elif criterion in {"POLICY_REVISION_RECHECKED", "FUNDING_RECHECKED"}:
        expected = "POLICY_REVISION_MISMATCH" if criterion == "POLICY_REVISION_RECHECKED" else "INSUFFICIENT_FUNDS"
        observed = _rows(run, "participants", "decisions")
        ok = safety == "DEMONSTRATED" and any(row["code"] == expected for row in observed)
        if criterion == "FUNDING_RECHECKED":
            ok = ok and outcome == "FAILED"
    elif criterion in {"SHARED_DEPENDENCY_RESPECTED", "CONSENT_REVOCATION_RESPECTED", "DISCLOSURE_REVOCATION_RESPECTED"}:
        productions = _rows(run, "producer", "productions")
        if criterion == "SHARED_DEPENDENCY_RESPECTED":
            ok = not any(row["provider_id"] in {"PRIMARY", "BACKUP"} for row in productions)
        elif criterion == "CONSENT_REVOCATION_RESPECTED":
            ok = not any(row["provider_id"] == "PRIMARY" and row["started_tick"] >= 10 for row in productions)
        else:
            forbidden = {row["delivery_id"] for row in productions if row["provider_id"] == "BACKUP"}
            ok = not any(row["delivery_id"] in forbidden for row in _rows(run, "receiver", "receipts"))
        ok = ok and safety == "DEMONSTRATED" and result["verification_status"] == "COMPLETE"
    elif criterion == "DEADLINE_REFUSAL_PRESERVED":
        deadline = strict_load(Path(authority) / "contract.json")["deadline_tick"]
        refused = any(row["decision"] == "REJECTED" and row["inspected_tick"] > deadline
                      for row in _rows(run, "receiver", "decisions"))
        refused = refused or any(event["event"] == "BROKER_REFUSED" and event["tick"] > deadline
                                 and event["detail"].get("op") == "inspect"
                                 and event["detail"].get("code") in {"PROPOSAL_EXPIRED", "DEADLINE_EXCEEDED"}
                                 for event in controller["events"])
        ok = outcome == "FAILED" and accepted == 0 and safety == "DEMONSTRATED" and refused
    elif criterion == "ONE_FINAL_CAPACITY_WINNER":
        races = [event for event in controller["events"] if event["event"] == "CAPACITY_COMPETITION"]
        responses = races[0]["detail"].get("responses", []) if len(races) == 1 else []
        ok = safety == "DEMONSTRATED" and len(responses) == 2 and sum(row.get("ok") is True for row in responses) == 1
    elif criterion == "FALSE_POSITIVE_MUTANT_EXPOSED":
        ok = outcome == "FAILED" and target is not None and target["claims"]["outcome"] == "DEMONSTRATED"
    elif criterion == "FALSE_NEGATIVE_MUTANT_EXPOSED":
        ok = outcome == "DEMONSTRATED" and target is not None and target["claims"]["outcome"] == "FAILED"
    else:
        raise HarnessError("UNSUPPORTED_OPERATION", criterion)
    if case["kind"] == "live" and strict_load(Path(authority) / "contract.json")["fault_schedule"]:
        ok = ok and not result["untriggered_faults"]
    return {"status": "PASSED" if ok else "FAILED", "criterion": criterion,
            "observed_outcome": outcome, "observed_service_feasibility": result["claims"]["service_feasibility"],
            "observed_safety_status": safety, "accepted_quantity": accepted,
            "finding_codes": sorted(codes), "checker_qualification": "FAILED" if case["kind"] == "verifier_mutation" else "NOT_APPLICABLE"}


def _assess_case(root, case, entry):
    run, authority = _safe_relative(root, entry["run"]), _safe_relative(root, entry["authority"])
    reference = verifier.verify_run(run, authority, expected_reference_sha256=entry["reference_sha256"])
    target = verify_mutant(run, authority, entry["reference_sha256"], case["mutation"]) if case["kind"] == "verifier_mutation" else None
    assertion = _assertion(case, reference, run, authority, target=target)
    report = deepcopy(reference)
    report["assessment"]["test_assertion"] = assertion["status"]
    report["challenge"] = {"id": case["id"], "kind": case["kind"], "criterion": case["criterion"],
                           "assertion": assertion, "execution_reused_from": case.get("source"),
                           "scope": "REGISTERED_SYNTHETIC_CHALLENGE"}
    if case["kind"] == "evidence_intervention":
        report["assessment"]["evidence_stage"] = "EVIDENCE_INTEGRITY_CHALLENGE"
    elif target is not None:
        report["assessment"].update(target_verdict=target["claims"]["outcome"],
                                      evidence_stage="TARGETED_VERIFIER_MUTATION", claim_status="FAILED")
        report["claims"]["checker_qualification"] = "FAILED"
        report["challenge"].update(assessed_claim="CHECKER_QUALIFICATION", checker_qualification="FAILED",
                                   reference_verdict=reference["claims"]["outcome"], target_verdict=target["claims"]["outcome"])
    return report, reference, target


def run_challenges(out_dir):
    spec, spec_sha = registry()
    root = fresh_directory(Path(out_dir).absolute())
    (root / "runs").mkdir(); (root / "authorities").mkdir()
    index = {"schema": "continuity-economy/challenge-index/v1", "version": "0.2.0", "registry_sha256": spec_sha,
             "created_utc": datetime.now(timezone.utc).isoformat(), "entries": []}
    by_id, records = {}, []
    for case in spec["cases"]:
        began = time.monotonic_ns()
        cid = case["id"]
        entry = {"case_id": cid, "run": "runs/" + cid, "authority": "authorities/" + cid,
                 "reference_sha256": None}
        run, authority = root / entry["run"], root / entry["authority"]
        try:
            if case["kind"] == "live":
                fixture = _fixture_for(case, spec)
                controller = Controller(fixture["contract"], fixture["policies"], case.get("method", spec["method"]), run, authority)
                controller.run()
                entry["reference_sha256"] = controller.reference_sha256
                if case.get("mutation") == "quantity_1850_original_pin":
                    entry["reference_sha256"] = by_id["valid-digital-control"]["reference_sha256"]
                if case.get("mutation") == "saved_favorable_report":
                    stale = {"assessment": {"test_assertion": "PASSED", "target_verdict": "PASS", "claim_status": "DEMONSTRATED"},
                             "claims": {"outcome": "DEMONSTRATED", "service_feasibility": "DEMONSTRATED"}, "accepted_quantity": 1900}
                    write_json(run / "RESULT.stale.json", stale)
                    (run / "PASSPORT.stale.en.md").write_text("# CONTINUITY Ω\n\nPASS — 1,900 units claimed by a stale producer report.\n", encoding="utf-8")
                    (run / "PASSPORT.stale.fr.md").write_text("# CONTINUITÉ Ω\n\nRÉUSSITE — 1 900 unités revendiquées par un rapport périmé du producteur.\n", encoding="utf-8")
            else:
                source = by_id[case["source"]]
                _copy_package(root / source["run"], root / source["authority"], run, authority)
                entry["reference_sha256"] = source["reference_sha256"]
                if case["kind"] == "evidence_intervention":
                    other = by_id.get("coherent-1850-rewrite", {}).get("run")
                    intervention = alter_evidence(run, authority, case["mutation"], other_run=root / other if other else None)
                    write_json(run / "INTERVENTION.json", intervention)
                    if case["mutation"] == "missing_pin":
                        entry["reference_sha256"] = None
            report, reference, target = _assess_case(root, case, entry)
            report["challenge"]["observation_wall_ns"] = time.monotonic_ns() - began
            write_json(run / "REFERENCE.json", reference)
            write_json(run / "TARGET.json", target if target is not None else reference)
            write_json(run / "CHALLENGE.json", report)
            write_passports(report, run, context={"registration_sha256": spec_sha, "registered_case": case,
                                                 "command": ["python", "-m", "continuity_economy", "challenge", "--out", str(root)],
                                                 "reference_sha256": entry["reference_sha256"]})
            records.append({"case_id": cid, "test_assertion": report["assessment"]["test_assertion"],
                            "assessment": report["assessment"], "claims": report["claims"],
                            "assertion": report["challenge"]["assertion"]})
        except Exception as exc:
            error = {"case_id": cid, "test_assertion": "FAILED", "code": getattr(exc, "code", "CHALLENGE_INCOMPLETE"),
                     "detail": type(exc).__name__, "claims": {"outcome": "NOT_ESTABLISHED", "service_feasibility": "NOT_ESTABLISHED"}}
            run.mkdir(parents=True, exist_ok=True)
            write_json(run / "CHALLENGE.error.json", error)
            records.append(error)
        index["entries"].append(entry)
        by_id[cid] = entry
        write_json(root / f"INDEX.progress-{len(records):03d}.json", index)
    write_json(root / "INDEX.json", index)
    summary = {"schema": "continuity-economy/challenge-result/v1", "version": "0.2.0", "fresh": False,
               "test_assertion": "PASSED" if all(row["test_assertion"] == "PASSED" for row in records) else "FAILED",
               "records": records, "registered_controls": len(spec["cases"]),
               "actual_live_runs": sum(case["kind"] == "live" for case in spec["cases"]),
               "defective_checkers_qualified": 0,
               "claims": {"method_advantage": "NOT_ESTABLISHED", "general_proof": "NOT_ESTABLISHED", "real_demand": "NOT_ESTABLISHED"}}
    write_json(root / "SUMMARY.json", summary)
    return summary


def verify_challenges(in_dir):
    root = Path(in_dir).absolute()
    spec, checksum = registry()
    index = object_fields(strict_load(root / "INDEX.json"), {"schema", "version", "registry_sha256", "created_utc", "entries"}, path="challenge_index")
    if index["schema"] != "continuity-economy/challenge-index/v1" or index["version"] != "0.2.0" or index["registry_sha256"] != checksum:
        raise HarnessError("REGISTRY_MISMATCH", "challenges")
    expected = {case["id"]: case for case in spec["cases"]}
    entries, records = {}, []
    for entry in index["entries"]:
        object_fields(entry, {"case_id", "run", "authority", "reference_sha256"}, path="challenge_entry")
        cid = entry["case_id"]
        if cid not in expected or cid in entries or entry["run"] != "runs/" + cid or entry["authority"] != "authorities/" + cid:
            raise HarnessError("SUITE_COVERAGE", "challenges")
        entries[cid] = entry
    if set(entries) != set(expected):
        raise HarnessError("SUITE_COVERAGE", "challenges")
    for case in spec["cases"]:
        entry = entries[case["id"]]
        run, authority = _safe_relative(root, entry["run"]), _safe_relative(root, entry["authority"])
        # Check each live exercise still is its registered challenge; random run
        # identity and actual monotonic origin are the only frozen-at-start fields.
        if case["kind"] == "live":
            actual = strict_load(authority / "contract.json")
            authored = _fixture_for(case, spec)
            authored["contract"]["run_id"], authored["contract"]["start_ns"] = actual["run_id"], actual["start_ns"]
            if actual != authored["contract"] or strict_load(authority / "policies.json") != authored["policies"]:
                raise HarnessError("REGISTERED_CONTRACT_MISMATCH", case["id"])
        if case.get("mutation") == "quantity_1850_original_pin":
            wanted_pin = entries["valid-digital-control"]["reference_sha256"]
        elif case.get("mutation") == "missing_pin":
            wanted_pin = None
        else:
            wanted_pin = digest(strict_load(authority / "reference.json"))
        if entry["reference_sha256"] != wanted_pin:
            raise HarnessError("CHALLENGE_REFERENCE_MISMATCH", case["id"])
        report, _, _ = _assess_case(root, case, entry)
        records.append({"case_id": case["id"], "test_assertion": report["assessment"]["test_assertion"],
                        "assessment": report["assessment"], "claims": report["claims"], "assertion": report["challenge"]["assertion"]})
    return {"schema": "continuity-economy/challenge-result/v1", "version": "0.2.0", "fresh": True,
            "test_assertion": "PASSED" if all(row["test_assertion"] == "PASSED" for row in records) else "FAILED",
            "records": records, "registered_controls": len(spec["cases"]), "defective_checkers_qualified": 0,
            "claims": {"method_advantage": "NOT_ESTABLISHED", "general_proof": "NOT_ESTABLISHED", "real_demand": "NOT_ESTABLISHED"}}
