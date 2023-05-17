from typing import List, Set, Tuple
from nl2flow.compile.flow import Flow
from profiler.data_types.agent_info_data_types import AgentInfo, Plan
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.schemas import (
    MemoryItem,
    MemoryState,
    SignatureItem,
    MappingItem,
    GoalItems,
    GoalItem,
    SlotProperty,
    MappingItem,
)
from profiler.converters.converter_variables import (
    AGENT_ID,
    ACTUATOR_SIGNATURE,
    SIGNATURE_TYPES,
    IN_SIGNATURE,
    OUT_SIGNATURE,
    SEQUENCE_ALIAS,
    SLOT_FILLABLE,
    NAME,
    REQUIRED,
)
from uuid import uuid4


def get_uuid() -> str:
    return str(uuid4())


def get_name(signature_item: SignatureItem) -> str:
    return (
        signature_item[SEQUENCE_ALIAS][:]
        if SEQUENCE_ALIAS in signature_item
        else signature_item[NAME]
    )


def get_operators_for_flow(available_agents: List[AgentInfo]) -> List[Operator]:
    operators: List[Operator] = list()
    for agent_info in available_agents:
        operator = Operator(agent_info[AGENT_ID])
        if ACTUATOR_SIGNATURE in agent_info:
            for signature_type in SIGNATURE_TYPES:
                if (
                    signature_type in agent_info[ACTUATOR_SIGNATURE]
                    and agent_info[ACTUATOR_SIGNATURE][signature_type] is not None
                ):
                    signature_names: List[str] = list()
                    for signature_item in agent_info[ACTUATOR_SIGNATURE][
                        signature_type
                    ]:
                        if signature_type == OUT_SIGNATURE:
                            signature_names.append(get_name(signature_item))
                        else:
                            if REQUIRED in signature_item and signature_item[REQUIRED]:
                                signature_names.append(get_name(signature_item))

                    if signature_type == IN_SIGNATURE and REQUIRED:
                        operator.add_input(SignatureItem(parameters=signature_names))
                    else:
                        operator.add_output(SignatureItem(parameters=signature_names))
        operators.append(operator)
    return operators


def get_goals_for_flow(goals: Set[str]) -> GoalItems:
    return GoalItems(goals=list(map(lambda name: GoalItem(goal_name=name), goals)))


def get_slot_fillers_for_flow(available_agents: List[AgentInfo]) -> List[SlotProperty]:
    slot_names: Set[str] = set()
    none_slot_fillable_names: set[str] = set()
    slot_properties: List[SlotProperty] = list()
    for agent_info in available_agents:
        if ACTUATOR_SIGNATURE in agent_info:
            for signature_type in SIGNATURE_TYPES:
                if (
                    signature_type in agent_info[ACTUATOR_SIGNATURE]
                    and agent_info[ACTUATOR_SIGNATURE][signature_type] is not None
                ):
                    for signature_item in agent_info[ACTUATOR_SIGNATURE][
                        signature_type
                    ]:
                        name = get_name(signature_item)
                        if (
                            SLOT_FILLABLE in signature_item
                            and signature_item[SLOT_FILLABLE]
                        ):
                            if name not in slot_names:
                                slot_names.add(name)
                                slot_properties.append(SlotProperty(slot_name=name))
                        else:
                            if name not in none_slot_fillable_names:
                                none_slot_fillable_names.add(name)
                                slot_properties.append(
                                    SlotProperty(slot_name=name, slot_desirability=0.0)
                                )

    return slot_properties


def get_data_mappers_for_flow(
    mappings: List[Tuple[str, str, float]]
) -> List[MappingItem]:
    return list(
        map(
            lambda mapping: MappingItem(
                source_name=mapping[0], target_name=mapping[1], probability=mapping[2]
            ),
            mappings,
        )
    )


def get_available_data_for_flow(available_data: List[str]) -> List[MemoryItem]:
    return list(
        map(
            lambda signature_item_name: MemoryItem(
                item_id=signature_item_name, item_state=MemoryState.KNOWN
            ),
            available_data,
        )
    )


def get_flow_from_agent_infos(
    available_agents: List[AgentInfo],
    mappings: List[Tuple[str, str, float]],
    goals: Set[str],
    available_data: List[str],
    flow_name: str = "default_name",
) -> Flow:
    flow = Flow(flow_name)
    flow.add(
        get_operators_for_flow(available_agents)
        + get_slot_fillers_for_flow(available_agents)
        + get_data_mappers_for_flow(mappings)
        + get_available_data_for_flow(available_data)
        + [get_goals_for_flow(goals)]
    )
    return flow


def get_pddl_plan_str(plan: Plan) -> str:
    plan_strs: List[str] = list()
    for plan_action in plan["plan"]:
        action_name = plan_action["action_name"]
        parameters = " ".join(plan_action["parameters"])
        plan_strs.append(f"({action_name} {parameters})")
    return "\n".join(plan_strs)
