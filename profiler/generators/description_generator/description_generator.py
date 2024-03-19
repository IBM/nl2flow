from typing import List, Optional, Set, Tuple
from profiler.data_types.agent_info_data_types import AgentInfo
from profiler.generators.description_generator.description_generator_helper import (
    get_variables_description,
    get_goal_description,
    get_mappings_description,
    get_available_agents_description,
    get_description_available_data,
    get_agent_info_description,
)
from profiler.generators.description_generator.descripter_generator_data import (
    ask_description,
    ask_last_resort_description,
    map_description,
)
from nl2flow.compile.options import SlotOptions


def get_sample_description(
    available_agents: List[AgentInfo],
    goal_agent_ids: Set[str],
    mappings: List[Tuple[str, str, float]],
    available_data: List[Tuple[str, Optional[str]]],
    slot_option: Optional[SlotOptions] = None,
) -> str:
    descriptions: list[str] = list()
    # system
    descriptions.append(get_available_agents_description(available_agents))
    descriptions.append(get_variables_description(available_agents, available_data))
    # slot-fillers
    if slot_option is not None and slot_option == SlotOptions.last_resort:
        descriptions.append(ask_last_resort_description[:])
    descriptions.append(ask_description[:])
    # actions
    for agent_info in available_agents:
        pre_cond, effect = get_agent_info_description(agent_info)
        descriptions.append(pre_cond)
        descriptions.append(effect)
    # known values
    if len(available_data) > 0:
        descriptions.append(get_description_available_data(available_data))
    # field mappings
    descriptions.append(map_description[:])
    if len(mappings) > 0:
        descriptions.append(get_mappings_description(mappings))
    descriptions.append(get_goal_description(goal_agent_ids))

    return "\n".join(descriptions)
