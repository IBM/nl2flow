from typing import List, Set, Tuple
from profiler.generators.info_generator.agent_info_data_types import AgentInfo, Plan
from nl2flow.compile.operators import Operator
from nl2flow.compile.schemas import (
    MemoryItem,
    SignatureItem,
    MappingItem,
    GoalItems,
    GoalItem,
    SlotProperty,
    MappingItem,
)


def get_available_agents_in_flow(
    available_agents: List[AgentInfo],
) -> Tuple[List[Operator], List[SlotProperty]]:
    return get_operators_for_flow(available_agents), get_slot_fillers_for_flow(
        available_agents
    )


def get_operators_for_flow(available_agents: List[AgentInfo]) -> List[Operator]:
    return []


def get_goals_for_flow(goals: Set[str]) -> GoalItems:
    # TODO: COMPLETE THIS
    return GoalItems()


def get_slot_fillers_for_flow(available_agents: List[AgentInfo]) -> List[SlotProperty]:
    # TODO: COMPLETE THIS
    return []


def get_data_mappers_for_flow(
    mappings: List[Tuple[str, str, float]]
) -> List[MappingItem]:
    return []


def get_pddl_plan_str(plan: Plan) -> str:
    plan_strs: List[str] = list()
    for plan_action in plan["plan"]:
        action_name = plan_action["action_name"]
        parameters = " ".join(plan_action["parameters"])
        plan_strs.append(f"({action_name} {parameters})")
    return "\n".join(plan_strs)
