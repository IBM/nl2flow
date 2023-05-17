from typing import List, Set, Tuple
from profiler.data_types.agent_info_data_types import AgentInfo
from profiler.generators.description_generator.description_generator_helper import (
    get_variables_description,
    get_goal_description,
    get_mappings_description,
    get_available_agents_description,
    get_description_available_data,
    get_agent_info_description,
    get_available_action_names,
)
from profiler.generators.description_generator.descripter_generator_data import (
    ask_description,
    ask_last_resort_description,
    ask_actions,
    ask_preference,
    map_description,
)


def get_sample_description(
    available_agents: List[AgentInfo],
    goal_agent_ids: Set[str],
    mappings: List[Tuple[str, str, float]],
    available_data: List[str],
) -> str:
    descriptions: list[str] = list()
    descriptions.append(get_available_agents_description(available_agents))
    descriptions.append(get_variables_description(available_agents, available_data))
    descriptions.append(ask_description[:])
    descriptions.append(ask_last_resort_description[:])
    descriptions.append(ask_preference)
    descriptions.append("\n")

    for agent_info in available_agents:
        pre_cond, in_description, effect = get_agent_info_description(agent_info)
        descriptions.append(pre_cond)
        descriptions.append(in_description)
        descriptions.append(effect)
        descriptions.append("\n")

    if len(available_data) > 0:
        descriptions.append(get_description_available_data(available_data))
        descriptions.append("\n")

    descriptions.append(map_description[:])

    if len(mappings) > 0:
        descriptions.append(get_mappings_description(mappings))
        descriptions.append("\n")

    descriptions.append(
        "The system obtains values from "
        + get_available_action_names(available_agents)
        + " rather than from "
        + ask_actions
    )

    descriptions.append("\n")

    descriptions.append(get_goal_description(goal_agent_ids))

    return "\n".join(descriptions)
