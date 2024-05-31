from nl2flow.printers.driver import Printer
from nl2flow.plan.schemas import Action, ClassicalPlan as Plan
from nl2flow.compile.schemas import Step, Constraint
from typing import Union, Any


class CodeLikePrint(Printer):
    @classmethod
    def pretty_print_plan(cls, plan: Plan, **kwargs: Any) -> str:
        show_output: bool = kwargs.get("show_output", True)
        line_numbers: bool = kwargs.get("line_numbers", True)

        pretty = []
        for step, action in enumerate(plan.plan):
            new_string = f"[{step}] " if line_numbers else ""

            if isinstance(action, Action):
                inputs = ", ".join(action.inputs) or None
                input_string = f"({inputs or ''})"

                outputs = ", ".join(action.outputs) or None
                output_string = f"{outputs} = " if outputs and show_output else ""

                new_string += f"{output_string}{action.name}{input_string}"

            elif isinstance(action, Constraint):
                new_string += f"assert {'' if action.truth_value else 'not '}{action.constraint}"

            pretty.append(new_string)

        return "\n".join(pretty)

    @classmethod
    def parse_token(cls, token: str) -> Union[Step, Constraint, None]:
        raise NotImplementedError
