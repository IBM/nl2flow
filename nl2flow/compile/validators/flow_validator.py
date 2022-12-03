import collections

from typing import Set, List, Dict, Optional
from nl2flow.compile.utils import string_transform
from nl2flow.compile.validators.validator import Validator, ValidationMessage
from nl2flow.compile.schemas import (
    FlowDefinition,
    MemoryItem,
    SignatureItem,
    Constraint,
    Transform,
)


def get_list_of_object_names(flow: FlowDefinition) -> Dict[str, Set[str]]:
    def update_object_map(object_name: str, object_type: Optional[str]) -> None:
        if object_name not in list_of_objects:
            if object_type:
                list_of_objects[object_name] = {object_type}
            else:
                list_of_objects[object_name] = set()
        else:
            if object_type:
                list_of_objects[object_name].add(object_type)

    def signature_parser(signature_item: SignatureItem) -> None:
        for parameter in signature_item.parameters:
            parameter_name = (
                parameter.item_id if isinstance(parameter, MemoryItem) else parameter
            )
            parameter_type = (
                parameter.item_type if isinstance(parameter, MemoryItem) else None
            )

            update_object_map(parameter_name, parameter_type)

        for constraint in signature_item.constraints:
            constraint_parser(constraint)

    def constraint_parser(constraint: Constraint) -> None:
        for p in constraint.parameters:
            update_object_map(p, None)

    list_of_objects: Dict[str, Set[str]] = dict()
    for item in flow.memory_items:
        update_object_map(item.item_id, item.item_type)

    for operator in flow.operators:
        for item in operator.inputs:
            signature_parser(item)

        outputs = operator.outputs
        if not isinstance(outputs, List):
            outputs = [outputs]

        for output in outputs:
            for item in output.constraints:
                constraint_parser(item)

            for item in output.outcomes:
                signature_parser(item)

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
    def no_duplicate_items(flow: FlowDefinition) -> ValidationMessage:
        def get_duplicates(list_item: List[str]) -> List[str]:
            return [i for i, c in collections.Counter(list_item).items() if c > 1]

        transforms: List[Transform] = list()
        check_list_key = ["operators", "type_hierarchy"]

        for item in check_list_key:
            list_of_items = list(
                map(
                    lambda x: str(string_transform(getattr(x, "name"), transforms)),
                    getattr(flow, item),
                )
            )

            duplicate_list = get_duplicates(list_of_items)
            is_duplicate = len(duplicate_list) > 0
            if is_duplicate:
                return ValidationMessage(
                    truth_value=not is_duplicate,
                    error_message=f"Duplicate names for {item=} {', '.join(duplicate_list)}.",
                )

        return ValidationMessage(truth_value=True)
