from typing import List, Optional
from typing_extensions import TypedDict


class AgentInfoSignatureItem(TypedDict, total=False):
    name: str
    providence: Optional[str]
    required: Optional[bool]
    sequence_alias: Optional[str]
    data_type: Optional[str]
    ont: Optional[str]
    mappable: Optional[bool]
    slot_fillable: Optional[bool]


class AgentInfoSignature(TypedDict, total=False):
    in_sig_full: List[AgentInfoSignatureItem]
    out_sig_full: List[AgentInfoSignatureItem]


class AgentInfo(TypedDict, total=False):
    agent_id: str
    agent_name: str
    evaluator_signature: AgentInfoSignature
    actuator_signature: AgentInfoSignature


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
