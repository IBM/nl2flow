from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple, Union
from nl2flow.compile.options import BasicOperations
from profiler.data_types.agent_info_data_types import (
    SIGNATURE_TYPES,
    AgentInfo,
    AgentInfoSignatureItem,
    SimpleActionModel,
    SimplePlanningModel,
)
from profiler.generators.description_generator.descripter_generator_data import (
    ask_description,
    map_description,
    action_requirement,
    system_goal_description,
)


def get_names(names: List[str]) -> str:
    names_filtered = list(filter(lambda name: len(name) > 0, map(lambda name: name.strip(), names)))
    if len(names_filtered) == 0:
        return ""
    if len(names_filtered) == 1:
        return names_filtered[0]
    if len(names_filtered) == 2:
        return names_filtered[0] + " and " + names_filtered[1]

    return ", ".join(names_filtered[:-1]) + ", and " + names_filtered[-1]


def get_available_action_names(available_agents: List[Union[AgentInfo, SimpleActionModel]]) -> str:
    return get_names(
        sorted(
            list(
                map(
                    lambda agent_info: agent_info.agent_id if isinstance(agent_info, AgentInfo) else agent_info.id,
                    available_agents,
                )
            )
        )
    )


def get_available_agents_description(available_agents: List[Union[AgentInfo, SimpleActionModel]]) -> str:
    parts: List[str] = ["The system has"]
    parts.append("action" if len(available_agents) == 1 else "actions")
    parts.append(f"{get_available_action_names(available_agents)}.")
    return " ".join(parts)


def get_variable_type_str(variable_name: str, type_str: Optional[str]) -> str:
    if type_str is None or len(type_str) == 0:
        return ""
    return f"The type of variable {variable_name} is {type_str}."


def get_variable_name_from_sig_item(
    sig_items: List[AgentInfoSignatureItem],
) -> List[str]:
    return list(map(lambda sig_item: "variable " + sig_item.name, sig_items))


def get_variable_property_description(available_agents: List[AgentInfo]) -> str:
    property_action_names_dict: Dict[bool, Set[str]] = defaultdict(set)
    for agent_info in available_agents:
        sig = agent_info.actuator_signature
        for signature_type in SIGNATURE_TYPES:
            for sig_item in sig.get_signature(signature_type):
                slot_fillable = sig_item.slot_fillable if sig_item.slot_fillable is not None else False
                slot_fillable_category = True if slot_fillable else False
                signature_item_name = sig_item.name
                if len(signature_item_name) > 0:
                    property_action_names_dict[slot_fillable_category].add(signature_item_name)

    variable_description_str_lst: List[str] = []
    for slot_fillable, sig_item_names in property_action_names_dict.items():
        if len(sig_item_names) > 0:
            sentence_parts: List[str] = []
            variable = "Variable" if len(sig_item_names) == 1 else "Variables"
            sentence_parts.append(variable)
            variable_names = get_names(sorted(sig_item_names))
            sentence_parts.append(variable_names)
            slot_fillable_description = (
                "can be acquired by asking the user." if slot_fillable else "cannot be acquired by asking the user."
            )
            sentence_parts.append(slot_fillable_description)
            variable_description_str_lst.append(" ".join(sentence_parts))

    return "\n".join(variable_description_str_lst)


def get_vartiable_type_description(
    available_agents: List[AgentInfo], available_data: List[Tuple[str, Optional[str]]]
) -> str:
    variable_list: List[str] = list()
    variable_type_strs: List[str] = list()
    for known_data in available_data:
        variable_list.append("variable " + known_data[0])
        variable_type_str = get_variable_type_str(known_data[0], known_data[1] if known_data[1] is not None else "")
        if len(variable_type_str) > 0:
            variable_type_strs.append(variable_type_str)

    for agent_info in available_agents:
        sig = agent_info.actuator_signature
        variable_type_strs += get_variable_type_from_sig_item(sig.in_sig_full)
        variable_type_strs += get_variable_type_from_sig_item(sig.out_sig_full)

    return (" ".join(sorted(list(set(variable_type_strs))))).strip() if len(variable_type_strs) > 0 else ""


def get_variable_type_from_sig_item(
    sig_items: List[AgentInfoSignatureItem],
) -> List[str]:
    return list(
        filter(
            lambda unfiltered_str: len(unfiltered_str) > 0,
            map(
                lambda sig_item: get_variable_type_str(sig_item.name, sig_item.data_type),
                sig_items,
            ),
        )
    )


def get_variables_description(
    available_agents: List[AgentInfo],
    available_data: List[Tuple[str, Optional[str]]],
) -> str:
    variable_property_description = get_variable_property_description(available_agents=available_agents)
    variable_type_description = get_vartiable_type_description(
        available_agents=available_agents, available_data=available_data
    )

    return (
        variable_property_description
        if len(variable_type_description) == 0
        else (variable_property_description + "\n" + variable_type_description)
    )


def get_names_from_signature_items(
    sig_items: List[AgentInfoSignatureItem],
) -> List[str]:
    return list(
        map(lambda sig: "variable " + sig.name.strip(), filter(lambda item: len(item.name.strip()) > 0, sig_items))
    )


def get_action_variable_description(agent_info: AgentInfo) -> str:
    sig = agent_info.actuator_signature
    input_variable_names = get_names_from_signature_items_no_category(sig.in_sig_full)
    output_variable_names = get_names_from_signature_items_no_category(sig.out_sig_full)

    part_list: List[str] = [f"Action {agent_info.agent_id}"]

    if len(input_variable_names) > 0:
        part_list.append("has input parameter" if len(input_variable_names) == 1 else "has input parameters")
        part_list.append(get_names(list(set(input_variable_names))))

        if len(output_variable_names) == 0:
            return " ".join(part_list) + "."

    if len(output_variable_names) > 0:
        if len(input_variable_names) > 0:
            part_list.append("and it")

        part_list.append("outputs variable" if len(output_variable_names) == 1 else "outputs variables")
        part_list.append(get_names(list(set(output_variable_names))))

        return " ".join(part_list) + "."

    return ""


def get_action_condition_description(agent_info: AgentInfo, is_in_sig: bool) -> str:
    sig = agent_info.actuator_signature
    variable_names = get_names_from_signature_items_no_category(sig.in_sig_full if is_in_sig else sig.out_sig_full)

    if len(variable_names) == 0:
        return (
            f"Action {agent_info.agent_id} can be executed without knowing the value of any variable."
            if is_in_sig
            else ""
        )

    variable_names = list(set(variable_names))
    part_list: List[str] = []
    is_singular = len(variable_names) == 1
    prepend_word = "variable" if is_singular else "variables"
    if is_in_sig:
        part_list.append(f"To execute action {agent_info.agent_id},")
        part_list.append(prepend_word)
        part_list.append(get_names(variable_names))
        part_list.append("must be known.")
    else:
        part_list.append(f"After executing action {agent_info.agent_id},")
        part_list.append(prepend_word)
        part_list.append(get_names(variable_names))
        part_list.append("is" if is_singular else "are")
        part_list.append("known.")

    return " ".join(part_list)


def get_names_from_signature_items_no_category(
    sig_items: List[AgentInfoSignatureItem],
) -> List[str]:
    return list(map(lambda sig: sig.name.strip(), filter(lambda item: len(item.name.strip()) > 0, sig_items)))


def get_signature_item_names(sig_items: List[AgentInfoSignatureItem]) -> str:
    return get_names(get_names_from_signature_items(sig_items))


def get_agent_info_description(agent_info: AgentInfo) -> Tuple[str, str]:
    agent_info_pre_cond_str_list: List[str] = []

    # variables description
    action_variable_description = get_action_variable_description(agent_info=agent_info)
    if len(action_variable_description) > 0:
        agent_info_pre_cond_str_list.append(action_variable_description)

    agent_info_pre_cond_str_list.append(get_action_condition_description(agent_info=agent_info, is_in_sig=True))

    return (
        " ".join(agent_info_pre_cond_str_list),
        get_action_condition_description(agent_info=agent_info, is_in_sig=False),
    )


def get_mapping_description(mapping: Tuple[str, str, float]) -> str:
    return f"Action {BasicOperations.MAPPER.value} can determine the value of variable {mapping[0]} from variable {mapping[1]}."


def get_mappings_description(mappings: List[Tuple[str, str, float]]) -> str:
    return " ".join(list(map(lambda mapping: get_mapping_description(mapping), mappings)))


def get_goal_description(goals: List[str]) -> str:
    parts: List[str] = ["The goal of the system is to execute"]
    parts.append("action" if len(goals) == 1 else "actions")
    parts.append(f"{get_names(goals)}.")
    return " ".join(parts)


def get_description_available_data(available_items: List[Tuple[str, Optional[str]]]) -> str:
    item_list = list(set(map(lambda available_item: available_item[0], available_items)))

    if len(item_list) == 0:
        return ""

    parts: List[str] = []
    parts.append("Values are available already for")
    parts.append("variable" if len(item_list) == 1 else "variables")
    parts.append(f"{get_names(item_list)}.")

    return " ".join(parts)


def get_concise_action_description(simple_planning_model: SimplePlanningModel) -> str:
    description: List[str] = []
    description.append("actions:")

    for action in simple_planning_model.actions:
        action_description: List[str] = [f"name: {action.id}"]
        if len(action.input) > 0:
            signature_names = ", ".join(action.input)
            action_description.append("inputs:" + " " + signature_names)
        if len(action.output) > 0:
            signature_names = ", ".join(action.output)
            action_description.append("outputs:" + " " + signature_names)
        description.append("\n".join(action_description))

    return "\n\n".join(description)


def get_concise_mapping_description(simple_planning_model: SimplePlanningModel) -> str:
    mapping_list: List[str] = []
    for mapping in simple_planning_model.mappings:
        mapping_list.append(f"({mapping[0]}, {mapping[1]})")
    return "mappings: " + ", ".join(mapping_list)


def get_concise_available_data_description(simple_planning_model: SimplePlanningModel) -> str:
    return "available data: " + ", ".join(simple_planning_model.available_data)


def get_concise_askable_parameters_description(simple_planning_model: SimplePlanningModel) -> str:
    return "askable parameters: " + ", ".join(simple_planning_model.askable_parameters)


def get_concise_unaskable_parameters_description(simple_planning_model: SimplePlanningModel) -> str:
    return "unaskable parameters: " + ", ".join(simple_planning_model.unaskable_parameters)


def get_concise_goals_description(simple_planning_model: SimplePlanningModel) -> str:
    return "goals: " + ", ".join(simple_planning_model.goal_action_ids)


def get_concise_description(simple_planning_model: SimplePlanningModel) -> str:
    description: List[str] = []
    if len(simple_planning_model.actions) > 0:
        description.append(
            get_available_agents_description(available_agents=simple_planning_model.actions) + " " + action_requirement
        )
        description.append(get_concise_action_description(simple_planning_model=simple_planning_model))
    if len(simple_planning_model.mappings) > 0:
        description.append(map_description[:])
        description.append(get_concise_mapping_description(simple_planning_model=simple_planning_model))
    if len(simple_planning_model.available_data) > 0:
        description.append(get_concise_available_data_description(simple_planning_model=simple_planning_model))
    if len(simple_planning_model.askable_parameters) > 0:
        description.append(ask_description[:])
        description.append(get_concise_askable_parameters_description(simple_planning_model=simple_planning_model))
    # if len(simple_planning_model.unaskable_parameters) > 0:
    #     description.append(get_concise_unaskable_parameters_description(simple_planning_model=simple_planning_model))
    if len(simple_planning_model.goal_action_ids) > 0:
        description.append(system_goal_description)
        description.append(get_concise_goals_description(simple_planning_model=simple_planning_model))

    return "\n\n".join(description)
