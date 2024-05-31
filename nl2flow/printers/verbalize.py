from nl2flow.compile.flow import Flow
from nl2flow.printers.driver import Printer
from nl2flow.plan.schemas import Action, ClassicalPlan as Plan
from nl2flow.plan.utils import is_goal
from nl2flow.compile.schemas import Step, Constraint
from nl2flow.compile.options import BasicOperations
from typing import Any, Union


class VerbalizePrint(Printer):
    @classmethod
    def pretty_print_plan(cls, plan: Plan, **kwargs: Any) -> str:
        flow_object: Flow = kwargs["flow_object"]
        bulleted: bool = kwargs.get("bulleted", True)

        verbose_strings = []

        for step, action in enumerate(plan.plan):
            new_string = f"{step}. " if bulleted else ""

            if isinstance(action, Action):
                if action.name == BasicOperations.SLOT_FILLER.value:
                    new_string += f"Acquire the value of {action.inputs[0]} by asking the user."

                elif action.name == BasicOperations.MAPPER.value:
                    new_string += f"Get the value of {action.inputs[1]} from {action.inputs[0]} which is already known."

                elif action.name == BasicOperations.CONFIRM.value:
                    new_string += f"Confirm with the user that the value of {action.inputs[0]} is correct."

                else:
                    inputs = ", ".join(action.inputs) or None
                    input_string = f" with {inputs} as input{'s' if len(action.inputs) > 1 else ''}" if inputs else ""

                    outputs = ", ".join(action.outputs) or None
                    output_string = f" This will result in acquiring {outputs}." if outputs else ""

                    action_string = f"Execute action {action.name}{input_string}.{output_string}"

                    if is_goal(action.name, flow_object):
                        action_string += f" Since {action.name} was a goal of this plan, return the results of {action.name}({inputs}) to the user."

                    new_string += action_string

            elif isinstance(action, Constraint):
                constraint_string = f"Check that {action.constraint} is {action.truth_value}"
                new_string += f"{step}. {constraint_string}."

            verbose_strings.append(new_string)

        delimiter = "\n" if bulleted else " "
        return delimiter.join(verbose_strings)

    @classmethod
    def parse_token(cls, token: str) -> Union[Step, Constraint, None]:
        raise NotImplementedError
