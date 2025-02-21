from nl2flow.printers.driver import Printer
from nestful.utils import parse_parameters
from nl2flow.plan.schemas import Action, ClassicalPlan as Plan
from nl2flow.compile.schemas import Step, Constraint
from nl2flow.compile.options import BasicOperations, ConstraintState
from typing import Union, Any
from re import match


class CustomPrint(Printer):
    @classmethod
    def pretty_print_plan(cls, plan: Plan, **kwargs: Any) -> str:
        pretty = []

        for step, action in enumerate(plan.plan):
            if isinstance(action, Action):
                if action.name.startswith(BasicOperations.SLOT_FILLER.value) or action.name.startswith(
                    BasicOperations.CONFIRM.value
                ):
                    new_string = f"{action.name} {action.inputs[0]}"

                elif action.name.startswith(BasicOperations.MAPPER.value):
                    new_string = f"{action.name} {action.inputs[0]} -> {action.inputs[1]}"

                else:
                    input_string = ", ".join(action.inputs) or None
                    input_string = f"({input_string or ''})"

                    outputs = ", ".join(action.outputs) or None
                    output_string = f" -> {outputs}" if outputs else ""

                    new_string = f"{action.name}{input_string}{output_string}"

            elif isinstance(action, Constraint):
                new_string = f"check if {action.constraint} is {action.truth_value}"

            else:
                continue

            pretty.append(new_string)

        return "\n".join(pretty)

    @classmethod
    def parse_token(cls, token: str, **kwargs: Any) -> Union[Step, Constraint]:
        token = token.strip()

        if token.startswith(BasicOperations.SLOT_FILLER.value):
            return Step(
                name=BasicOperations.SLOT_FILLER.value,
                parameters=token.split()[1:],
            )

        elif token.startswith(BasicOperations.MAPPER.value):
            match_object = match(pattern=rf"{BasicOperations.MAPPER.value} (?P<from>.*) -> (?P<to>.*)", string=token)

            if match_object:
                parsed_items = match_object.groupdict()
                return Step(
                    name=BasicOperations.MAPPER.value,
                    parameters=[parsed_items.get("from"), parsed_items.get("to")],
                )
            else:
                raise SyntaxError(f"Could not parse mapping: {token}")

        elif token.startswith(BasicOperations.CONFIRM.value):
            return Step(
                name=BasicOperations.CONFIRM.value,
                parameters=token.split()[1:],
            )

        elif token.startswith("check"):
            match_object = match(pattern=r"check if (?P<constraint>.*) is (?P<truth_value>.*)", string=token)

            if match_object:
                parsed_items = match_object.groupdict()
                return Constraint(
                    constraint=parsed_items.get("constraint"),
                    truth_value=parsed_items.get("truth_value") == str(ConstraintState.TRUE.value),
                )
            else:
                raise SyntaxError(f"Could not parse constraint: {token}")
        else:
            action_split = token.split(" -> ")
            agent_signature = action_split[0]
            action_name, parameters = parse_parameters(agent_signature)
            return Step(
                name=action_name,
                parameters=parameters,
            )
