from typing import List, Optional, Set, Tuple
from nl2flow.compile.flow import Flow
from profiler.data_types.agent_info_data_types import AgentInfo, AgentInfoSignatureItem, Plan
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.schemas import (
    MemoryItem,
    MemoryState,
    SignatureItem,
    MappingItem,
    GoalItems,
    GoalItem,
    SlotProperty,
    Parameter,
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
from nl2flow.compile.options import SlotOptions
from uuid import uuid4


def get_uuid() -> str:
    return str(uuid4())


def get_name(signature_item: AgentInfoSignatureItem) -> str:
    if SEQUENCE_ALIAS not in signature_item:
        return str(signature_item[NAME])
    if signature_item[SEQUENCE_ALIAS] is not None:
        return str(signature_item[SEQUENCE_ALIAS])
    return ""


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
                    signature_names: List[Parameter] = list()
                    for signature_item in agent_info[ACTUATOR_SIGNATURE][signature_type]:
                        if signature_type == OUT_SIGNATURE:
                            signature_names.append(
                                Parameter(
                                    item_id=get_name(signature_item),
                                    item_type=signature_item["data_type"],
                                )
                            )
                        else:
                            if REQUIRED in signature_item and signature_item[REQUIRED]:
                                signature_names.append(
                                    Parameter(
                                        item_id=get_name(signature_item),
                                        item_type=signature_item["data_type"],
                                    )
                                )

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
                    for signature_item in agent_info[ACTUATOR_SIGNATURE][signature_type]:
                        name = get_name(signature_item)
                        if SLOT_FILLABLE in signature_item and signature_item[SLOT_FILLABLE]:
                            if name not in slot_names:
                                slot_names.add(name)
                                slot_properties.append(SlotProperty(slot_name=name, slot_desirability=1.0))
                        else:
                            if name not in none_slot_fillable_names:
                                none_slot_fillable_names.add(name)
                                slot_properties.append(SlotProperty(slot_name=name, slot_desirability=0.0))

    return slot_properties


def get_data_mappers_for_flow(mappings: List[Tuple[str, str, float]]) -> List[MappingItem]:
    return list(
        map(
            lambda mapping: MappingItem(source_name=mapping[0], target_name=mapping[1], probability=mapping[2]),
            mappings,
        )
    )


def get_available_data_for_flow(available_data: List[Tuple[str, Optional[str]]]) -> List[MemoryItem]:
    return list(
        map(
            lambda signature_item: MemoryItem(
                item_id=signature_item[0],
                item_type=signature_item[1],
                item_state=MemoryState.KNOWN,
            ),
            available_data,
        )
    )


def get_flow_from_agent_infos(
    available_agents: List[AgentInfo],
    mappings: List[Tuple[str, str, float]],
    goals: Set[str],
    available_data: List[Tuple[str, Optional[str]]],
    flow_name: str = "default_name",
    slot_filler_option: Optional[SlotOptions] = None,
) -> Flow:
    flow = Flow(flow_name)
    flow.add(
        get_operators_for_flow(available_agents)
        + get_available_data_for_flow(available_data)
        + get_data_mappers_for_flow(mappings)
        + get_slot_fillers_for_flow(available_agents)
        + [get_goals_for_flow(goals)]
    )
    if slot_filler_option is not None and slot_filler_option == SlotOptions.last_resort:
        flow.slot_options.add(SlotOptions.last_resort)
    return flow


def get_pddl_plan_str(plan: Plan) -> str:
    plan_strs: List[str] = list()
    for plan_action in plan["plan"]:
        action_name = plan_action["action_name"]
        parameters = " ".join(plan_action["parameters"])
        plan_strs.append(f"({action_name} {parameters})")
    return "\n".join(plan_strs)
