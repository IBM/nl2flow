from typing import List, Optional, TypedDict


class AgentInfoSignatureItem(TypedDict, total=False):
    name: str
    providence: Optional[str]
    required: Optional[bool]
    sequence_alias: Optional[str]
    data_type: Optional[str]
    ont: Optional[str]
    slot_fillable: Optional[bool]


class AgentInfoSignature(TypedDict, total=False):
    in_sig_full: List[AgentInfoSignatureItem]
    out_sig_full: List[AgentInfoSignatureItem]


class AgentInfo(TypedDict, total=False):
    agent_id: str
    real_agent_id: Optional[str]  # agent_id before normalizing
    agent_name: Optional[str]
    evaluator_signature: Optional[AgentInfoSignature]
    actuator_signature: Optional[AgentInfoSignature]


class PlanAction(TypedDict):
    action_name: str
    parameters: List[str]


class Plan(TypedDict):
    plan: List[PlanAction]
    metric: float


class PlannerErrorInfo(TypedDict):
    exception: Optional[Exception]
    message: str


class PlanInfo(TypedDict):
    plans: List[Plan]
    error_info: Optional[PlannerErrorInfo]
