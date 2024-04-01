from typing import List, Optional, Set, Tuple
import random
from profiler.data_types.generator_data_type import VariableInfo
from profiler.data_types.agent_info_data_types import AgentInfo, AgentInfoSignatureType


def exist_variable_name_in_signature(
    agent_infos: List[AgentInfo],
    variable_info: Optional[VariableInfo],
    agent_index: int,
    signature_type: AgentInfoSignatureType,
) -> bool:
    if variable_info is None:
        return False
    sig_names = map(lambda item: item.name, agent_infos[agent_index].actuator_signature.get_signature(signature_type))
    return True if variable_info.variable_name in sig_names else False


def get_out_item_position_to_couple_agents(
    agent_index: int,
    num_input_parameters: int,
    position_item_coupled: Set[Tuple[int, AgentInfoSignatureType, int]],
    variable_info: VariableInfo,
    agent_infos: List[AgentInfo],
    signature_type: AgentInfoSignatureType,
) -> Tuple[Tuple[int, AgentInfoSignatureType, int], bool]:
    """
    return 1) the position of a "out" item to couple agents
    # and 2) and the status of choosing a "out_sig_full" item position
    already used for coupling"""
    agent_idx = -1
    item_idx = -1
    max_try = 20
    try_cnt = 0
    # randomly choose an agent
    while try_cnt < max_try:
        agent_idx = random.randint(0, agent_index)
        item_idx = random.randint(0, num_input_parameters - 1)
        # check if the chosen position is already used for coupling agents
        if (agent_idx, signature_type, item_idx) in position_item_coupled:
            return ((agent_idx, signature_type, item_idx), True)
        # check if the same variable appears in a signature multiple times
        if not exist_variable_name_in_signature(agent_infos, variable_info, agent_idx, signature_type):
            return ((agent_idx, signature_type, item_idx), False)
        try_cnt += 1

    return ((agent_index, signature_type, 0), False)
