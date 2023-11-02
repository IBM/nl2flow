from profiler.data_types.agent_info_data_types import (
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
    "data_type": None,
}
SIGNATURE_TYPES = ["in_sig_full", "out_sig_full"]
variable_data_types = [
    "boolean",
    "int32",
    "int64",
    "double",
    "float",
    "date",
    "datetime",
    "password",
    "byte",
    "binary",
    "uuid",
    "uri",
    "hostname",
    "ipv4",
    "ipv6",
]
