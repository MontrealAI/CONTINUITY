"""Strict contracts for the separately registered digital-product experiment.

JSON framing, integer units and path checks reuse the qualified v0.1 module.
This module is admission/schema code, not the recipient or fresh-verifier oracle.
"""
from copy import deepcopy
from continuity_harness.schema import (HarnessError, canonical, digest, strict_load,
    strict_loads, read_bytes, object_fields, integer, identifier, boolean, sha256, MAX_JSON_BYTES)
from .policy_schema import validate_policies

CONTRACT = "continuity-economy/contract/v1"
PRODUCT = "continuity-economy/label-job/v1"
REFERENCE = "continuity-economy/reference/v1"
# The supported envelope has fewer than 25 fields, bounded ASCII identifiers
# (at most 128 bytes each), a digest, bounded integers and the labels array.
# This intentionally conservative allowance also covers the correction binding.
PRODUCT_ENVELOPE_BYTES = 4096
FAULTS = {
    "BACKUP_FAIL_BEFORE_RESERVE", "PRODUCTION_CRASH_HALF_WRITE", "REJECT_FIRST_CONTENT",
    "ACK_LOST_AFTER_ACCEPTANCE", "CANDIDATE_RESTART_AFTER_ACCEPTANCE",
    "POLICY_CHANGE_AFTER_PROPOSE", "FUNDING_WITHDRAWAL_AFTER_PROPOSE",
    "CAPACITY_COMPETITION", "LATE_ACCEPTANCE", "PERMISSION_REVOKE_BEFORE_TRANSFER",
    "CONSENT_REVOKE_BEFORE_PRODUCTION", "SHARED_DEPENDENCY_FAILURE",
}


def require(condition, code, detail=""):
    if not condition:
        raise HarnessError(code, detail)


def text_value(value, path, maximum=200):
    require(type(value) is str and 0 < len(value) <= maximum and not any(ord(c) < 32 for c in value),
            "INVALID_TEXT", path)
    return value


def bounded_list(value, path, maximum=64):
    require(type(value) is list and len(value) <= maximum, "INVALID_TYPE", path)
    return value


def validate_obligation(o):
    object_fields(o, {"obligation_id", "recipient", "revision", "quantity", "deadline_tick", "status", "spec"})
    identifier(o["obligation_id"], "obligation_id"); identifier(o["recipient"], "recipient")
    require(len(o["obligation_id"]) <= 24 and len(o["recipient"]) <= 64, "INVALID_RANGE", "obligation identifier length")
    integer(o["revision"], "revision", 1, 1000); integer(o["quantity"], "quantity", 1, 2000)
    integer(o["deadline_tick"], "deadline_tick", 1, 10000)
    require(o["status"] in ("ACTIVE", "CANCELLED"), "INVALID_STATUS")
    s = object_fields(o["spec"], {"format", "sku", "name_en", "name_fr", "instructions_en", "instructions_fr", "lot", "serial_prefix"})
    require(s["format"] == PRODUCT, "UNSUPPORTED_VERSION", "product.format")
    for k in ("sku", "lot", "serial_prefix"):
        identifier(s[k], "spec." + k)
        require(len(s[k]) <= 48, "INVALID_RANGE", "spec." + k)
    for k in ("name_en", "name_fr", "instructions_en", "instructions_fr"):
        text_value(s[k], "spec." + k, 160)
    return o


def product_byte_bound(contract, obligation):
    """A structural admission bound, not a producer or acceptance oracle.

    Canonical escaped byte lengths matter: one valid Unicode character can
    occupy twelve ASCII bytes. The largest ordinal and serial bound every label
    in this obligation; the fixed envelope allowance bounds remaining metadata.
    No output is generated, accepted or counted by this calculation.
    """
    quantity = min(contract["lot_size"], obligation["quantity"]) if contract["allow_split"] else obligation["quantity"]
    spec = obligation["spec"]
    maximal_label = {"ordinal": obligation["quantity"],
        "serial": spec["serial_prefix"] + f'{obligation["quantity"]:06d}',
        **{key: spec[key] for key in ("sku", "name_en", "name_fr", "instructions_en", "instructions_fr", "lot")}}
    return PRODUCT_ENVELOPE_BYTES + quantity * (len(canonical(maximal_label)) + 1)


def replay_source(events, cutoff):
    bounded_list(events, "source_events", 64)
    require(type(cutoff) is int and cutoff == len(events), "INCOMPLETE_SOURCE")
    state = {}
    for seq, e in enumerate(events, 1):
        require(type(e) is dict, "INVALID_EVENT")
        kind = e.get("type")
        object_fields(e, {"sequence", "type", "obligation_id"} | ({"obligation"} if kind in ("ACCEPT", "AMEND") else set()))
        require(e["sequence"] == seq and type(e["sequence"]) is int, "INVALID_EVENT", "sequence")
        oid = identifier(e["obligation_id"], "event.obligation_id")
        if kind == "ACCEPT":
            require(oid not in state, "INVALID_EVENT", "duplicate acceptance")
        elif kind in ("AMEND", "CANCEL"):
            require(oid in state and state[oid]["status"] == "ACTIVE", "INVALID_EVENT", "inactive obligation")
        else:
            raise HarnessError("INVALID_EVENT", "unsupported kind")
        if kind == "CANCEL":
            state[oid]["status"] = "CANCELLED"
        else:
            item = deepcopy(validate_obligation(e["obligation"]))
            require(item["obligation_id"] == oid and item["status"] == "ACTIVE", "INVALID_EVENT", "binding")
            if kind == "AMEND":
                require(item["revision"] > state[oid]["revision"], "INVALID_EVENT", "revision")
            state[oid] = item
    return [state[k] for k in sorted(state)]


def validate_contract(c):
    canonical(c)
    object_fields(c, {"schema", "experiment_id", "fixture_id", "cohort", "run_id", "contract_id", "revision",
        "start_ns", "deadline_tick", "observation_cutoff_tick", "wall_deadline_ms", "lease_ticks", "seed",
        "authority_kind", "source_id", "source_complete", "source_sha256", "cutoff_sequence", "source_events",
        "obligations", "permissible_recovery_loss_units", "allow_split", "lot_size", "max_attempts", "providers",
        "blocked_dependencies", "revocations", "fault_schedule", "mode", "disclosure_fields", "permitted_actions", "bounds"})
    require(c["schema"] == CONTRACT, "UNSUPPORTED_VERSION", "contract")
    for key in ("experiment_id", "fixture_id", "run_id", "contract_id", "source_id"):
        identifier(c[key], key)
    require(c["cohort"] in ("base", "successor", "challenge"), "INVALID_COHORT")
    require(c["authority_kind"] == "SYNTHETIC_EXERCISE", "UNSUPPORTED_AUTHORITY")
    require(c["mode"] in ("market", "technical_control"), "UNSUPPORTED_MODE")
    integer(c["revision"], "revision", 1, 1000); integer(c["start_ns"], "start_ns", 0, 2**63-1)
    integer(c["deadline_tick"], "deadline_tick", 1, 10000)
    integer(c["observation_cutoff_tick"], "observation_cutoff_tick", c["deadline_tick"], 20000)
    integer(c["wall_deadline_ms"], "wall_deadline_ms", 1, 120000)
    integer(c["lease_ticks"], "lease_ticks", 1, 1000); integer(c["seed"], "seed", 0, 2**31-1)
    boolean(c["source_complete"], "source_complete"); boolean(c["allow_split"], "allow_split")
    integer(c["lot_size"], "lot_size", 1, 2000); integer(c["max_attempts"], "max_attempts", 1, 2)
    require(type(c["permissible_recovery_loss_units"]) is int and c["permissible_recovery_loss_units"] == 0,
            "UNSUPPORTED_RECOVERY_LOSS")
    sha256(c["source_sha256"], "source_sha256")
    require(digest(c["source_events"]) == c["source_sha256"], "SOURCE_DIGEST_MISMATCH")
    expected = replay_source(c["source_events"], c["cutoff_sequence"])
    bounded_list(c["obligations"], "obligations", 8)
    for o in c["obligations"]:
        validate_obligation(o)
        require(o["deadline_tick"] <= c["deadline_tick"], "INVALID_DEADLINE")
    require(c["obligations"] == expected, "SOURCE_OBLIGATION_MISMATCH")
    require(any(o["status"] == "ACTIVE" for o in expected), "NO_ACTIVE_OBLIGATION")
    require(len(lots(c)) <= 8, "TOO_MANY_LOTS")
    for o in c["obligations"]:
        if o["status"] == "ACTIVE":
            require(product_byte_bound(c, o) <= MAX_JSON_BYTES, "PRODUCT_SIZE_LIMIT", o["obligation_id"])
    ids = set()
    for p in bounded_list(c["providers"], "providers", 5):
        object_fields(p, {"provider_id", "role", "dependency", "permissions", "windows"})
        pid = identifier(p["provider_id"], "provider_id")
        require(len(pid) <= 24 and pid not in ids, "DUPLICATE_PROVIDER"); ids.add(pid)
        identifier(p["dependency"], "dependency")
        require(p["role"] in ("primary", "backup", "alternative"), "INVALID_ROUTE")
        permissions = object_fields(p["permissions"], {"production", "disclosure"})
        for k, v in permissions.items(): boolean(v, k)
        windows = bounded_list(p["windows"], "windows", 3)
        require(bool(windows), "INVALID_WINDOW")
        wins = set()
        for w in windows:
            object_fields(w, {"window_id", "start", "end", "capacity"})
            wid = identifier(w["window_id"], "window_id")
            require(len(wid) <= 24 and wid not in wins, "DUPLICATE_WINDOW"); wins.add(wid)
            integer(w["start"], "start", 0, 10000); integer(w["end"], "end", w["start"]+1, 20000)
            integer(w["capacity"], "capacity", 0, 20000)
        ordered = sorted(windows, key=lambda x: x["start"])
        require(all(a["end"] <= b["start"] for a,b in zip(ordered, ordered[1:])), "OVERLAPPING_PROVIDER_WINDOWS")
    require(bool(ids), "NO_PROVIDER")
    for d in bounded_list(c["blocked_dependencies"], "blocked_dependencies", 8): identifier(d, "dependency")
    for e in bounded_list(c["revocations"], "revocations", 16):
        object_fields(e, {"tick", "party_id", "action"})
        integer(e["tick"], "revocation.tick", 0, 20000); identifier(e["party_id"], "party_id")
        require(e["action"] in ("produce", "transfer", "accept", "consent"), "INVALID_ACTION")
    seen = set()
    for f in bounded_list(c["fault_schedule"], "fault_schedule", 16):
        object_fields(f, {"event", "trigger", "occurrence", "target", "value"})
        require(type(f["event"]) is str and f["event"] in FAULTS and f["event"] not in seen, "UNREGISTERED_FAULT"); seen.add(f["event"])
        require(f["trigger"] in ("initialize", "propose", "decide", "reserve", "produce", "transfer", "inspect"), "INVALID_TRIGGER")
        integer(f["occurrence"], "occurrence", 1, 16); identifier(f["target"], "target")
        integer(f["value"], "fault.value", 0, 100000000)
    require(c["disclosure_fields"] == ["recipient", "sku", "name_en", "name_fr", "instructions_en", "instructions_fr", "lot", "serial_prefix"], "UNSUPPORTED_DISCLOSURE")
    require(c["permitted_actions"] == ["restore", "propose", "decide", "technical", "reserve", "produce", "transfer", "inspect", "settle", "cancel", "status"], "UNSUPPORTED_ACTIONS")
    b = object_fields(c["bounds"], {"max_requests", "max_plans", "max_proposals", "service_timeout_ms"})
    integer(b["max_requests"], "max_requests", 1, 1024); integer(b["max_plans"], "max_plans", 1, 65536)
    integer(b["max_proposals"], "max_proposals", 1, 16); integer(b["service_timeout_ms"], "service_timeout_ms", 1, 30000)
    return c


def lots(c):
    result = []
    for o in c["obligations"]:
        if o["status"] != "ACTIVE": continue
        size = c["lot_size"] if c["allow_split"] else o["quantity"]
        for n, first in enumerate(range(1, o["quantity"]+1, size), 1):
            result.append({"lot_id": f'{o["obligation_id"]}.L{n:03d}', "obligation_id": o["obligation_id"],
                           "first_unit": first, "last_unit": min(first+size-1,o["quantity"])})
    return result


def capacity_order(c, lot, attempt):
    o = next(o for o in c["obligations"] if o["obligation_id"] == lot["obligation_id"])
    material = {"obligation_id":o["obligation_id"],"revision":o["revision"],"recipient":o["recipient"],
                "spec":o["spec"],"first_unit":lot["first_unit"],"last_unit":lot["last_unit"],"attempt":attempt}
    return {"order_id": f'{lot["lot_id"]}.A{attempt}', "recipient":o["recipient"],"product":"DIGITAL_LABEL_JOB",
            "spec_sha256":digest(material),"quantity":lot["last_unit"]-lot["first_unit"]+1,"deadline_tick":o["deadline_tick"]}


def candidate_view(contract, policies):
    # Identical permitted material for every candidate; no reference pin, seal,
    # acceptance database, expected answer, or completed base deliverable.
    return {"contract":deepcopy(contract),"policies":deepcopy(policies),"lots":lots(contract)}
