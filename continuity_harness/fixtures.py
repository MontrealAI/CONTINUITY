"""Authored local service scenarios, derived from the registered experiment.

The original event motif is attributed to continuity_omega/demo.py at
8776d70ba091f71dab12fc9d3195baf7fc789676.  No historical file is changed.
"""

from copy import deepcopy
from pathlib import Path

from .schema import digest, strict_load, validate_contract


SPEC_PATH = Path(__file__).resolve().parents[1] / "experiments/harness-v0.1/spec.json"


def specification():
    return strict_load(SPEC_PATH)


def make_contract(fixture_id="labels-base", scenario="recovery", method="harness", run_id=None):
    spec = specification()
    config = next((x for x in spec["fixtures"] if x["id"] == fixture_id), None)
    if config is None or scenario not in spec["controls"]:
        raise ValueError("UNKNOWN_FIXTURE_OR_SCENARIO")
    q1, q2 = config["quantities"]
    final_spec = digest({"product": "LABEL-A", "fixture": fixture_id, "revision": 2})
    old_spec = digest({"product": "LABEL-A", "fixture": fixture_id, "revision": 1})
    def accepted(seq, oid, quantity, recipient):
        return {"sequence": seq, "type": "ACCEPT", "order_id": oid,
                "recipient": recipient, "product": "LABEL-A", "spec_sha256": old_spec,
                "quantity": quantity, "deadline_tick": spec["clock"]["deadline_tick"]}
    events = [accepted(1, "LBL-100", max(1, q1 - 100), "CUSTOMER-A"),
              accepted(2, "LBL-200", q2, "CUSTOMER-B"),
              accepted(3, "LBL-300", 600, "CUSTOMER-C"),
              {"sequence": 4, "type": "AMEND", "order_id": "LBL-100", "quantity": q1, "spec_sha256": final_spec},
              {"sequence": 5, "type": "CANCEL", "order_id": "LBL-300"}]
    if config["held_out"]:
        events.append({"sequence": 6, "type": "AMEND", "order_id": "LBL-200", "spec_sha256": final_spec})
    run_id = run_id or f"{fixture_id}-{scenario}-{method}"
    fault_schedule = []
    if scenario != "recovery":
        fault_schedule.append({"event": "PRIMARY_UNAVAILABLE", "action": "DISABLE", "target": "primary"})
    if scenario == "constrained":
        for event, action, target in [
            ("CONCURRENT_FINAL_CAPACITY", "RACE", "backup"),
            ("ACK_LOST_AFTER_DURABLE_FULFILLMENT", "DROP_ACK", "service"),
            ("RETRY_WHILE_OUTCOME_UNKNOWN", "RETRY", "service"),
            ("SERVICE_KILLED_AFTER_COMMIT", "KILL", "service"),
            ("CANDIDATE_KILLED_AFTER_REQUEST", "KILL", "candidate"),
            ("RESTART_RECONCILIATION", "RESTART", "candidate")]:
            fault_schedule.append({"event": event, "action": action, "target": target})
    primary_domain = "GRID-A" if not config["held_out"] else f"GRID-{config['seed']}"
    contract = {
        "schema": "continuity-harness/contract/v1", "version": 1,
        "contract_id": f"CONTRACT-{fixture_id}-{scenario}", "run_id": run_id,
        "mode": "SYNTHETIC_LOCAL_EXECUTION", "source_events": events,
        "source_sha256": digest(events), "cutoff_sequence": len(events), "source_complete": True,
        "deadline_tick": spec["clock"]["deadline_tick"], "wall_deadline_ms": spec["clock"]["wall_deadline_ms"],
        "recovery_objective_ms": spec["clock"]["recovery_objective_ms"],
        "window": {"start": 0, "end": spec["clock"]["deadline_tick"]},
        "lease_ticks": spec["clock"]["lease_ticks"],
        "capacities": {"primary": config["primary_capacity"], "backup": config["constrained_capacity"] if scenario == "constrained" else config["backup_capacity"]},
        "allowed_routes": ["primary", "backup"], "permissions": {"activation": True, "sharing": True},
        "dependencies": {"primary": primary_domain, "backup": primary_domain + "-INDEPENDENT"},
        "blocked_dependencies": [] if scenario == "recovery" else [primary_domain],
        "currency": "USD", "budget_minor": 0, "scenario": scenario, "seed": config["seed"],
        "fault_schedule": fault_schedule,
        "comparison": {"suite_id": spec["experiment_id"], "fixture_id": fixture_id,
                       "held_out": config["held_out"], "information": "EQUAL", "resource_policy": "SHARED_SERVICES"},
    }
    return validate_contract(contract)


def stale_snapshot(contract):
    # Authored stale snapshot: pre-amendment first order, missing second order,
    # and an order cancelled after this snapshot.  Source events remain separate.
    return [{k: e[k] for k in ("order_id", "recipient", "product", "spec_sha256", "quantity", "deadline_tick")}
            for e in contract["source_events"] if e["type"] == "ACCEPT" and e["order_id"] != "LBL-200"]


def candidate_view(contract, snapshot=None):
    return {"contract": deepcopy(contract), "snapshot": deepcopy(snapshot if snapshot is not None else stale_snapshot(contract))}
