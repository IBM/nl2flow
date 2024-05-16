from math import ceil
from typing import Dict, List, Optional, Set, Tuple
from profiler.data_types.agent_info_data_types import AgentInfo, SIGNATURE_TYPES, AgentInfoSignatureType
from profiler.data_types.generator_data_type import (
    AgentInfoGeneratorInput,
)


def get_stats_coupled_agents(
    agent_infos: List[AgentInfo],
) -> Tuple[int, Set[Tuple[str, str]]]:
    variable_agent_dict_ins: Dict[str, Set[str]] = dict()
    variable_agent_dict_outs: Dict[str, Set[str]] = dict()
    for agent_info in agent_infos:
        for signature_type in SIGNATURE_TYPES:
            for item in agent_info.actuator_signature.get_signature(signature_type):  # type: ignore
                if signature_type == AgentInfoSignatureType.IN_SIG_FULL:
                    if item.name not in variable_agent_dict_ins:
                        variable_agent_dict_ins[item.name] = set()
                    variable_agent_dict_ins[item.name].add(agent_info.agent_id)
                if signature_type == AgentInfoSignatureType.OUT_SIG_FULL:
                    if item.name not in variable_agent_dict_outs:
                        variable_agent_dict_outs[item.name] = set()
                    variable_agent_dict_outs[item.name].add(agent_info.agent_id)
    connections: Set[Tuple[str, str]] = set()
    # go through out signature
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
        for signature_type in SIGNATURE_TYPES:
            for item in agent_info.actuator_signature.get_signature(signature_type):
                if item.slot_fillable:
                    slot_fillable_var.add(item.name)

    return len(slot_fillable_var)


def get_num_variables(agent_infos: List[AgentInfo], available_data: List[Tuple[str, Optional[str]]]) -> int:
    vars: Set[str] = set()
    for agent_info in agent_infos:
        for signature_type in SIGNATURE_TYPES:
            for item in agent_info.actuator_signature.get_signature(signature_type):
                vars.add(item.name[:])
    for datum in available_data:
        vars.add(datum[0][:])  # add variable name

    return len(vars)


def get_num_variables_used_for_data_mapping(mappings: List[Tuple[(str, str, float)]]) -> int:
    vars: Set[str] = set()
    for mapping in mappings:
        vars.add(mapping[0])
        vars.add(mapping[1])

    return len(vars)


def check_num_input_parameters(agent_infos: List[AgentInfo], num_input_parameters: int) -> bool:
    for agent_info in agent_infos:
        for signature_type in SIGNATURE_TYPES:
            if num_input_parameters != len(agent_info.actuator_signature.get_signature(signature_type)):
                return False

    return True


def check_sample(
    input: AgentInfoGeneratorInput,
    available_agents: List[AgentInfo],
    available_data: List[Tuple[str, Optional[str]]],
    goal_agent_ids: List[str],
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
    expected_couple_agents = ceil(input.num_agents * input.proportion_coupled_agents)
    expected_couple_agents = 0 if expected_couple_agents == 1 else expected_couple_agents
    assert expected_couple_agents == num_coupled_agents
    # goals
    assert input.num_goal_agents == len(goal_agent_ids)
    # data mapper
    expected_prop_variables_mapping = ceil(input.num_var * input.proportion_mappable_variables)
    expected_prop_variables_mapping = 0 if expected_prop_variables_mapping == 1 else expected_prop_variables_mapping
    assert expected_prop_variables_mapping == get_num_variables_used_for_data_mapping(mappings)
    # slot-filler
    # variables assigned for available data can't be checked if they are slot-fillable
    assert ceil(input.num_var * input.proportion_slot_fillable_variables) >= get_num_slot_fillable_variables(
        available_agents
    )
