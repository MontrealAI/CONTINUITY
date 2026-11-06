"""Pipe-confined candidate procedures.  No authority/verifier imports.

The conventional procedure uses journal recovery and ordinary transaction /
idempotency tools. The harness procedure also checks reconstructed service state
against its own event replay. Both receive identical inputs and tools.
"""

import argparse
import hashlib
import json
import os
import sys

from .schema import canonical, digest, strict_loads, validate_contract, HarnessError
from .sandbox import activate
from .adapters import ADAPTERS


def reconcile_events(events, cutoff):
    """Candidate replay, separate from the authority verifier's implementation."""
    accepted = {}
    for event in events:
        if event["sequence"] > cutoff:
            continue
        key = event["order_id"]
        if event["type"] == "ACCEPT":
            accepted[key] = {k: event[k] for k in ("order_id", "recipient", "product", "spec_sha256", "quantity", "deadline_tick")}
            accepted[key]["fulfilled"] = 0
            accepted[key]["active"] = True
        elif event["type"] == "AMEND":
            for name, value in event.items():
                if name not in ("sequence", "type", "order_id"):
                    accepted[key][name] = value
        elif event["type"] == "FULFILL":
            accepted[key]["fulfilled"] += event["quantity"]
        elif event["type"] == "CANCEL":
            accepted[key]["active"] = False
    result = []
    for order in accepted.values():
        quantity = order["quantity"] - order["fulfilled"]
        if order["active"] and quantity > 0:
            result.append({k: order[k] for k in ("order_id", "recipient", "product", "spec_sha256", "deadline_tick")} | {"quantity": quantity})
    return sorted(result, key=lambda x: (x["deadline_tick"], x["order_id"]))


def emit(value):
    sys.stdout.buffer.write(canonical(value) + b"\n")
    sys.stdout.buffer.flush()


def rpc(op, args=None):
    emit({"op": op, "args": args or {}})
    line = sys.stdin.buffer.readline(1_048_578)
    if not line:
        raise HarnessError("BROKER_CLOSED")
    return strict_loads(line)


def order_fields(value):
    return {k: value[k] for k in ("order_id", "recipient", "product", "spec_sha256", "quantity", "deadline_tick")}


def execute(initial, method):
    contract = validate_contract(initial["view"]["contract"])
    if not contract["source_complete"]:
        return {"verdict": "NOT_ESTABLISHED", "reason": "SOURCE_INCOMPLETE", "outcomes": []}
    if not contract["permissions"]["activation"]:
        return {"verdict": "REFUSED", "reason": "PERMISSION_MISSING", "outcomes": []}
    if initial.get("restart"):
        reconciliation = rpc("reconcile")
        if not reconciliation.get("ok") or reconciliation.get("result", {}).get("status") != "RECONCILED":
            return {"verdict": "ERROR", "reason": "RECONCILIATION_INCOMPLETE", "outcomes": []}
    reconstructed = reconcile_events(contract["source_events"], contract["cutoff_sequence"])
    if method == "ablation":
        orders = sorted(initial["view"]["snapshot"], key=lambda x: (x["deadline_tick"], x["order_id"]))
        route = "primary"
    else:
        restoration = rpc("restore", {"events": contract["source_events"], "cutoff": contract["cutoff_sequence"]})
        if restoration.get("ok"):
            recovered = rpc("orders")
            if not recovered.get("ok"):
                return {"verdict": "ERROR", "reason": recovered.get("code", "ORDERS_UNAVAILABLE"), "outcomes": []}
            orders = sorted([order_fields(x) for x in recovered["result"]["orders"]], key=lambda x: (x["deadline_tick"], x["order_id"]))
            route = "primary"
            if method == "harness" and orders != reconstructed:
                return {"verdict": "REFUSED", "reason": "RECOVERY_RECONCILIATION_MISMATCH", "outcomes": []}
        else:
            if restoration.get("code") not in ("ROUTE_UNAVAILABLE", "ROUTE_NOT_AUTHORIZED"):
                return {"verdict": "REFUSED", "reason": restoration.get("code", "RESTORE_FAILED"), "outcomes": []}
            orders = reconstructed
            route = "backup"
    if route not in contract["allowed_routes"] or contract["dependencies"][route] in contract["blocked_dependencies"]:
        return {"verdict": "REFUSED", "reason": "DEPENDENCY_UNAVAILABLE", "outcomes": []}
    if route == "backup" and not contract["permissions"]["sharing"]:
        return {"verdict": "REFUSED", "reason": "PERMISSION_MISSING", "outcomes": []}
    requests = []
    for order in orders:
        key = digest({"contract_id": contract["contract_id"], "run_id": contract["run_id"], "order_id": order["order_id"]})
        requests.append({k: order[k] for k in ("order_id", "recipient", "product", "spec_sha256", "quantity")} | {"route": route, "key": key})
    # Each order uses lookup, commit, then fulfill. Commit must precede the
    # uncommitted lease expiry; later queue entries acquire their lease only
    # when their chunk is ready. Never renew or rewrite an existing key.
    batch_size = max(1, contract["lease_ticks"] // 3)
    outcomes = []
    for offset in range(0, len(requests), batch_size):
        batch = requests[offset:offset + batch_size]
        reservation_results = rpc("reserve_batch", {"requests": batch})
        if not reservation_results.get("ok"):
            return {"verdict": "REFUSED", "reason": reservation_results.get("code", "RESERVATION_FAILED"), "outcomes": outcomes}
        for request, result in zip(batch, reservation_results["result"]["results"]):
            if not result.get("ok"):
                outcomes.append({"order_id": request["order_id"], "state": "REFUSED", "code": result.get("code", "REFUSED")})
                continue
            key = request["key"]
            known = rpc("lookup", {"key": key})
            if known.get("ok") and known["result"].get("receipt"):
                outcomes.append({"order_id": request["order_id"], "state": "COMPLETED", "code": "DURABLE_RECEIPT_RECONCILED"})
                continue
            committed = rpc("commit", {"key": key})
            if not committed.get("ok"):
                outcomes.append({"order_id": request["order_id"], "state": "REFUSED", "code": committed.get("code", "COMMIT_FAILED")})
                continue
            fulfilled = rpc("fulfill", {"key": key})
            outcomes.append({"order_id": request["order_id"], "state": "COMPLETED" if fulfilled.get("ok") else "UNRESOLVED",
                             "code": "LOCAL_OUTPUT_COMPLETED" if fulfilled.get("ok") else fulfilled.get("code", "FULFILLMENT_UNCERTAIN")})
    return {"verdict": "COMPLETED" if outcomes and all(x["state"] == "COMPLETED" for x in outcomes) else "PARTIAL", "reason": "EXECUTED_LOCAL_PROCEDURE", "outcomes": outcomes}


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--method", choices=("conventional", "harness", "ablation"), required=True)
    parser.add_argument("--authority-probe", required=True)
    parser.add_argument("--workspace-probe", required=True)
    args = parser.parse_args()
    # Exercise hashing before syscall confinement to load any lazy crypto path.
    hashlib.sha256(b"warmup").hexdigest()
    try:
        isolation = activate(args.authority_probe, args.workspace_probe)
        emit({"event": "sandbox", "isolation": isolation})
        initial = strict_loads(sys.stdin.buffer.readline(1_048_578))
        result = execute(initial, args.method) if args.method == "ablation" else ADAPTERS[args.method].run(initial, rpc, execute)
        emit({"event": "done", "result": result})
        return 0
    except (HarnessError, OSError, KeyError, TypeError, ValueError) as error:
        emit({"event": "error", "code": getattr(error, "code", "CANDIDATE_ERROR"), "detail": str(error)[:500]})
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
