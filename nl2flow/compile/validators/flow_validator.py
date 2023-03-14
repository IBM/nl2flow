import collections

from typing import Set, List, Dict, Optional
from nl2flow.compile.utils import string_transform
from nl2flow.compile.validators.validator import Validator, ValidationMessage
from nl2flow.compile.options import GoalType
from nl2flow.plan.schemas import Step, Parameter
from nl2flow.compile.schemas import (
    FlowDefinition,
    MemoryItem,
    SignatureItem,
    Constraint,
    Transform,
    GoalItem,
)


def update_object_map(
    list_of_objects: Dict[str, Set[str]], object_name: str, object_type: Optional[str]
) -> None:
    if object_name not in list_of_objects:
        if object_type:
            list_of_objects[object_name] = {object_type}
        else:
            list_of_objects[object_name] = set()
    else:
        if object_type:
            list_of_objects[object_name].add(object_type)


def signature_parser(
    list_of_objects: Dict[str, Set[str]], signature_item: SignatureItem
) -> None:
    for parameter in signature_item.parameters:
        parameter_name = (
            parameter.item_id if isinstance(parameter, MemoryItem) else parameter
        )
        parameter_type = (
            parameter.item_type if isinstance(parameter, MemoryItem) else None
        )

        update_object_map(list_of_objects, parameter_name, parameter_type)

    for constraint in signature_item.constraints:
        constraint_parser(list_of_objects, constraint)


def constraint_parser(
    list_of_objects: Dict[str, Set[str]], constraint: Constraint
) -> None:
    update_object_map(list_of_objects, constraint.constraint_id, None)
    for p in constraint.parameters:
        update_object_map(list_of_objects, p, None)


def get_list_of_object_names(flow: FlowDefinition) -> Dict[str, Set[str]]:
    list_of_objects: Dict[str, Set[str]] = dict()
    for item in flow.memory_items:
        update_object_map(list_of_objects, item.item_id, item.item_type)

    for item in flow.goal_items:
        goals: List[GoalItem] = (
            item.goals if isinstance(item.goals, List) else [item.goals]
        )
        for goal in goals:
            if goal.goal_type != GoalType.OPERATOR and goal.goal_name not in [
                t.name for t in flow.type_hierarchy
            ]:
                update_object_map(list_of_objects, goal.goal_name, None)

            elif goal.goal_type == GoalType.OPERATOR and isinstance(
                goal.goal_name, Step
            ):
                for param in goal.goal_name.parameters:
                    update_object_map(
                        list_of_objects,
                        param.item_id if isinstance(param, Parameter) else param,
                        None,
                    )

    for operator in flow.operators:
        for item in operator.inputs:
            signature_parser(list_of_objects, item)

        outputs = operator.outputs
        if not isinstance(outputs, List):
            outputs = [outputs]

        for output in outputs:
            for item in output.constraints:
                constraint_parser(list_of_objects, item)

            for item in output.outcomes:
                signature_parser(list_of_objects, item)

    return list_of_objects


class FlowValidator(Validator):
    @staticmethod
    def slots_are_among_known_memory_items(
        flow: FlowDefinition,
    ) -> ValidationMessage:

        list_of_object_names = get_list_of_object_names(flow)

        for slot in flow.slot_properties:
            if slot.slot_name not in list_of_object_names:
                return ValidationMessage(
                    truth_value=False,
                    error_message=f"Slot request with {slot.slot_name} unknown.",
                )

        return ValidationMessage(truth_value=True)

    @staticmethod
    def mappings_are_among_known_memory_items(
        flow: FlowDefinition,
    ) -> ValidationMessage:

        list_of_object_names = get_list_of_object_names(flow)

        for mapping in flow.list_of_mappings:
            for item in [mapping.source_name, mapping.target_name]:
                if item not in list_of_object_names:
                    return ValidationMessage(
                        truth_value=False,
                        error_message=f"Mapping request with {item} unknown.",
                    )

        return ValidationMessage(truth_value=True)

    @staticmethod
    def object_type_conflict(flow: FlowDefinition) -> ValidationMessage:

        list_of_object_names = get_list_of_object_names(flow)
        for item in list_of_object_names:
            type_set = list_of_object_names[item]
            if len(type_set) > 1:
                return ValidationMessage(
                    truth_value=False,
                    error_message=f"Object {item} has more than one type: {', '.join(type_set)}.",
                )

        return ValidationMessage(truth_value=True)

    @staticmethod
    def hash_conflicts(flow: FlowDefinition) -> ValidationMessage:

        transforms: List[Transform] = list()

        reference_list_of_objects = get_list_of_object_names(flow)
        reference_keys = list(reference_list_of_objects.keys())

        check_list_key = {
            "operators": "name",
            "type_hierarchy": "name",
            "constraints": "constraint_id",
            "history": "name",
        }

        for key in check_list_key:
            list_of_items = list(
                map(
                    lambda x: str(getattr(x, check_list_key[key])),
                    getattr(flow, key),
                )
            )

            for item in list_of_items:
                if item not in reference_keys:
                    reference_keys.append(item)

        transformed_keys = [
            string_transform(item, transforms) for item in reference_keys
        ]

        for item in reference_keys:
            item = string_transform(item, transforms)
            members = [o for o in transformed_keys if item == o]
            if len(members) > 1:
                return ValidationMessage(
                    truth_value=False,
                    error_message=f"Conflicting names for {item}.",
                )

        return ValidationMessage(truth_value=True)

    @staticmethod
    def no_duplicate_items(flow: FlowDefinition) -> ValidationMessage:
        def get_duplicates(list_item: List[str]) -> List[str]:
            return [i for i, c in collections.Counter(list_item).items() if c > 1]

        check_list_key = ["operators", "type_hierarchy"]
        for key in check_list_key:
            list_of_items = list(
                map(
                    lambda x: str(getattr(x, "name")),
                    getattr(flow, key),
                )
            )

            duplicate_list = get_duplicates(list_of_items)
            is_duplicate = len(duplicate_list) > 0
            if is_duplicate:
                return ValidationMessage(
                    truth_value=not is_duplicate,
                    error_message=f"Duplicate names for {key=} {', '.join(duplicate_list)}.",
                )

        return ValidationMessage(truth_value=True)
