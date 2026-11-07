"""Pipe-only candidate procedures; all effects require the trusted broker."""
import argparse
import hashlib
import sys
import time
from .planning import choose_plan, make_proposal, signature
from .schema import HarnessError, canonical, strict_loads
from continuity_harness.sandbox import activate


def emit(value):
    sys.stdout.buffer.write(canonical(value)+b"\n");sys.stdout.buffer.flush()


COUNTER = 0
def rpc(op,args):
    global COUNTER
    COUNTER += 1; rid=f"tool-{COUNTER}"
    emit({"event":"tool","id":rid,"op":op,"args":args})
    response = strict_loads(sys.stdin.buffer.readline(1_048_578))
    if type(response) is not dict or response.get("id") != rid:
        raise HarnessError("RPC_ID_MISMATCH")
    return response


def value(response):
    if not response.get("ok"):
        raise HarnessError(response.get("code","BROKER_REFUSED"))
    return response["result"]


def execute(initial,method,tool=rpc,telemetry=lambda _:None):
    searches, interventions = [], []
    if method == "outside":
        return {"verdict":"OUTSIDE_OPTION","reason":"VOLUNTARY_NO_PURCHASE","searches":[],"interventions":[]}
    excluded_by_revision = {}
    for iteration in range(initial["view"]["contract"]["bounds"]["max_proposals"]+1):
        state = value(tool("status",{})); catalog=state["catalog"]
        active = next((a for a in catalog["agreements"] if a["status"] in ("ACTIVE","SETTLED")),None)
        if active and active["status"] == "SETTLED":
            return {"verdict":"COMPLETED","reason":"RECIPIENT_ACCEPTANCE_RECONCILED","searches":searches,"interventions":interventions}
        if active:
            proposal = next(p["payload"] for p in catalog["proposals"] if p["proposal_id"]==active["proposal_id"])
            agreement_id=active["agreement_id"]
        else:
            count = len(catalog["proposals"])
            if count >= state["contract"]["bounds"]["max_proposals"]:
                return {"verdict":"NOT_ESTABLISHED","reason":"PROPOSAL_BUDGET_EXHAUSTED","searches":searches,"interventions":interventions}
            revision=state["policies"]["revision"]
            planning_start=time.monotonic_ns()
            chosen=choose_plan(state,method,excluded_by_revision.get(revision,()))
            chosen["search"]["candidate_elapsed_ns"]=time.monotonic_ns()-planning_start
            telemetry({"event":"telemetry","kind":"planning","report":chosen["search"]})
            searches.append(chosen["search"])
            if chosen["plan"] is None:
                return {"verdict":"NO_DEAL" if chosen["reason"]!="SEARCH_LIMIT" else "NOT_ESTABLISHED",
                        "reason":chosen["reason"],"searches":searches,"interventions":interventions}
            proposal=make_proposal(state,chosen["plan"],count+1)
            submitted=tool("propose",{"proposal":proposal})
            if not submitted.get("ok"):
                return {"verdict":"NOT_ESTABLISHED","reason":submitted.get("code","PROPOSAL_REFUSED"),"searches":searches,"interventions":interventions}
            decided=value(tool("decide",{"proposal_id":proposal["proposal_id"]}))
            active=decided.get("agreement")
            status=decided["proposal"]["status"]
            if active is None and state["contract"]["mode"] == "technical_control" and status=="REJECTED":
                grant=tool("technical",{"proposal_id":proposal["proposal_id"]})
                if grant.get("ok"):
                    active=grant["result"].get("agreement",grant["result"])
            if not active:
                codes={d["code"] for d in decided.get("decisions",[]) if d["verdict"]!="ACCEPTED"}
                if status=="NOT_ESTABLISHED" or "UNCERTAIN_BUYER_VALUE" in codes:
                    return {"verdict":"NOT_ESTABLISHED","reason":"UNCERTAIN_BUYER_VALUE","searches":searches,"interventions":interventions}
                # The chosen tariff is the least expensive admissible assignment.
                # An unchanged buyer value or exhausted funds rejects every
                # more costly option; a policy revision still requires replan.
                if "BUYER_OUTSIDE_OPTION" in codes and "POLICY_REVISION_MISMATCH" not in codes:
                    return {"verdict":"NO_DEAL","reason":"BUYER_OUTSIDE_OPTION","searches":searches,"interventions":interventions}
                if "POLICY_REVISION_MISMATCH" not in codes and any(
                    d.get("role")=="buyer" and d.get("code")=="INSUFFICIENT_FUNDS"
                    for d in decided.get("decisions",[])):
                    return {"verdict":"NO_DEAL","reason":"INSUFFICIENT_FUNDS","searches":searches,"interventions":interventions}
                excluded_by_revision.setdefault(revision,[]).append(signature(proposal["allocations"]))
                continue
            agreement_id=active["agreement_id"]

        completed=0; failure=None
        order = sorted(proposal["allocations"],key=lambda a:(next(w["start"] for p in state["contract"]["providers"] if p["provider_id"]==a["provider_id"] for w in p["windows"] if w["window_id"]==a["window_id"]),a["lot_id"]))
        restored=set()
        for allocation in order:
            state=value(tool("status",{}))
            p=next(p for p in state["contract"]["providers"] if p["provider_id"]==allocation["provider_id"])
            slot=(p["provider_id"],allocation["window_id"])
            if p["role"]=="primary" and slot not in restored:
                r=tool("restore",{"provider_id":slot[0],"window_id":slot[1]})
                if not r.get("ok"): failure=r.get("code","RECOVERY_FAILED");break
                restored.add(slot)
            supersedes=None; accepted=False
            for attempt in range(1,state["contract"]["max_attempts"]+1):
                pid=f'{agreement_id}.{allocation["lot_id"]}.A{attempt}'; did=pid+".D"
                known=next((d for d in state["receiver"]["deliveries"] if d["delivery_id"]==did),None)
                if known and known["status"]=="ACCEPTED" and known.get("timely") is True:
                    accepted=True;break
                if known and known["status"]=="REJECTED":
                    supersedes=did;continue
                args={"agreement_id":agreement_id,"lot_id":allocation["lot_id"],"attempt":attempt}
                r=tool("reserve",args)
                if not r.get("ok"):failure=r.get("code","RESERVATION_FAILED");break
                r=tool("produce",{**args,"supersedes":supersedes})
                if not r.get("ok"):failure=r.get("code","PRODUCTION_UNRESOLVED");break
                r=tool("transfer",{"production_id":pid})
                if not r.get("ok"):failure=r.get("code","TRANSFER_UNRESOLVED");break
                r=tool("inspect",{"delivery_id":did})
                if not r.get("ok") and r.get("code") in ("ACK_UNKNOWN","PROCESS_EXITED"):
                    # Retry the same durable acceptance request, never produce
                    # a second product merely because acknowledgment was lost.
                    interventions.append({"type":"AUTOMATIC_IDEMPOTENT_RETRY","delivery_id":did})
                    r=tool("inspect",{"delivery_id":did})
                if not r.get("ok"):failure=r.get("code","ACCEPTANCE_UNRESOLVED");break
                observation=r["result"]
                if observation.get("status")=="ACCEPTED" and observation.get("timely") is True:
                    accepted=True;break
                if observation.get("status")=="REJECTED":
                    supersedes=did
                    interventions.append({"type":"AUTOMATIC_CORRECTION","delivery_id":did})
                    continue
                failure="ACCEPTANCE_NOT_ESTABLISHED";break
            if not accepted:
                failure=failure or "CORRECTION_BUDGET_EXHAUSTED";break
            completed += 1
        if failure:
            if completed:
                interventions.append({"type":"PARTIAL_AGREEMENT_RETAINED","agreement_id":agreement_id,
                                      "reason":failure,"accepted_lots":completed})
                return {"verdict":"PARTIAL","reason":failure,"searches":searches,"interventions":interventions}
            cancellation=tool("cancel",{"agreement_id":agreement_id,"reason":failure})
            interventions.append({"type":"CANCELLED_ATTEMPT","agreement_id":agreement_id,"reason":failure,"cancelled":cancellation.get("ok") is True})
            if not cancellation.get("ok"):
                return {"verdict":"NOT_ESTABLISHED","reason":cancellation.get("code","CANCELLATION_UNRESOLVED"),
                        "searches":searches,"interventions":interventions}
            # A known unavailable route may be replaced. Every rejected deal,
            # cost and capacity transition survives in the same run's evidence.
            excluded_by_revision.setdefault(state["policies"]["revision"],[]).append(signature(proposal["allocations"]))
            continue
        settled=tool("settle",{"agreement_id":agreement_id})
        return {"verdict":"COMPLETED" if settled.get("ok") else "NOT_ESTABLISHED",
                "reason":"DIGITAL_PRODUCT_ACCEPTED" if settled.get("ok") else settled.get("code","SETTLEMENT_UNRESOLVED"),
                "searches":searches,"interventions":interventions}
    return {"verdict":"NOT_ESTABLISHED","reason":"PROPOSAL_BUDGET_EXHAUSTED","searches":searches,"interventions":interventions}


def main():
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument("--method",choices=("conventional","harness","outside"),required=True)
    parser.add_argument("--authority-probe",required=True);parser.add_argument("--workspace-probe",required=True)
    args=parser.parse_args()
    hashlib.sha256(b"warmup").hexdigest()
    try:
        isolation=activate(args.authority_probe,args.workspace_probe)
        emit({"event":"sandbox","isolation":isolation})
        initial=strict_loads(sys.stdin.buffer.readline(1_048_578))
        emit({"event":"done","result":execute(initial,args.method,telemetry=emit)})
        return 0
    except (HarnessError,OSError,KeyError,TypeError,ValueError) as error:
        emit({"event":"error","code":getattr(error,"code","CANDIDATE_ERROR"),"detail":str(error)[:300]})
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
