import collections

from typing import Set, List
from nl2flow.compile.utils import string_transform
from nl2flow.compile.validators.validator import Validator, ValidationMessage
from nl2flow.compile.schemas import (
    FlowDefinition,
    MemoryItem,
    SignatureItem,
    Constraint,
    Transform,
)


def get_list_of_object_names(flow: FlowDefinition) -> Set[str]:
    def signature_parser(signature_item: SignatureItem) -> None:
        for parameter in signature_item.parameters:
            parameter = (
                parameter.item_id if isinstance(parameter, MemoryItem) else parameter
            )
            list_of_object_names.add(parameter)

        for constraint in signature_item.constraints:
            constraint_parser(constraint)

    def constraint_parser(constraint: Constraint) -> None:
        for p in constraint.parameters:
            list_of_object_names.add(p)

    list_of_object_names = {item.item_id for item in flow.memory_items}

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

    return list_of_object_names


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
    def no_duplicate_items(flow: FlowDefinition) -> ValidationMessage:
        def get_duplicates(list_item: List[str]) -> List[str]:
            return [i for i, c in collections.Counter(list_item).items() if c > 1]

        transforms: List[Transform] = list()
        check_list_key = {
            "operators": "name",
            "memory_items": "item_id",
            "type_hierarchy": "name",
        }

        for item in check_list_key:

            list_of_items = list(
                map(
                    lambda x: str(
                        string_transform(getattr(x, check_list_key[item]), transforms)
                    ),
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
