"""Neutral, strict structural schemas for authored SMU policies and proposals.

These functions validate bounded wire shapes and scalar types. They make no
participant acceptance, profitability, funding or fulfillment decision. The
producer, policy service and independent verifier may share these schemas.
"""
from continuity_harness.schema import (HarnessError, canonical, identifier,
    integer, object_fields, sha256)

POLICY_SCHEMA = "continuity-economy/policies/v1"
PROPOSAL_SCHEMA = "continuity-economy/proposal/v1"
MAX_MONEY = 1_000_000_000
MAX_TICK = 1_000_000_000
MAX_ITEMS = 4_096
SINK = "COST_SINK"
OUTSIDE = "OUTSIDE_ACCOUNT"


def fail(code, detail=""):
    raise HarnessError(code, detail)


def money(value, path):
    return integer(value, path, 0, MAX_MONEY)


def tick_value(value, path="tick"):
    return integer(value, path, 0, MAX_TICK)


def _list(value, path, maximum=MAX_ITEMS):
    if type(value) is not list or len(value) > maximum:
        fail("INVALID_TYPE", path)
    return value


def _bool(value, path):
    if type(value) is not bool:
        fail("INVALID_TYPE", path)
    return value


def validate_policies(value):
    """Strict complete policy schema. Boolean money is never an integer here."""
    object_fields(value, {"schema", "revision", "currency", "buyer", "providers", "coordinator", "technical_sponsor"}, path="policies")
    if value["schema"] != POLICY_SCHEMA or value["currency"] != "SMU":
        fail("UNSUPPORTED_VERSION", "policies")
    integer(value["revision"], "policies.revision", 1, MAX_ITEMS)
    buyer = value["buyer"]
    object_fields(buyer, {"party_id", "value_min_minor", "value_max_minor", "outside_utility_minor", "max_price_minor", "balance_minor", "consent_until_tick"}, path="buyer")
    identifier(buyer["party_id"], "buyer.party_id")
    for key in ("value_min_minor", "value_max_minor", "outside_utility_minor", "max_price_minor", "balance_minor"):
        money(buyer[key], "buyer." + key)
    tick_value(buyer["consent_until_tick"], "buyer.consent_until_tick")
    if buyer["value_min_minor"] > buyer["value_max_minor"]:
        fail("INVALID_POLICY", "buyer.value_interval")
    providers = _list(value["providers"], "providers", 64)
    if not providers:
        fail("INVALID_POLICY", "providers")
    for p in providers:
        object_fields(p, {"party_id", "setup_cost_minor", "unit_cost_minor", "rework_setup_cost_minor", "rework_unit_cost_minor", "min_profit_minor", "outside_profit_minor", "balance_minor", "liability_limit_minor", "consent_until_tick", "technical_control_allowed"}, path="provider")
        identifier(p["party_id"], "provider.party_id")
        for key in ("setup_cost_minor", "unit_cost_minor", "rework_setup_cost_minor", "rework_unit_cost_minor", "min_profit_minor", "outside_profit_minor", "balance_minor", "liability_limit_minor"):
            money(p[key], "provider." + key)
        tick_value(p["consent_until_tick"], "provider.consent_until_tick")
        _bool(p["technical_control_allowed"], "provider.technical_control_allowed")
    c = value["coordinator"]
    object_fields(c, {"party_id", "operating_cost_minor", "min_profit_minor", "outside_profit_minor", "balance_minor", "liability_limit_minor", "consent_until_tick", "technical_control_allowed"}, path="coordinator")
    identifier(c["party_id"], "coordinator.party_id")
    for key in ("operating_cost_minor", "min_profit_minor", "outside_profit_minor", "balance_minor", "liability_limit_minor"):
        money(c[key], "coordinator." + key)
    tick_value(c["consent_until_tick"], "coordinator.consent_until_tick")
    _bool(c["technical_control_allowed"], "coordinator.technical_control_allowed")
    s = value["technical_sponsor"]
    object_fields(s, {"party_id", "balance_minor", "authorized"}, path="technical_sponsor")
    identifier(s["party_id"], "technical_sponsor.party_id")
    money(s["balance_minor"], "technical_sponsor.balance_minor")
    _bool(s["authorized"], "technical_sponsor.authorized")
    ids = [buyer["party_id"], c["party_id"], s["party_id"], *[p["party_id"] for p in providers]]
    if len(ids) != len(set(ids)) or {SINK, OUTSIDE} & set(ids):
        fail("INVALID_POLICY", "participant identities")
    canonical(value)
    return value



def validate_proposal_shape(value):
    object_fields(value, {"schema", "proposal_id", "contract_sha256", "policy_revision", "allocations", "buyer_price_minor", "coordinator_fee_minor", "rework_budget_minor", "cancellation_fee_minor", "expires_tick"}, path="proposal")
    if value["schema"] != PROPOSAL_SCHEMA:
        fail("UNSUPPORTED_VERSION", "proposal")
    identifier(value["proposal_id"], "proposal_id")
    # Derived technical agreement, production, delivery and authorization IDs
    # must also fit the common 128-character wire bound before any escrow.
    if len(value["proposal_id"]) > 74:
        fail("INVALID_RANGE", "proposal_id.max74")
    sha256(value["contract_sha256"], "contract_sha256")
    integer(value["policy_revision"], "policy_revision", 1, MAX_ITEMS)
    for key in ("buyer_price_minor", "coordinator_fee_minor", "rework_budget_minor", "cancellation_fee_minor"):
        money(value[key], key)
    integer(value["expires_tick"], "expires_tick", 1, MAX_TICK)
    for a in _list(value["allocations"], "allocations"):
        object_fields(a, {"lot_id", "provider_id", "window_id", "obligation_id", "first_unit", "last_unit", "pay_minor"}, path="allocation")
        for key in ("lot_id", "provider_id", "window_id", "obligation_id"):
            identifier(a[key], "allocation." + key)
        integer(a["first_unit"], "allocation.first_unit", 1, 1_000_000)
        integer(a["last_unit"], "allocation.last_unit", 1, 1_000_000)
        money(a["pay_minor"], "allocation.pay_minor")
    canonical(value)
    return value
