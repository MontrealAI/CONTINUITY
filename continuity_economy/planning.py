"""Two competent finite planners with the same public input and action domain.

Conventional: exhaustive assignment enumeration, ordinary feasibility checks.
Harness: depth-first branch and bound, identical feasibility and price function.
Neither planner controls participant consent or the recipient's acceptance.
"""
from copy import deepcopy
from itertools import product
from .schema import digest, lots, validate_contract, validate_policies, HarnessError, integer


def signature(allocations):
    return tuple((a["lot_id"], a["provider_id"], a["window_id"]) for a in allocations)


def minimum_terms(contract, policies, allocations, coordinator_sunk=0):
    """Public tariff calculation. Decisions are made in the retained service."""
    grouped = {}
    for a in allocations:
        grouped[a["provider_id"]] = grouped.get(a["provider_id"], 0) + a["last_unit"]-a["first_unit"]+1
    pp = {p["party_id"]:p for p in policies["providers"]}
    rows, rework = {}, 0
    for pid, units in grouped.items():
        p = pp[pid]
        base = p["setup_cost_minor"] + units*p["unit_cost_minor"]
        repair = p["rework_setup_cost_minor"] + units*p["rework_unit_cost_minor"] if contract["max_attempts"] == 2 else 0
        rows[pid] = base+repair+max(p["min_profit_minor"], p["outside_profit_minor"])
        rework += repair
    cp = policies["coordinator"]
    fee = cp["operating_cost_minor"]+max(cp["min_profit_minor"],cp["outside_profit_minor"])+coordinator_sunk
    result = deepcopy(allocations)
    # Payments are credited once per selected provider, on its first lot. All
    # other lots carry a zero installment; the complete terms remain explicit.
    seen = set()
    for a in result:
        a["pay_minor"] = rows[a["provider_id"]] if a["provider_id"] not in seen else 0
        seen.add(a["provider_id"])
    return {"allocations":result,"buyer_price_minor":sum(rows.values())+fee,
            "coordinator_fee_minor":fee,"rework_budget_minor":rework,"cancellation_fee_minor":0}


def _available_funds(state, policies):
    """Use current unencumbered funds whenever a live catalog is supplied.

    Pure fixture planning may start from the explicitly authored balances. A
    live catalog must contain every participant; missing current evidence never
    licenses falling back to a larger historical starting balance.
    """
    parties = [policies["buyer"], *policies["providers"], policies["coordinator"], policies["technical_sponsor"]]
    accounts = state.get("catalog", {}).get("participant_accounting", [])
    current = bool(state.get("catalog", {}).get("schema")) or any("free_minor" in a for a in accounts)
    if not current:
        return {p["party_id"]: p["balance_minor"] for p in parties}, "AUTHORED_STARTING_BALANCES"
    values = {}
    for account in accounts:
        pid = account.get("party_id")
        if pid in values or "free_minor" not in account:
            raise HarnessError("FUNDING_INFORMATION_INVALID", str(pid))
        values[pid] = integer(account["free_minor"], "free_minor", 0)
    if any(p["party_id"] not in values for p in parties):
        raise HarnessError("FUNDING_INFORMATION_MISSING")
    return values, "CURRENT_UNENCUMBERED_BALANCES"


def _service_funding_allows(contract, policies, allocations, funds):
    """Public supplier/coordinator feasibility, independently decided later.

    Buyer value, price and funding are deliberately left to a retained proposal
    and the separate buyer decision. This preserves negative/uncertain demand
    controls and never turns a planner screen into participant acceptance.
    """
    quantities = {}
    for allocation in allocations:
        pid = allocation["provider_id"]
        quantities[pid] = quantities.get(pid, 0) + allocation["last_unit"]-allocation["first_unit"]+1
    selected = [p for p in policies["providers"] if p["party_id"] in quantities]
    costs = {}
    for provider in selected:
        units = quantities[provider["party_id"]]
        base = provider["setup_cost_minor"] + units*provider["unit_cost_minor"]
        correction = provider["rework_setup_cost_minor"] + units*provider["rework_unit_cost_minor"] if contract["max_attempts"] == 2 else 0
        costs[provider["party_id"]] = base + correction
    coordinator = policies["coordinator"]
    operating = coordinator["operating_cost_minor"]
    trade = (operating <= coordinator["liability_limit_minor"] and operating <= funds[coordinator["party_id"]]
             and all(costs[p["party_id"]] <= min(p["liability_limit_minor"], funds[p["party_id"]]) for p in selected))
    if trade:
        return True
    sponsor = policies["technical_sponsor"]
    return (contract["mode"] == "technical_control" and sponsor["authorized"]
            and coordinator["technical_control_allowed"] and all(p["technical_control_allowed"] for p in selected)
            and sum(costs.values())+operating <= funds[sponsor["party_id"]])


def choose_plan(state, method="conventional", excluded=()):
    c, policies = state["contract"], state["policies"]
    validate_contract(c); validate_policies(policies)
    work = lots(c)
    tick = state.get("tick", 0)
    blocked = set(state.get("blocked_dependencies", c["blocked_dependencies"]))
    pp = {p["party_id"]:p for p in policies["providers"]}
    funds, funding_basis = _available_funds(state, policies)
    options = []
    for p in c["providers"]:
        permissions=state.get("effective_permissions",{}).get(p["provider_id"],p["permissions"])
        if p["dependency"] in blocked or not permissions["production"]: continue
        if p["role"] != "primary" and not permissions["disclosure"]: continue
        if tick >= pp[p["provider_id"]]["consent_until_tick"]: continue
        if any(r["party_id"] == p["provider_id"] and r["tick"] <= tick and r["action"] in ("produce","transfer","consent") for r in c["revocations"]): continue
        for w in p["windows"]:
            if w["end"] > tick and w["start"] < c["deadline_tick"]:
                capacity=state.get("effective_capacities",{}).get(p["provider_id"]+"."+w["window_id"],w["capacity"])
                options.append((p["provider_id"],w["window_id"],w["start"],w["end"],capacity))
    options.sort(key=lambda x:(x[0],x[1]))
    theoretical = len(options)**len(work)
    stats = {"method":method,"assignment_domain":theoretical,"complete_assignments_observed":0,
             "partial_nodes_observed":0,"capacity_prunes":0,"price_prunes":0,"feasible_assignments":0,
             "participant_prunes":0,"funding_basis":funding_basis,
             "exhaustive_within_declared_domain":True}
    if theoretical > c["bounds"]["max_plans"]:
        stats["exhaustive_within_declared_domain"] = False
        return {"plan":None,"reason":"SEARCH_LIMIT","search":stats}
    coordinator = policies["coordinator"]["party_id"]
    accounts = state.get("catalog",{}).get("participant_accounting",[])
    sunk = next((a["unreimbursed_cancelled_cost_minor"] for a in accounts if a["party_id"]==coordinator),0)
    banned = set(excluded)
    best, best_key = None, None

    def allocation(lot, option):
        return {**lot,"provider_id":option[0],"window_id":option[1],"pay_minor":0}

    def consider(rows):
        nonlocal best,best_key
        if signature(rows) in banned: return
        if not _service_funding_allows(c, policies, rows, funds):
            stats["participant_prunes"] += 1
            return
        stats["feasible_assignments"] += 1
        terms = minimum_terms(c,policies,rows,sunk)
        key = (terms["buyer_price_minor"],signature(rows))
        if best_key is None or key < best_key:
            best,best_key = terms,key

    if method == "conventional":
        for assignment in product(options,repeat=len(work)):
            stats["complete_assignments_observed"] += 1
            usage, rows, feasible = {}, [], True
            for lot,opt in zip(work,assignment):
                k = opt[:2]; usage[k] = usage.get(k,0)+lot["last_unit"]-lot["first_unit"]+1
                deadline = next(o["deadline_tick"] for o in c["obligations"] if o["obligation_id"]==lot["obligation_id"])
                if usage[k] > opt[4] or opt[2] >= deadline:
                    feasible = False; stats["capacity_prunes"] += 1; break
                rows.append(allocation(lot,opt))
            if feasible: consider(rows)
    elif method == "harness":
        # A partial assignment's tariff (nonnegative setup, unit and participation
        # costs) is a valid lower bound. Strict > preserves deterministic ties.
        def visit(index, rows, usage):
            stats["partial_nodes_observed"] += 1
            if index == len(work):
                stats["complete_assignments_observed"] += 1; consider(rows); return
            if best_key is not None and rows and minimum_terms(c,policies,rows,sunk)["buyer_price_minor"] > best_key[0]:
                stats["price_prunes"] += 1; return
            lot = work[index]
            deadline = next(o["deadline_tick"] for o in c["obligations"] if o["obligation_id"]==lot["obligation_id"])
            for opt in options:
                k = opt[:2]; amount = lot["last_unit"]-lot["first_unit"]+1
                if usage.get(k,0)+amount > opt[4] or opt[2] >= deadline:
                    stats["capacity_prunes"] += 1; continue
                prior = usage.get(k,0); usage[k] = prior+amount
                visit(index+1,rows+[allocation(lot,opt)],usage)
                usage[k] = prior
        visit(0,[],{})
    else:
        raise HarnessError("UNKNOWN_METHOD",method)
    reason = "PROPOSAL_AVAILABLE" if best else "NO_FUNDED_SERVICE_ARRANGEMENT" if stats["participant_prunes"] else "NO_CAPACITY_ARRANGEMENT"
    return {"plan":best,"reason":reason,"search":stats}


def make_proposal(state, terms, ordinal):
    c,p = state["contract"],state["policies"]
    return {"schema":"continuity-economy/proposal/v1","proposal_id":f"proposal-{ordinal:03d}",
            "contract_sha256":digest(c),"policy_revision":p["revision"],**terms,
            "expires_tick":c["deadline_tick"]}
