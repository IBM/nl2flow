from typing import List, Set, Tuple
from profiler.generators.info_generator.agent_info_data_types import (
    AgentInfo,
    AgentInfoSignatureItem,
)


def get_names(names: List[str]) -> str:
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return names[0] + " and " + names[1]

    return ", ".join(names[:-1]) + ", and " + names[-1]


def get_available_agents_description(available_agents: List[AgentInfo]) -> str:
    names_str = get_names(
        sorted(
            list(
                map(
                    lambda agent_info: "Action " + agent_info.get("agent_id"),
                    available_agents,
                )
            )
        )
    )

    return "The system has " + names_str + "."


def get_variables_description(
    available_agents: List[AgentInfo], available_data_names: List[str]
) -> str:
    variable_list = set(map(lambda name: "Variable " + name, available_data_names))

    for agent_info in available_agents:
        sig = agent_info.get("actuator_signature")
        # in sig
        in_sig = sig.get("in_sig_full")
        for in_sig_item in in_sig:
            variable_list.add("Variable " + in_sig_item.get("name"))

        # out sig
        out_sig = sig.get("out_sig_full")
        for out_sig_item in out_sig:
            variable_list.add("Variable " + out_sig_item.get("name"))

    names_str = get_names(sorted(list(variable_list)))
    return "The system has " + names_str + "."


def get_names_from_signature_items(
    sig_items: List[AgentInfoSignatureItem],
) -> List[str]:
    return list(map(lambda sig: "Variable " + sig.get("name"), sig_items))


def get_signature_item_names(sig_items: List[AgentInfoSignatureItem]) -> str:
    names = list(map(lambda sig: "Variable " + sig.get("name"), sig_items))

    return get_names(names)


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
    be_out = " is " if len(in_sig) == 1 else " are "
    agent_info_effect_str = (
        f"After executing Action {agent_id}, "
        + get_signature_item_names(out_sig)
        + be_out
        + "known."
    )
    # out_sig_items_description: List[str] = list()
    # for out_sig_item in out_sig:
    #     out_sig_items_description.append(
    #         get_agent_info_signature_item_description(out_sig_item))
    return (
        agent_info_pre_cond_str,
        " ".join(in_sig_items_description),
        agent_info_effect_str,
    )
    # return agent_info_pre_cond_str, " ".join(in_sig_items_description), agent_info_effect_str, " ".join(out_sig_items_description)


def get_agent_info_signature_item_description(
    sig_item: AgentInfoSignatureItem, is_output: bool = False
) -> str:
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
    return f"Values for Variable {mapping[0]} can be used for Variable {mapping[1]} with the confidance score of {round(mapping[2], 2)}."


def get_mappings_description(mappings: List[Tuple[str, str, float]]) -> str:
    return " ".join(
        list(map(lambda mapping: get_mapping_description(mapping), mappings))
    )


def get_goal_description(goals: Set[str]) -> str:
    goals_list = sorted(list(map(lambda name: "Action " + name, goals)))

    return f"The goal of the system is to execute {get_names(goals_list)}."


def get_description_available_data(available_item_names: List[str]) -> str:
    item_list = list(map(lambda name: "Variable " + name, available_item_names))

    return f"Values are available already for {get_names(item_list)}."
