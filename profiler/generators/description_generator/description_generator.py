from typing import List, Optional, Tuple
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
    map_description,
)
from nl2flow.compile.options import SlotOptions


def get_sample_description(
    available_agents: List[AgentInfo],
    goal_agent_ids: List[str],
    mappings: List[Tuple[str, str, float]],
    available_data: List[Tuple[str, Optional[str]]],
    slot_option: Optional[SlotOptions] = None,
) -> str:
    descriptions: list[str] = list()
    # system
    if len(available_agents) > 0:
        descriptions.append(get_available_agents_description(available_agents))

    # actions
    for agent_info in available_agents:
        pre_cond, effect = get_agent_info_description(agent_info)
        parts: List[str] = [pre_cond]

        if len(effect) > 0:
            parts.append(effect)

        descriptions.append(" ".join(parts))
    # known values
    if len(available_data) > 0:
        descriptions.append(get_description_available_data(available_data))
    # field mappings
    if len(mappings) > 0:
        descriptions.append(map_description[:])
        descriptions.append(get_mappings_description(mappings))

    # slot-fillers
    descriptions.append(ask_description[:])

    # variable description
    if len(available_agents) > 0 or len(available_data) > 0:
        descriptions.append(get_variables_description(available_agents, available_data))

    # goals
    if len(goal_agent_ids) > 0:
        descriptions.append(get_goal_description(goal_agent_ids))

    return "\n".join(descriptions)
