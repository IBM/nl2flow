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
