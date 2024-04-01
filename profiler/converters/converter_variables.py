from typing import List, Literal, Union


AGENT_ID: Literal["agent_id"] = "agent_id"
ACTUATOR_SIGNATURE: Literal["actuator_signature"] = "actuator_signature"
IN_SIGNATURE: Literal["in_sig_full"] = "in_sig_full"
OUT_SIGNATURE: Literal["out_sig_full"] = "out_sig_full"
SIGNATURE_TYPES: List[Union[Literal["in_sig_full"], Literal["out_sig_full"]]] = [IN_SIGNATURE, OUT_SIGNATURE]
