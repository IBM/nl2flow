from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple
from profiler.data_types.agent_info_data_types import (
    AgentInfo,
    AgentInfoSignature,
    AgentInfoSignatureItem,
)


def get_names(names: List[str]) -> str:
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return names[0] + " and " + names[1]

    return ", ".join(names[:-1]) + ", and " + names[-1]


def get_available_action_names(available_agents: List[AgentInfo]) -> str:
    return get_names(
        sorted(
            list(
                map(
                    lambda agent_info: "Action " + agent_info.get("agent_id", ""),
                    available_agents,
                )
            )
        )
    )


def get_available_agents_description(available_agents: List[AgentInfo]) -> str:
    return "The system has " + get_available_action_names(available_agents) + "."


def get_variable_type_str(variable_name: str, type_str: Optional[str]) -> str:
    if type_str is None or len(type_str) == 0:
        return ""
    return f"The type of Variable {variable_name} is {type_str}."


def get_variable_name_from_sig_item(
    sig_items: List[AgentInfoSignatureItem],
) -> List[str]:
    return list(map(lambda sig_item: "Variable " + sig_item.get("name", ""), sig_items))


def get_variable_property_description(available_agents: List[AgentInfo]) -> str:
    property_action_names_dict: Dict[bool, Set[str]] = defaultdict(set)
    for agent_info in available_agents:
        sig = agent_info.get("actuator_signature", None)
        if sig is not None:
            for signature_type in ["in_sig_full", "out_sig_full"]:
                for sig_item in sig.get(signature_type, []):
                    slot_fillable = sig_item.get("slot_fillable", True)
                    slot_fillable_category = True if slot_fillable else False
                    signature_item_name = sig_item.get("name", "")
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
            description = " ".join(sentence_parts)
            variable_description_str_lst.append(description)

    return "\n".join(variable_description_str_lst)


def get_vartiable_type_description(
    available_agents: List[AgentInfo], available_data: List[Tuple[str, Optional[str]]]
) -> str:
    variable_list: List[str] = list()
    variable_type_strs: List[str] = list()
    for known_data in available_data:
        variable_list.append("Variable " + known_data[0])
        variable_type_str = get_variable_type_str(known_data[0], known_data[1] if known_data[1] is not None else "")
        if len(variable_type_str) > 0:
            variable_type_strs.append(variable_type_str)

    for agent_info in available_agents:
        sig = agent_info.get("actuator_signature")
        variable_type_strs += get_variable_type_from_sig_item(sig.get("in_sig_full", []) if sig is not None else [])
        variable_type_strs += get_variable_type_from_sig_item(sig.get("out_sig_full", []) if sig is not None else [])

    return (" ".join(sorted(list(set(variable_type_strs))))).strip() if len(variable_type_strs) > 0 else ""


def get_variable_type_from_sig_item(
    sig_items: List[AgentInfoSignatureItem],
) -> List[str]:
    return list(
        filter(
            lambda unfiltered_str: len(unfiltered_str) > 0,
            map(
                lambda sig_item: get_variable_type_str(sig_item.get("name", ""), sig_item.get("data_type")),
                sig_items,
            ),
        )
    )


def get_variable_description_str() -> str:
    return ""


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
    return list(map(lambda sig: "Variable " + sig.get("name", ""), sig_items))


def get_signature_item_names(sig_items: List[AgentInfoSignatureItem]) -> str:
    return get_names(get_names_from_signature_items(sig_items))


def get_agent_info_description(agent_info: AgentInfo) -> Tuple[str, str]:
    agent_id = agent_info.get("agent_id")
    sig = agent_info.get("actuator_signature", AgentInfoSignature(in_sig_full=[], out_sig_full=[]))
    # in sig
    in_sig = sig.get("in_sig_full", [])
    agent_info_pre_cond_str = f"To execute Action {agent_id}, " + get_signature_item_names(in_sig) + " should be known."
    # out sig
    out_sig = sig.get("out_sig_full", [])
    be_out = " is " if len(out_sig) == 1 else " are "
    agent_info_effect_str = (
        f"After executing Action {agent_id}, " + get_signature_item_names(out_sig) + be_out + "known."
    )

    return (agent_info_pre_cond_str, agent_info_effect_str)


def get_mapping_description(mapping: Tuple[str, str, float]) -> str:
    return f"Values for Variable {mapping[0]} can be used for Variable {mapping[1]}."


def get_mappings_description(mappings: List[Tuple[str, str, float]]) -> str:
    return " ".join(list(map(lambda mapping: get_mapping_description(mapping), mappings)))


def get_goal_description(goals: Set[str]) -> str:
    goals_list = sorted(list(map(lambda name: "Action " + name, goals)))

    return f"The goal of the system is to execute {get_names(goals_list)}."


def get_description_available_data(available_items: List[Tuple[str, Optional[str]]]) -> str:
    item_list = list(map(lambda available_item: "Variable " + available_item[0], available_items))

    return f"Values are available already for {get_names(item_list)}."
