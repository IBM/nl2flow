from collections import deque
from copy import deepcopy
from math import ceil
from types import ModuleType
from typing import Any, Deque, Dict, List, Optional, Set, Tuple
from profiler.data_types.agent_info_data_types import (
    AgentInfo,
    AgentInfoSignature,
    AgentInfoSignatureItem,
    SIGNATURE_TYPES,
    AgentInfoSignatureType,
)
from profiler.data_types.generator_data_type import (
    VariableInfo,
    NameGenerator,
)
from haikunator import Haikunator
from profiler.data.api_spec_data import agent_names, parameter_names
from profiler.generators.info_generator.agent_info_generator_coupling_helper import (
    get_out_item_position_to_couple_agents,
)
from profiler.generators.info_generator.generator_variables import variable_data_types


def get_names_dataset(num: int, name_type: str, random: Any) -> List[str]:
    num_names_dataset = len(agent_names) if name_type == "agent" else len(parameter_names)
    indices = [i for i in range(num_names_dataset)]
    names: Dict[str, int] = dict()
    name = ""
    for i in range(num):
        if i % num_names_dataset == 0:
            random.shuffle(indices)
        if name_type == "agent":
            name = agent_names[indices[i % num_names_dataset]]
        else:
            name = parameter_names[indices[i % num_names_dataset]]
        if name not in names:
            names[name] = 0
        names[name] += 1
    final_names: List[str] = list()
    for picked_name, count in names.items():
        for i in range(count):
            counter = "_" + str(i) if i > 0 else ""
            final_names.append(picked_name[:] + counter)
    random.shuffle(final_names)
    return final_names


def get_names_from_haikunator(num_names: int) -> List[str]:
    names: Set[str] = set()
    while len(names) < num_names:
        name = Haikunator.haikunate(0)
        if names not in names:
            names.add(name)
    return list(names)


def get_agent_variable_names_with_dataset(num_agents: int, num_var: int, random: Any) -> Tuple[List[str], List[str]]:
    return get_names_dataset(num_agents, "agent", random), get_names_dataset(num_var, "parameter", random)


def get_agent_variable_names_with_haikunator(num_agents: int, num_var: int) -> Tuple[List[str], List[str]]:
    names = list(get_names_from_haikunator(num_agents + num_var))
    return names[0:num_agents], names[num_agents:]


def get_agent_variable_names_with_number(num_agents: int, num_var: int) -> Tuple[List[str], List[str]]:
    return [f"a__{str(i)}" for i in range(num_agents)], [f"v__{str(i)}" for i in range(num_var)]


def get_agent_variable_names(
    name_generator: NameGenerator, num_agents: int, num_var: int, random: Any
) -> Tuple[List[str], List[str]]:
    if name_generator == NameGenerator.HAIKUNATOR:
        return get_agent_variable_names_with_haikunator(num_agents, num_var)
    if name_generator == NameGenerator.DATASET:
        return get_agent_variable_names_with_dataset(num_agents, num_var, random)
    return get_agent_variable_names_with_number(num_agents, num_var)


def get_agents(agent_names: List[str], num_input_parameters: int) -> List[AgentInfo]:
    num_agents = len(agent_names)
    agent_infos: List[AgentInfo] = list()
    for i in range(num_agents):
        agent_id = agent_names[i][:]
        agent_info = AgentInfo(
            agent_id=agent_id,
            actuator_signature=AgentInfoSignature(),
        )

        for i in range(num_input_parameters):
            agent_info.actuator_signature.in_sig_full.append(AgentInfoSignatureItem())
            agent_info.actuator_signature.out_sig_full.append(AgentInfoSignatureItem())

        agent_infos.append(agent_info)
    return agent_infos


def get_variable_types(num_variables: int, num_var_types: int, random: Any) -> List[Optional[str]]:
    """
    returns types for variables
    A None element indicates that no type should be assigned for a variable
    """
    sample_types: List[Optional[str]] = [None] * num_variables
    if num_var_types == 0:
        return sample_types
    types = random.sample(variable_data_types, num_var_types)
    types.append(None)
    for i in range(num_variables):
        if i < len(types) - 1:
            sample_types[i] = types[i][:]
        else:
            idx = random.randint(0, len(types) - 1)
            if idx == len(types) - 1:
                continue  # None is selected
            else:
                sample_types[i] = types[idx][:]
    random.shuffle(sample_types)
    return sample_types


def get_variables(
    variable_names: List[str],
    proportion_slot_fillable_variables: float,
    proportion_mappable_variables: float,
    num_var_types: int,
    random: Any,
) -> List[VariableInfo]:
    num_variables = len(variable_names)

    # mappable
    num_slot_fillable_variables = ceil(num_variables * proportion_slot_fillable_variables)
    slot_fillable_variable_names = set(random.sample(variable_names, num_slot_fillable_variables))

    # mappable
    num_mappable_variables = ceil(num_variables * proportion_mappable_variables)
    mappable_variable_names = set(random.sample(variable_names, num_mappable_variables))

    variable_types = get_variable_types(num_variables, num_var_types, random)
    variable_slot_fillable_state: List[VariableInfo] = list()
    for i, variable_name in enumerate(variable_names):
        slot_fillable = False
        mappable = False
        if variable_name in mappable_variable_names:
            mappable = True
        if variable_name in slot_fillable_variable_names:
            slot_fillable = True

        variable_slot_fillable_state.append(
            VariableInfo(
                variable_name=variable_name,
                slot_fillable=slot_fillable,
                mappable=mappable,
                variable_type=variable_types[i],
            )
        )
    return variable_slot_fillable_state


def get_goals(num_goals: int, agent_infos: List[AgentInfo], random: ModuleType) -> List[str]:
    return list(random.sample(list(map(lambda info: info.agent_id[:], agent_infos)), num_goals))


def get_mappings(variable_infos: List[VariableInfo], random: ModuleType) -> List[Tuple[str, str, float]]:
    mappable_variable_names = list(
        map(
            lambda filtered_info: filtered_info.variable_name,
            filter(lambda info: info.mappable, variable_infos),
        )
    )
    random.shuffle(mappable_variable_names)

    if len(mappable_variable_names) == 0:
        return []

    previous_variable_name = mappable_variable_names[0]
    mappings: List[Tuple[str, str, float]] = list()
    mapping_score = 1.0
    for i in range(1, len(mappable_variable_names)):
        # mapping_score = random.uniform(0, 1)
        mappings.append((previous_variable_name, mappable_variable_names[i], mapping_score))
        mappings.append((mappable_variable_names[i], previous_variable_name, mapping_score))
        previous_variable_name = mappable_variable_names[i]
    return mappings


def get_new_signature_from_variable_info(
    signature_item_input: AgentInfoSignatureItem, variable_info: VariableInfo
) -> AgentInfoSignatureItem:
    signature_item: AgentInfoSignatureItem = signature_item_input.model_copy(deep=True)
    signature_item.name = variable_info.variable_name[:]
    signature_item.slot_fillable = variable_info.slot_fillable
    signature_item.data_type = variable_info.variable_type

    return signature_item


def get_uncoupled_agents(agent_infos_input: List[AgentInfo], variable_infos: List[VariableInfo]) -> List[AgentInfo]:
    # returns agent_infos with uncoupled agents
    agent_infos = deepcopy(agent_infos_input)
    for agent_info in agent_infos:
        parameter_counter = 0
        for signature_type in SIGNATURE_TYPES:
            tmp_signature_items = agent_info.actuator_signature.get_signature(signature_type)
            tmp_signature_items_cpy = list(map(lambda tmp_item: tmp_item.model_copy(deep=True), tmp_signature_items))
            for item_idx, item in enumerate(tmp_signature_items):
                tmp_signature_items_cpy[item_idx] = get_new_signature_from_variable_info(
                    item, variable_infos[parameter_counter]
                )
                parameter_counter += 1
            agent_info.actuator_signature.set_signature(
                agent_info_signature_items=tmp_signature_items_cpy, type=signature_type
            )

    return agent_infos


def get_agent_infos_with_coupled_agents(
    agent_infos_input: List[AgentInfo],
    variable_infos: List[VariableInfo],
    proportion_coupled_agents: float,
    num_input_parameters: int,
) -> Tuple[List[AgentInfo], Set[Tuple[int, AgentInfoSignatureType, int]], Deque[VariableInfo]]:
    # returns a list of agent_infos and the positions of the items used for coupling agents
    agent_infos = deepcopy(agent_infos_input)
    num_used_variables = num_input_parameters * 2
    variables_remaining_deque = deque(variable_infos[num_used_variables:][:])
    num_coupled_agents = int(ceil(len(agent_infos) * proportion_coupled_agents))

    # postions of items used for coupling agents
    # Tuple[agent_index, "in" or "out", item_index]
    position_item_coupled: Set[Tuple[int, AgentInfoSignatureType, int]] = set()
    previous_variable: Optional[VariableInfo] = (
        deepcopy(variables_remaining_deque[0]) if len(variables_remaining_deque) > 0 else None
    )
    chosen_agent_index = -1
    chosen_item_index = -1
    loop_cnt = num_coupled_agents - 1

    if proportion_coupled_agents > 0.0:
        for agent_i in range(loop_cnt):
            # keep using an unused variables until there is no unused variable
            variable_info: Optional[VariableInfo] = (
                deepcopy(variables_remaining_deque[0]) if len(variables_remaining_deque) > 0 else previous_variable
            )

            is_variable_used_for_coupling = True

            if variable_info is not None:
                (
                    chosen_agent_index,
                    _,
                    chosen_item_index,
                ), is_variable_used_for_coupling = get_out_item_position_to_couple_agents(
                    agent_i,
                    num_input_parameters,
                    position_item_coupled,
                    variable_info,
                    agent_infos,
                    AgentInfoSignatureType.OUT_SIG_FULL,
                )

            previous_variable = variable_info

            # randomly choose agent & signature item indices

            if is_variable_used_for_coupling or previous_variable is None:
                # use a variable already used for coupling agents
                # use an initially assigned variable if there are only two agents
                chosen_item = agent_infos[chosen_agent_index].actuator_signature.out_sig_full[chosen_item_index]
                variable_info = VariableInfo(
                    variable_name=chosen_item.name[:],
                    mappable=chosen_item.mappable if chosen_item.mappable is not None else False,
                    slot_fillable=chosen_item.slot_fillable if chosen_item.slot_fillable is not None else True,
                    variable_type=chosen_item.data_type,
                )
                previous_variable = variable_info
            elif len(variables_remaining_deque) > 0:
                variables_remaining_deque.popleft()

            # couple agents
            # out

            if variable_info is not None:
                source = agent_infos[chosen_agent_index]
                source.actuator_signature.out_sig_full[chosen_item_index] = get_new_signature_from_variable_info(
                    source.actuator_signature.out_sig_full[chosen_item_index],
                    variable_info,
                )
                # add a position used for coupling agents
                position_item_coupled.add((chosen_agent_index, AgentInfoSignatureType.OUT_SIG_FULL, chosen_item_index))

                # in
                destination = agent_infos[agent_i + 1]
                destination.actuator_signature.in_sig_full[0] = get_new_signature_from_variable_info(
                    destination.actuator_signature.in_sig_full[0], variable_info
                )
                # add a position used for coupling agents
                position_item_coupled.add((agent_i + 1, AgentInfoSignatureType.IN_SIG_FULL, 0))

    return agent_infos, position_item_coupled, variables_remaining_deque


def get_agent_info_with_remaining_variables(
    agent_infos_input: List[AgentInfo],
    position_item_coupled: Set[Tuple[int, AgentInfoSignatureType, int]],
    variables_remaining_deque_input: Deque[VariableInfo],
) -> Tuple[List[AgentInfo], Deque[VariableInfo]]:
    agent_infos = deepcopy(agent_infos_input)
    variables_remaining_deque = deepcopy(variables_remaining_deque_input)
    out_sig_full_signature_names_first_agent = set(
        map(
            lambda item: item.name,
            agent_infos[0].actuator_signature.out_sig_full,
        )
    )
    # assign remaining variables to agents
    # use as many variables as possible for agents
    for agent_i, agent_info in enumerate(agent_infos):
        if agent_i == 0:
            # The first agent should keep all initially assigned
            continue
        for signature_type in SIGNATURE_TYPES:
            tmp_signature_items = agent_info.actuator_signature.get_signature(signature_type)
            tmp_signature_items_cpy = list(map(lambda tmp_item: tmp_item.model_copy(deep=True), tmp_signature_items))
            for item_i, item in enumerate(tmp_signature_items):
                if len(variables_remaining_deque) == 0:
                    # no more remaining variables
                    break
                if ((agent_i, signature_type, item_i) in position_item_coupled) or (
                    (agent_i == len(agent_infos) - 1)
                    and (signature_type == AgentInfoSignatureType.OUT_SIG_FULL)
                    and (item.name not in out_sig_full_signature_names_first_agent)
                ):
                    # skip to avoid breaking couplings among agents
                    continue
                # assign a remaining variable to a signature
                tmp_signature_items_cpy[item_i] = get_new_signature_from_variable_info(
                    item, variables_remaining_deque.popleft()
                )
            agent_info.actuator_signature.set_signature(
                agent_info_signature_items=tmp_signature_items_cpy, type=signature_type
            )

    return agent_infos, variables_remaining_deque


def get_shuffled_agent_infos(agent_infos_input: List[AgentInfo], random: Any) -> List[AgentInfo]:
    agent_infos = deepcopy(agent_infos_input)
    random.shuffle(agent_infos)
    for agent_info in agent_infos:
        for signature_type in SIGNATURE_TYPES:
            if signature_type == AgentInfoSignatureType.IN_SIG_FULL:
                random.shuffle(agent_info.actuator_signature.in_sig_full)
            if signature_type == AgentInfoSignatureType.OUT_SIG_FULL:
                random.shuffle(agent_info.actuator_signature.out_sig_full)

    return agent_infos


def get_agents_with_variables(
    agent_infos_input: List[AgentInfo],
    variable_infos_input: List[VariableInfo],
    proportion_coupled_agents: float,
    random: Any,
) -> Tuple[List[AgentInfo], List[Tuple[str, Optional[str]]]]:
    # returns agent_infos and available_data
    agent_infos = deepcopy(agent_infos_input)
    variable_infos = deepcopy(variable_infos_input)
    available_data: List[Tuple[str, Optional[str]]] = list()
    num_input_parameters = len(agent_infos[0].actuator_signature.in_sig_full)

    slot_fillable_variable_infos = list(filter(lambda var: var.slot_fillable, variable_infos))
    none_slot_fillable_variable_infos = list(filter(lambda var: not var.slot_fillable, variable_infos))
    # assign slot_fillable variables to agents first
    # to reduce the number of slot_fillable variables assigned to "available_data"
    variable_infos = slot_fillable_variable_infos + none_slot_fillable_variable_infos

    # set non-coupled agents with the minimum number of variables
    agent_infos = get_uncoupled_agents(agent_infos, variable_infos)

    # coupling agents
    (
        agent_infos,
        position_item_coupled,
        variables_remaining_deque,
    ) = get_agent_infos_with_coupled_agents(
        agent_infos, variable_infos, proportion_coupled_agents, num_input_parameters
    )

    # assign the remaining variables to agents
    agent_infos, variables_remaining_deque = get_agent_info_with_remaining_variables(
        agent_infos, position_item_coupled, variables_remaining_deque
    )

    # check if any slot-fillable variables remains
    if len(variables_remaining_deque) > 0 and variables_remaining_deque[0].slot_fillable:
        # slot-fillable variable should not be used for available_data
        return [], available_data

    # use remaining variables for available_data
    available_data = list(
        map(
            lambda var: (var.variable_name, var.variable_type),
            variables_remaining_deque,
        )
    )

    # shuffle data
    agent_infos = get_shuffled_agent_infos(agent_infos, random)

    return agent_infos, available_data
