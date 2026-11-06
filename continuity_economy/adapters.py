"""Explicit local-AI protocol; absent capability never becomes a performance run."""
from copy import deepcopy
from .schema import HarnessError, canonical, object_fields


class LocalAIAdapter:
    operations={"status","propose","decide","technical","restore","reserve","produce","transfer","inspect","settle","cancel"}

    def __init__(self,decider=None,capability_id=None):
        self.decider,self.capability_id=decider,capability_id

    def run(self,context,tools):
        if self.decider is None or not self.capability_id:
            return {"verdict":"NOT_RUN","reason":"LOCAL_AI_UNAVAILABLE"}
        history=[]
        for _ in range(context["contract"]["bounds"]["max_requests"]):
            action=self.decider(deepcopy(context),deepcopy(history));canonical(action)
            if type(action) is not dict: raise HarnessError("INVALID_AI_ACTION")
            if action.get("event")=="done":
                object_fields(action,{"event","result"});return action["result"]
            object_fields(action,{"op","args"})
            if type(action["op"]) is not str or action["op"] not in self.operations:
                raise HarnessError("BROKER_OPERATION_FORBIDDEN")
            if type(action["args"]) is not dict: raise HarnessError("INVALID_AI_ACTION")
            history.append({"request":action,"response":tools(action["op"],action["args"])})
        raise HarnessError("REQUEST_BUDGET_EXCEEDED")
