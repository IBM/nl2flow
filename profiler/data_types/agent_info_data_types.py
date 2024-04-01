from typing import List, Optional
from typing_extensions import TypedDict

from pydantic import BaseModel


class AgentInfoSignatureItem(BaseModel):
    name: str = ""
    providence: Optional[str] = None
    required: Optional[bool] = False
    data_type: Optional[str] = None
    ont: Optional[str] = None
    mappable: Optional[bool] = False
    slot_fillable: Optional[bool] = False


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
