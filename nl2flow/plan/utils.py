from typing import List, Optional, Union
from nl2flow.compile.flow import Flow
from nl2flow.compile.utils import Transform, revert_string_transform, string_transform
from nl2flow.compile.basic_compilations.utils import unpack_list_of_signature_items
from nl2flow.plan.schemas import ClassicalPlan, Action
from nl2flow.debug.schemas import DebugFlag
from nl2flow.compile.options import (
    BasicOperations,
    RestrictedOperations,
    SlotOptions,
    MappingOptions,
    ConfirmOptions,
    ConstraintState,
)
from nl2flow.compile.schemas import (
    OperatorDefinition,
    Outcome,
    Constraint,
    GoalItem,
    Step,
)


def group_items(plan: ClassicalPlan, option: Union[SlotOptions, MappingOptions, ConfirmOptions]) -> ClassicalPlan:
    if option == SlotOptions.group_slots:
        action_name = BasicOperations.SLOT_FILLER.value

    elif option == MappingOptions.group_maps:
        action_name = BasicOperations.MAPPER.value

    elif option == ConfirmOptions.group_confirms:
        action_name = BasicOperations.CONFIRM.value

    else:
        raise TypeError("Unknown grouping option.")

    new_action = Action(name=action_name)
    new_plan = ClassicalPlan(
        cost=plan.cost,
        length=plan.length,
        metadata=plan.metadata,
        reference=plan.reference,
    )

    new_start_of_plan = 0
    temp_plan = []

    for index, action in enumerate(plan.plan):
        if action.name not in [
            item.value for item in BasicOperations if item.value != BasicOperations.CONSTRAINT.value
        ]:
            new_start_of_plan = index
            break

        if action.name == action_name:
            new_action.inputs.extend(action.inputs)

        else:
            temp_plan.append(action)

    new_plan.plan = [new_action] + temp_plan + plan.plan[new_start_of_plan:] if new_start_of_plan else plan.plan
    new_plan.length = len(new_plan.plan)
    return new_plan


def get_all_goals(flow_object: Flow) -> List[GoalItem]:
    list_of_goals = list()

    for goal_items in flow_object.flow_definition.goal_items:
        goals = goal_items.goals

        if not isinstance(goals, List):
            goals = [goals]

        for goal in goals:
            if isinstance(goal.goal_name, Constraint):
                list_of_goals.append(GoalItem(goal_name=goal.goal_name.constraint, goal_type=goal.goal_type))
            else:
                goal_name = goal.goal_name.name if isinstance(goal.goal_name, Step) else goal.goal_name
                list_of_goals.append(GoalItem(goal_name=goal_name, goal_type=goal.goal_type))

    return list_of_goals


def find_goal(name: str, flow_object: Flow) -> Optional[GoalItem]:
    all_goals = get_all_goals(flow_object)
    return next(filter(lambda goal_item: getattr(goal_item, "goal_name") == name, all_goals), None)


def parse_action(
    action_name: str,
    parameters: List[str],
    flow_object: Flow,
    transforms: List[Transform],
    debug_flag: DebugFlag,
) -> Optional[Union[Action, Constraint]]:
    if RestrictedOperations.is_restricted(action_name):
        return None

    which_basic = BasicOperations.which_basic(action_name)

    if which_basic:
        if which_basic == BasicOperations.CONSTRAINT:
            new_action_name = action_name.replace(f"{BasicOperations.CONSTRAINT.value}_", "", 1)
            action_split_for_id = new_action_name.split("_to_")

            constraint = revert_string_transform(action_split_for_id[0], transforms)
            assert constraint, ValueError(f"Failed to parse constraint id from {action_name}")

            action_split_for_truth_value = action_split_for_id[1].split("_with_")

            truth_value = None
            for v in ConstraintState:
                if string_transform(str(v.value), transforms) == action_split_for_truth_value[0]:
                    truth_value = v.value

            return Constraint(constraint=constraint, truth_value=truth_value)

        else:
            new_action = Action(name=which_basic.value)
            new_action.inputs = parameters
            return new_action

    else:
        filter_for_operators = filter(lambda x: x.name == action_name, flow_object.flow_definition.operators)
        operator: Optional[OperatorDefinition] = next(filter_for_operators, None)

        if operator is None:
            if debug_flag:
                return None
            else:
                raise ValueError(f"Tried to parse unknown operation: {action_name}, parameters: {parameters}")

        else:
            new_action = Action(
                name=operator.name,
                parameters=parameters,
                inputs=unpack_list_of_signature_items(operator.inputs),
            )

            if isinstance(operator.outputs, Outcome):
                new_action.outputs = unpack_list_of_signature_items(operator.outputs.outcomes)
            else:
                raise NotImplementedError("Only working on classical operators at the moment.")

            return new_action
