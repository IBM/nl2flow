import collections

from typing import List
from nl2flow.compile.utils import string_transform
from nl2flow.compile.validators.validator import Validator, ValidationMessage
from nl2flow.compile.options import TypeOptions
from nl2flow.compile.schemas import (
    FlowDefinition,
    SignatureItem,
    GoalType,
    GoalItem,
    MemoryState,
    Constraint,
    Transform,
)


def __get_duplicates__(list_item: List[str]) -> List[str]:
    return [item for item, count in collections.Counter(list_item).items() if count > 1]


def __is_name_an_operator_name__(name: str, flow: FlowDefinition) -> bool:
    return name in map(lambda x: str(x.name), flow.operators)


def __is_name_a_type_name__(name: str, flow: FlowDefinition) -> bool:
    assert not any(
        t for t in TypeOptions if t.value == name
    ), "Cannot use reserved name {name} for type."
    return name in map(lambda x: str(x.name), flow.type_hierarchy)


def __is_name_an_object_name__(name: str, flow: FlowDefinition) -> bool:
    return name in map(lambda x: str(x.item_id), flow.memory_items)


def __check_constraint__(
    constraint: Constraint, flow: FlowDefinition
) -> ValidationMessage:
    _ = flow
    # for param in constraint.parameters:
    #     if isinstance(param, str):
    #         check_known_item = __is_name_a_type_name__(
    #             param, flow
    #         ) or __is_name_an_object_name__(param, flow)
    #         if not check_known_item:
    #             return ValidationMessage(
    #                 truth_value=check_known_item,
    #                 error_message=f"Unknown parameter for constraint: {constraint.constraint_id}.",
    #             )

    constraint_must_have_value = constraint.truth_value is not None
    if not constraint_must_have_value:
        return ValidationMessage(
            truth_value=constraint_must_have_value,
            error_message=f"Must specify truth value for constraint: {constraint.constraint_id}.",
        )

    return ValidationMessage(truth_value=True)


def __check_signature_item__(
    signature_item: SignatureItem, flow: FlowDefinition
) -> ValidationMessage:
    # for param in signature_item.parameters:
    #     check_known_item = __is_name_an_object_name__(param, flow)
    #     if not check_known_item:
    #         return ValidationMessage(
    #             truth_value=check_known_item,
    #             error_message=f"Unknown parameter {param} for signature.",
    #         )

    for constraint in signature_item.constraints:
        __check_constraint__(constraint, flow)

    return ValidationMessage(truth_value=True)


class FlowValidator(Validator):
    @staticmethod
    def is_start_item_an_operator(flow: FlowDefinition) -> ValidationMessage:
        start_item: str = flow.starts_with
        return ValidationMessage(
            truth_value=start_item is None
            or __is_name_an_operator_name__(start_item, flow),
            error_message=f"Start operator name {start_item} not found among list of operators.",
        )

    @staticmethod
    def is_end_item_an_operator(flow: FlowDefinition) -> ValidationMessage:
        end_item: str = flow.ends_with
        return ValidationMessage(
            truth_value=end_item is None
            or __is_name_an_operator_name__(end_item, flow),
            error_message=f"End operator name {end_item} not found among list of operators.",
        )

    @staticmethod
    def goals_are_of_proper_types(flow: FlowDefinition) -> ValidationMessage:
        for list_of_goal_items in flow.goal_items:
            goal_items = list_of_goal_items.goals

            if not isinstance(goal_items, List):
                goal_items = [goal_items]

            for goal_item in goal_items:

                if isinstance(goal_item, GoalItem):

                    goal_type_check = isinstance(goal_item.goal_type, GoalType)
                    if not goal_type_check:
                        return ValidationMessage(
                            truth_value=goal_type_check,
                            error_message="Unknown type of goal item.",
                        )

                    operator_goal_check = (
                        goal_item.goal_type == GoalType.OPERATOR
                        and not __is_name_an_operator_name__(goal_item.goal_name, flow)
                    )
                    if operator_goal_check:
                        return ValidationMessage(
                            truth_value=not operator_goal_check,
                            error_message=f"Attempt to add unknown operator: {goal_item.goal_name}.",
                        )

                    operator_object_check = (
                        goal_item.goal_type == GoalType.OBJECT
                        and not __is_name_a_type_name__(goal_item.goal_name, flow)
                    )
                    if operator_object_check:
                        return ValidationMessage(
                            truth_value=not operator_object_check,
                            error_message=f"Attempted to add unknown goal type: {goal_item.goal_name}.",
                        )

                elif isinstance(goal_item, Constraint):
                    __check_constraint__(goal_item, flow)

                else:
                    return ValidationMessage(
                        truth_value=False,
                        error_message="Goals are either constraints or goal items.",
                    )

        return ValidationMessage(truth_value=True)

    @staticmethod
    def mappings_are_among_known_memory_items(
        flow: FlowDefinition,
    ) -> ValidationMessage:
        for mapping in flow.list_of_mappings:

            probability_check = 0.0 <= mapping.probability <= 1.0
            if not probability_check:
                return ValidationMessage(
                    truth_value=probability_check,
                    error_message="Invalid mapping probability.",
                )

            source_sink_membership_check = __is_name_an_object_name__(
                mapping.source_name, flow
            ) and __is_name_an_object_name__(mapping.target_name, flow)
            if not source_sink_membership_check:
                return ValidationMessage(
                    truth_value=source_sink_membership_check,
                    error_message="Unknown source or target names.",
                )

        return ValidationMessage(truth_value=True)

    @staticmethod
    def all_constraints_are_fully_defined(flow: FlowDefinition) -> ValidationMessage:
        for constraint in flow.constraints:
            __check_constraint__(constraint, flow)

        return ValidationMessage(truth_value=True)

    @staticmethod
    def all_memory_items_have_known_concepts(flow: FlowDefinition) -> ValidationMessage:

        for item in flow.memory_items:

            state_type_check = isinstance(item.item_state, MemoryState)
            if not state_type_check:
                return ValidationMessage(
                    truth_value=state_type_check,
                    error_message=f"Memory item {item.item_id} has unknown state.",
                )

            check_for_known_types = __is_name_a_type_name__(item.item_type, flow)
            if not check_for_known_types and item.item_type is not None:
                return ValidationMessage(
                    truth_value=check_for_known_types,
                    error_message=f"Memory item {item.item_id} has unknown type.",
                )

        return ValidationMessage(truth_value=True)

    @staticmethod
    def partial_orders_are_operator_names(flow: FlowDefinition) -> ValidationMessage:
        for partial_order in flow.partial_orders:
            for name in [partial_order.precedent, partial_order.antecedent]:
                check_name = __is_name_an_operator_name__(name, flow) or name == "*"
                if not check_name:
                    return ValidationMessage(
                        truth_value=check_name,
                        error_message=f"Partial orders must be an operator name or total order *, found {name}.",
                    )

        return ValidationMessage(truth_value=True)

    @staticmethod
    def check_operator_definition(flow: FlowDefinition) -> ValidationMessage:

        for operator in flow.operators:
            for o_input in operator.inputs:

                # for param in o_input.parameters:
                #     if isinstance(param, str):
                #         is_param_known_object = __is_name_an_object_name__(param, flow)
                #         if not is_param_known_object:
                #             return ValidationMessage(
                #                 truth_value=is_param_known_object,
                #                 error_message=f"Unknown parameter for action: {operator.name}.",
                #             )

                for constraint in o_input.constraints:
                    __check_constraint__(constraint, flow)

            outputs = operator.outputs
            if not isinstance(outputs, List):
                outputs = [outputs]

            for outcome in outputs:
                for outcome_item in [outcome.conditions, outcome.outcomes]:
                    for signature_item in outcome_item:
                        __check_signature_item__(signature_item, flow)

        return ValidationMessage(truth_value=True)

    @staticmethod
    def no_duplicate_items(flow: FlowDefinition) -> ValidationMessage:

        transforms: List[Transform] = list()
        operators = map(
            lambda x: str(string_transform(x.name, transforms)), flow.operators
        )
        memory_items = map(
            lambda x: str(string_transform(x.item_id, transforms)), flow.memory_items
        )
        types = map(
            lambda x: str(string_transform(x.name, transforms)), flow.type_hierarchy
        )

        # TODO: Not sure what to do with constraint names spread across the definition. Is this allowed?
        constraints = map(lambda x: str(x.name.lower()), flow.constraints)

        check_list = [operators, memory_items, types, constraints]
        for item in check_list:
            duplicate_list = __get_duplicates__(list(item))
            is_duplicate = len(duplicate_list) > 0
            if is_duplicate:
                return ValidationMessage(
                    truth_value=not is_duplicate,
                    error_message=f"Duplicate names for {item=} {', '.join(duplicate_list)}.",
                )

        return ValidationMessage(truth_value=True)
