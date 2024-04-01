from enum import Enum
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


class AgentInfoSignatureType(str, Enum):
    IN_SIG_FULL = "IN_SIG_FULL"
    OUT_SIG_FULL = "OUT_SIG_FULL"


SIGNATURE_TYPES = [AgentInfoSignatureType.IN_SIG_FULL, AgentInfoSignatureType.OUT_SIG_FULL]


class AgentInfoSignature(BaseModel):
    in_sig_full: List[AgentInfoSignatureItem] = []
    out_sig_full: List[AgentInfoSignatureItem] = []

    def get_signature(self, type: AgentInfoSignatureType) -> List[AgentInfoSignatureItem]:
        if type == AgentInfoSignatureType.IN_SIG_FULL:
            return self.in_sig_full
        if type == AgentInfoSignatureType.OUT_SIG_FULL:
            return self.out_sig_full

    def set_signature(
        self, agent_info_signature_items: List[AgentInfoSignatureItem], type: AgentInfoSignatureType
    ) -> None:
        if type == AgentInfoSignatureType.IN_SIG_FULL:
            self.in_sig_full = agent_info_signature_items
        if type == AgentInfoSignatureType.OUT_SIG_FULL:
            self.out_sig_full = agent_info_signature_items


class AgentInfo(BaseModel):
    agent_id: str
    actuator_signature: AgentInfoSignature = AgentInfoSignature()


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
