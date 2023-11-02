from typing import List, Optional, Set, Tuple
from profiler.data_types.agent_info_data_types import (
    AgentInfo,
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
                    lambda agent_info: "Action " + agent_info.get("agent_id"),
                    available_agents,
                )
            )
        )
    )


def get_available_agents_description(available_agents: List[AgentInfo]) -> str:
    return "The system has " + get_available_action_names(available_agents) + "."


def get_variable_type_str(variable_name: str, type_str: Optional[str]) -> str:
    return (
        ""
        if type_str is None
        else f"The type of Variable {variable_name} is {type_str}."
    )


def get_variable_name_from_sig_item(
    sig_items: List[AgentInfoSignatureItem],
) -> List[str]:
    return list(map(lambda sig_item: "Variable " + sig_item.get("name"), sig_items))


def get_variable_type_from_sig_item(
    sig_items: List[AgentInfoSignatureItem],
) -> List[str]:
    return list(
        filter(
            lambda unfiltered_str: len(unfiltered_str) > 0,
            map(
                lambda sig_item: get_variable_type_str(
                    sig_item.get("name"), sig_item.get("data_type")
                ),
                sig_items,
            ),
        )
    )


def get_variables_description(
    available_agents: List[AgentInfo],
    available_data: List[Tuple[str, Optional[str]]],
) -> str:
    variable_list: List[str] = list()
    variable_type_strs: List[str] = list()
    for known_data in available_data:
        variable_list.append("Variable " + known_data[0])
        variable_type_str = get_variable_type_str(known_data[0], known_data[1])
        if len(variable_type_str) > 0:
            variable_type_strs.append(variable_type_str)
    for agent_info in available_agents:
        sig = agent_info.get("actuator_signature")
        variable_list += get_variable_name_from_sig_item(sig.get("in_sig_full"))
        variable_list += get_variable_name_from_sig_item(sig.get("out_sig_full"))
        variable_type_strs += get_variable_type_from_sig_item(sig.get("in_sig_full"))
        variable_type_strs += get_variable_type_from_sig_item(sig.get("out_sig_full"))

    return (
        "The system has "
        + get_names(sorted(list(set(variable_list))))
        + ".\n"
        + " ".join(sorted(list(set(variable_type_strs))))
    )


def get_names_from_signature_items(
    sig_items: List[AgentInfoSignatureItem],
) -> List[str]:
    return list(map(lambda sig: "Variable " + sig.get("name"), sig_items))


def get_signature_item_names(sig_items: List[AgentInfoSignatureItem]) -> str:
    return get_names(get_names_from_signature_items(sig_items))


def get_agent_info_description(agent_info: AgentInfo) -> Tuple[str, str, str]:
    agent_id = agent_info.get("agent_id")
    sig = agent_info.get("actuator_signature")
    # in sig
    in_sig = sig.get("in_sig_full")
    agent_info_pre_cond_str = (
        f"To execute Action {agent_id}, "
        + get_signature_item_names(in_sig)
        + " should be known."
    )

    in_sig_items_description: List[str] = list()
    for in_sig_item in in_sig:
        in_sig_items_description.append(
            get_agent_info_signature_item_description(in_sig_item)
        )

    # out sig
    out_sig = sig.get("out_sig_full")
    be_out = " is " if len(out_sig) == 1 else " are "
    agent_info_effect_str = (
        f"After executing Action {agent_id}, "
        + get_signature_item_names(out_sig)
        + be_out
        + "known."
    )

    return (
        agent_info_pre_cond_str,
        " ".join(in_sig_items_description),
        agent_info_effect_str,
    )


def get_agent_info_signature_item_description(sig_item: AgentInfoSignatureItem) -> str:
    sig_name = sig_item.get("name")
    required_str = "required" if sig_item.get("required") else "not required"
    slot_fillable_str = "can" if sig_item.get("slot_fillable") else "cannot"
    return (
        f"Variable {sig_name} is "
        + required_str
        + " and "
        + slot_fillable_str
        + " be acquired by asking the user."
    )


def get_mapping_description(mapping: Tuple[str, str, float]) -> str:
    return f"Values for Variable {mapping[0]} can be used for Variable {mapping[1]}."


def get_mappings_description(mappings: List[Tuple[str, str, float]]) -> str:
    return " ".join(
        list(map(lambda mapping: get_mapping_description(mapping), mappings))
    )


def get_goal_description(goals: Set[str]) -> str:
    goals_list = sorted(list(map(lambda name: "Action " + name, goals)))

    return f"The goal of the system is to execute {get_names(goals_list)}."


def get_description_available_data(
    available_items: List[Tuple[str, Optional[str]]]
) -> str:
    item_list = list(
        map(lambda available_item: "Variable " + available_item[0], available_items)
    )

    return f"Values are available already for {get_names(item_list)}."
