from typing import Any, List, Optional, Union
from nl2flow.compile.flow import Flow
from nl2flow.compile.utils import revert_string_transform, string_transform
from nl2flow.plan.schemas import ClassicalPlan, Action, Parameter
from nl2flow.compile.options import (
    BasicOperations,
    RestrictedOperations,
    TypeOptions,
    SlotOptions,
    MappingOptions,
    ConfirmOptions,
    ConstraintState,
)
from nl2flow.compile.schemas import (
    OperatorDefinition,
    MemoryItem,
    SignatureItem,
    Outcome,
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
    )

    new_start_of_plan = 0
    temp_plan = []

    for index, action in enumerate(plan.plan):
        if action.name not in [item.value for item in BasicOperations]:
            new_start_of_plan = index
            break

        if action.name == action_name:
            new_action.inputs.extend(action.inputs)

        else:
            temp_plan.append(action)

    new_plan.plan = [new_action] + temp_plan + plan.plan[new_start_of_plan:] if new_start_of_plan else plan.plan
    return new_plan


def parse_action(
    action_name: str,
    parameters: List[str],
    **kwargs: Any,
) -> Optional[Action]:
    def __add_parameters(signatures: List[SignatureItem]) -> List[Parameter]:
        list_of_parameters: List[Parameter] = list()

        for signature_item in signatures:
            signature_parameters = (
                signature_item.parameters
                if isinstance(signature_item.parameters, List)
                else [signature_item.parameters]
            )

            for parameter in signature_parameters:
                if isinstance(parameter, Parameter):
                    list_of_parameters.append(
                        Parameter(
                            item_id=parameter.item_id,
                            item_type=parameter.item_type or TypeOptions.ROOT.value,
                        )
                    )

                elif isinstance(parameter, str):
                    find_in_memory = list(
                        filter(
                            lambda x: x.item_id == parameter,
                            flow.flow_definition.memory_items,
                        )
                    )

                    if find_in_memory:
                        memory_item: MemoryItem = find_in_memory[0]
                        list_of_parameters.append(
                            Parameter(
                                item_id=memory_item.item_id,
                                item_type=memory_item.item_type,
                            )
                        )

                    else:
                        list_of_parameters.append(Parameter(item_id=parameter, item_type=TypeOptions.ROOT.value))

        return list_of_parameters

    transforms = kwargs["transforms"]
    new_action = Action(name=action_name)
    flow: Flow = kwargs["flow"]

    if any([action_name.startswith(item.value) for item in BasicOperations]):
        if action_name.startswith(BasicOperations.SLOT_FILLER.value) or action_name.startswith(
            BasicOperations.MAPPER.value
        ):
            temp = action_name.split("----")
            new_action.name = (
                BasicOperations.SLOT_FILLER.value
                if BasicOperations.SLOT_FILLER.value in temp[0]
                else BasicOperations.MAPPER.value
            )

            if temp[1:] and not parameters:
                parameters = temp[1:]

        elif action_name.startswith(BasicOperations.CONSTRAINT.value):
            new_action_name = action_name.replace(f"{BasicOperations.CONSTRAINT.value}_", "")

            for v in ConstraintState:
                new_action_name = new_action_name.replace(f"_to_{string_transform(str(v.value), transforms)}", "")

            new_action_name = revert_string_transform(new_action_name, transforms)

            for v in ConstraintState:
                if action_name.endswith(f"_to_{string_transform(str(v.value), transforms)}"):
                    new_action_name = f"{BasicOperations.CONSTRAINT.value}(new_action_name) = {v.value}"

            new_action.name = new_action_name

        new_action.inputs = [
            Parameter(
                item_id=revert_string_transform(param, transforms),
                item_type=TypeOptions.ROOT.value,
            )
            for param in parameters
        ]

    elif any([action_name.startswith(item.value) for item in RestrictedOperations]):
        return None

    else:
        operator: OperatorDefinition = list(filter(lambda x: x.name == action_name, flow.flow_definition.operators))[0]

        new_action.inputs = __add_parameters(operator.inputs)

        if isinstance(operator.outputs, Outcome):
            new_action.outputs = __add_parameters(operator.outputs.outcomes)
        else:
            raise TypeError("Parsing classical action, must have only one outcome.")

    return new_action
