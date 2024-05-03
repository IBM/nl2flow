from typing import Any, List, Optional, Union
from nl2flow.compile.flow import Flow
from nl2flow.compile.utils import revert_string_transform, string_transform
from nl2flow.compile.basic_compilations.utils import unpack_list_of_signature_items
from nl2flow.plan.schemas import ClassicalPlan, Action
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


def is_goal(action_name: str, flow_object: Flow) -> bool:
    for goal_items in flow_object.flow_definition.goal_items:
        goals = goal_items.goals

        if not isinstance(goals, List):
            goals = [goals]

        for goal in goals:
            if isinstance(goal, Constraint):
                continue
            else:
                goal_name = goal.goal_name.name if isinstance(goal.goal_name, Step) else goal.goal_name
                if action_name == goal_name:
                    return True

    return False


def parse_action(action_name: str, parameters: List[str], **kwargs: Any) -> Optional[Union[Action, Constraint]]:
    transforms = kwargs["transforms"]
    flow: Flow = kwargs["flow"]

    if any([action_name.startswith(item.value) for item in RestrictedOperations]):
        return None

    elif action_name.startswith(BasicOperations.SLOT_FILLER.value):
        new_action = Action(name=BasicOperations.SLOT_FILLER.value)

        temp = action_name.split("----")
        if temp[1:] and not parameters:
            parameters = temp[1:]

        new_action.inputs = [revert_string_transform(param, transforms) for param in parameters]
        return new_action

    elif action_name.startswith(BasicOperations.CONFIRM.value):
        new_action = Action(name=BasicOperations.CONFIRM.value)
        new_action.inputs = [revert_string_transform(param, transforms) for param in parameters]
        return new_action

    elif action_name.startswith(BasicOperations.MAPPER.value):
        new_action = Action(name=BasicOperations.MAPPER.value)

        temp = action_name.split("----")
        if temp[1:] and not parameters:
            parameters = temp[1:]

        new_action.inputs = [revert_string_transform(param, transforms) for param in parameters]
        return new_action

    elif action_name.startswith(BasicOperations.CONSTRAINT.value):
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
        operator: OperatorDefinition = next(filter(lambda x: x.name == action_name, flow.flow_definition.operators))
        new_action = Action(name=operator.name)

        new_action.inputs = unpack_list_of_signature_items(operator.inputs)

        if isinstance(operator.outputs, Outcome):
            new_action.outputs = unpack_list_of_signature_items(operator.outputs.outcomes)
        else:
            raise NotImplementedError("Only working on classical operators at the moment.")

        return new_action
