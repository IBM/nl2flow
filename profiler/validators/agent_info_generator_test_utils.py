from math import ceil
from typing import Dict, List, Set, Tuple
from profiler.generators.info_generator.agent_info_data_types import AgentInfo
from profiler.generators.info_generator.generator_data_type import (
    AgentInfoGeneratorInput,
)
from profiler.generators.info_generator.generator_variables import SIGNATURE_TYPES


def get_stats_coupled_agents(
    agent_infos: List[AgentInfo],
) -> Tuple[int, Set[Tuple[str, str]]]:
    variable_agent_dict_ins: Dict[str, Set[str]] = dict()
    variable_agent_dict_outs: Dict[str, Set[str]] = dict()
    for agent_info in agent_infos:
        for signature in SIGNATURE_TYPES:
            for item in agent_info["actuator_signature"][signature]:
                if signature == "in_sig_full":
                    if item["name"] not in variable_agent_dict_ins:
                        variable_agent_dict_ins[item["name"]] = set()
                    variable_agent_dict_ins[item["name"]].add(agent_info["agent_id"])
                if signature == "out_sig_full":
                    if item["name"] not in variable_agent_dict_outs:
                        variable_agent_dict_outs[item["name"]] = set()
                    variable_agent_dict_outs[item["name"]].add(agent_info["agent_id"])
    connections: Set[Tuple[str, str]] = set()
    # go throught out signature
    for var in variable_agent_dict_outs:
        if var in variable_agent_dict_ins:
            # connections
            for agent_name_0 in variable_agent_dict_outs[var]:
                for agent_name_1 in variable_agent_dict_ins[var]:
                    if agent_name_1 < agent_name_0:
                        connections.add((agent_name_1, agent_name_0))
                    else:
                        connections.add((agent_name_0, agent_name_1))

    connected_agents: Set[str] = set()
    for connection in connections:
        connected_agents.add(connection[0])
        connected_agents.add(connection[1])

    return len(connected_agents), connections


def get_num_slot_fillable_variables(agent_infos: List[AgentInfo]) -> int:
    slot_fillable_var: Set[str] = set()
    for agent_info in agent_infos:
        for signature in SIGNATURE_TYPES:
            for item in agent_info["actuator_signature"][signature]:
                if item["slot_fillable"]:
                    slot_fillable_var.add(item["name"])

    return len(slot_fillable_var)


def get_num_variables(agent_infos: List[AgentInfo], available_data: List[str]) -> int:
    vars: Set[str] = set()
    for agent_info in agent_infos:
        for signature in SIGNATURE_TYPES:
            for item in agent_info["actuator_signature"][signature]:
                vars.add(item["name"][:])
    for datum in available_data:
        vars.add(datum[:])

    return len(vars)


def get_num_variables_used_for_data_mapping(
    mappings: List[Tuple[(str, str, float)]]
) -> int:
    vars: Set[str] = set()
    for mapping in mappings:
        vars.add(mapping[0])
        vars.add(mapping[1])

    return len(vars)


def check_num_input_parameters(
    agent_infos: List[AgentInfo], num_input_parameters: int
) -> bool:
    for agent_info in agent_infos:
        for signature in SIGNATURE_TYPES:
            if num_input_parameters != len(agent_info["actuator_signature"][signature]):
                return False
    return True


def check_sample(
    input: AgentInfoGeneratorInput,
    available_agents: List[AgentInfo],
    available_data: List[str],
    goal_agent_ids: Set[str],
    mappings: List[Tuple[str, str, float]],
) -> None:
    # agents
    assert input.num_agents == len(available_agents)
    # variables
    assert input.num_var == get_num_variables(available_agents, available_data)
    # input parameters
    assert check_num_input_parameters(available_agents, input.num_input_parameters)
    # coupling
    num_coupled_agents, combs = get_stats_coupled_agents(available_agents)
    assert (
        ceil(input.num_agents * input.proportion_coupled_agents) == num_coupled_agents
    )
    # goals
    assert input.num_goal_agents == len(goal_agent_ids)
    # data mapper
    assert ceil(
        input.num_var * input.proportion_mappable_variables
    ) == get_num_variables_used_for_data_mapping(mappings)
    # slot-filler
    assert ceil(
        input.num_var * input.proportion_slot_fillable_variables
    ) == get_num_slot_fillable_variables(available_agents)
