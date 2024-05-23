from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple
from profiler.data_types.agent_info_data_types import (
    SIGNATURE_TYPES,
    AgentInfo,
    AgentInfoSignatureItem,
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


def get_available_action_names(available_agents: List[AgentInfo]) -> str:
    return get_names(
        sorted(
            list(
                map(
                    lambda agent_info: agent_info.agent_id,
                    available_agents,
                )
            )
        )
    )


def get_available_agents_description(available_agents: List[AgentInfo]) -> str:
    parts: List[str] = ["The system has"]
    parts.append("action" if len(available_agents) == 1 else "actions")
    parts.append(f"{get_available_action_names(available_agents)}.")
    txt = " ".join(parts)
    return txt.capitalize()


def get_variable_type_str(variable_name: str, type_str: Optional[str]) -> str:
    if type_str is None or len(type_str) == 0:
        return ""
    txt = f"The type of variable {variable_name} is {type_str}."
    return txt.capitalize()


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
            variable = "variable" if len(sig_item_names) == 1 else "variables"
            sentence_parts.append(variable)
            variable_names = get_names(sorted(sig_item_names))
            sentence_parts.append(variable_names)
            slot_fillable_description = (
                "can be acquired by asking the user." if slot_fillable else "cannot be acquired by asking the user."
            )
            sentence_parts.append(slot_fillable_description)
            description = " ".join(sentence_parts)
            variable_description_str_lst.append(description.capitalize())

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
    txt = (" ".join(sorted(list(set(variable_type_strs))))).strip() if len(variable_type_strs) > 0 else ""

    return txt.capitalize()


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
    variable_names = get_names_from_signature_items_no_category(
        sig.in_sig_full
    ) + get_names_from_signature_items_no_category(sig.out_sig_full)

    if len(variable_names) > 0:
        part_list: List[str] = [f"action {agent_info.agent_id} has"]
        part_list.append("variable" if len(variable_names) == 1 else "variables")
        part_list.append(get_names(list(set(variable_names))))
        txt = " ".join(part_list) + "."
        return txt.capitalize()

    return ""


def get_action_condition_description(agent_info: AgentInfo, is_in_sig: bool) -> str:
    sig = agent_info.actuator_signature
    variable_names = get_names_from_signature_items_no_category(sig.in_sig_full if is_in_sig else sig.out_sig_full)

    if len(variable_names) == 0:
        txt = f"action {agent_info.agent_id} can be executed without knowing any variable" if is_in_sig else ""
        return txt.capitalize()

    variable_names = list(set(variable_names))
    part_list: List[str] = []
    if is_in_sig:
        part_list.append(f"To execute action {agent_info.agent_id},")
        part_list.append("variable" if len(variable_names) == 1 else "variables")
        part_list.append(get_names(variable_names))
        part_list.append("should be known.")
    else:
        part_list.append(f"After executing action {agent_info.agent_id},")
        part_list.append("variable" if len(variable_names) == 1 else "variables")
        part_list.append(get_names(variable_names))
        part_list.append("is" if variable_names == 1 else "are")
        part_list.append("known.")
    txt = " ".join(part_list)

    return txt.capitalize()


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
    txt = f"Action map can determine the value of variable {mapping[0]} from variable {mapping[1]}."
    return txt.capitalize()


def get_mappings_description(mappings: List[Tuple[str, str, float]]) -> str:
    return " ".join(list(map(lambda mapping: get_mapping_description(mapping), mappings)))


def get_goal_description(goals: List[str]) -> str:
    parts: List[str] = ["The goal of the system is to execute"]
    parts.append("action" if len(goals) == 1 else "actions")
    parts.append(f"{get_names(goals)}.")
    txt = " ".join(parts)
    return txt.capitalize()


def get_description_available_data(available_items: List[Tuple[str, Optional[str]]]) -> str:
    item_list = list(set(map(lambda available_item: available_item[0], available_items)))

    if len(item_list) == 0:
        return ""

    parts: List[str] = []
    parts.append("Values are available already for")
    parts.append("variable" if len(item_list) == 1 else "variables")
    parts.append(f"{get_names(item_list)}.")
    txt = " ".join(parts)

    return txt.capitalize()
