from profiler.generators.info_generator.agent_info_data_types import (
    AgentInfoSignature,
    AgentInfoSignatureItem,
)

VARIABLE_PREFIX = "v__"
AGENT_ID_PREFIX = "a__"

AGENT_INFO_SIGNATURE_TEMPLATE: AgentInfoSignature = {
    "in_sig_full": [],
    "out_sig_full": [],
}

AGENT_INFO_SIGNATURE_ITEM_TEMPLATE: AgentInfoSignatureItem = {
    "name": "",
    "sequence_alias": "",
    "required": True,
    "slot_fillable": False,
    "mappable": False,
}
SIGNATURE_TYPES = ["in_sig_full", "out_sig_full"]
