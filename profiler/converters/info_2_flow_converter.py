from typing import List, Optional, Set, Tuple
from nl2flow.compile.flow import Flow
from profiler.data_types.agent_info_data_types import AgentInfo, AgentInfoSignatureType, Plan, SIGNATURE_TYPES
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
from nl2flow.compile.options import SlotOptions, NL2FlowOptions
from uuid import uuid4


def get_uuid() -> str:
    return str(uuid4())


def get_operators_for_flow(available_agents: List[AgentInfo]) -> List[Operator]:
    operators: List[Operator] = list()
    for agent_info in available_agents:
        operator = Operator(agent_info.agent_id)
        for signature_type in SIGNATURE_TYPES:
            signature_names: List[Parameter] = list()
            for signature_item in agent_info.actuator_signature.get_signature(signature_type):
                signature_names.append(
                    Parameter(
                        item_id=signature_item.name,
                        item_type=signature_item.data_type,
                    )
                )

            if signature_type == AgentInfoSignatureType.IN_SIG_FULL:
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
        for signature_type in SIGNATURE_TYPES:
            for signature_item in agent_info.actuator_signature.get_signature(signature_type):
                name = signature_item.name
                if signature_item.slot_fillable:
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

    flow.optimization_options.remove(NL2FlowOptions.multi_instance)
    flow.optimization_options.remove(NL2FlowOptions.allow_retries)

    return flow


def get_pddl_plan_str(plan: Plan) -> str:
    plan_strs: List[str] = list()
    for plan_action in plan.plan:
        action_name = plan_action.action_name
        parameters = " ".join(plan_action.parameters)
        plan_strs.append(f"({action_name} {parameters})")
    return "\n".join(plan_strs)
