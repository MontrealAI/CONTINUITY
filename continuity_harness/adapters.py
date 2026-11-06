"""Common adapter contract and an explicit optional local-AI tool protocol.

No provider SDK, key, model download, recorded-model result or network dependency
is included. A configured local model capability must implement decide(context,
history) and is a separately authorized trusted integration, not a Python plugin
silently imported into the sandbox. Unit stubs qualify protocol plumbing only.
"""

from abc import ABC, abstractmethod
from copy import deepcopy

from .schema import HarnessError, canonical, object_fields


class CandidateAdapter(ABC):
    name = "abstract"

    @abstractmethod
    def run(self, context, tools, procedure=None):
        """Return a target report; the independent verifier decides acceptance."""


class ConventionalAdapter(CandidateAdapter):
    name = "conventional"

    def run(self, context, tools, procedure=None):
        if procedure is None:
            raise HarnessError("PROCEDURE_UNAVAILABLE")
        return procedure(context, self.name)


class HarnessAdapter(ConventionalAdapter):
    name = "harness"


class LocalAIAdapter(CandidateAdapter):
    """Model-selected tool calls through the same bounded tool contract.

    A decider is intentionally explicit. Merely installing this adapter never
    implies a model was available or measured. No local decider is shipped.
    """
    name = "ai"
    operations = {"restore", "orders", "reserve_batch", "lookup", "commit", "fulfill", "release", "reconcile"}

    def __init__(self, decider=None, *, capability_id=None):
        self.decider = decider
        self.capability_id = capability_id

    def run(self, context, tools, procedure=None):
        if self.decider is None or not self.capability_id:
            return {"verdict": "NOT_RUN", "reason": "LOCAL_AI_UNAVAILABLE", "outcomes": []}
        history = []
        for _ in range(128):
            proposal = self.decider(deepcopy(context), deepcopy(history))
            canonical(proposal)
            if type(proposal) is not dict:
                raise HarnessError("INVALID_AI_ACTION")
            if proposal.get("event") == "done":
                object_fields(proposal, {"event", "result"}, path="ai.done")
                object_fields(proposal["result"], {"verdict", "reason", "outcomes"}, path="ai.result")
                return proposal["result"]
            object_fields(proposal, {"op", "args"}, path="ai.action")
            if proposal["op"] not in self.operations:
                raise HarnessError("BROKER_OPERATION_FORBIDDEN", str(proposal["op"]))
            result = tools(proposal["op"], proposal["args"])
            history.append({"action": proposal, "result": result})
        raise HarnessError("REQUEST_BUDGET_EXCEEDED", "ai")


ADAPTERS = {"conventional": ConventionalAdapter(), "harness": HarnessAdapter(), "ai": LocalAIAdapter()}
