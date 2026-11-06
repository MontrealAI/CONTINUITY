"""Load registered inputs; no fixture answer is available to candidate code."""
from copy import deepcopy
from pathlib import Path
import hashlib
from .schema import strict_load, validate_contract, validate_policies, HarnessError

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/economy-v0.2"


def fixture_names():
    return [f["id"] for f in strict_load(EXPERIMENT / "spec.json")["fixtures"]]


def load_fixture(name):
    spec = strict_load(EXPERIMENT / "spec.json")
    entry = next((f for f in spec["fixtures"] if f["id"] == name), None)
    if entry is None:
        raise HarnessError("UNKNOWN_FIXTURE", name)
    path = EXPERIMENT / entry["file"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
        raise HarnessError("REGISTERED_FIXTURE_CHANGED", name)
    value = strict_load(path)
    validate_contract(value["contract"]); validate_policies(value["policies"])
    return deepcopy(value)
