from nl2flow.printers.driver import Printer
from nl2flow.plan.schemas import Action, ClassicalPlan as Plan
from nl2flow.compile.schemas import Step, Constraint
from nl2flow.compile.options import BasicOperations
from typing import Union, Any


class CodeLikePrint(Printer):
    @classmethod
    def pretty_print_plan(cls, plan: Plan, **kwargs: Any) -> str:
        show_output: bool = kwargs.get("show_output", True)
        line_numbers: bool = kwargs.get("line_numbers", True)
        collapse_maps: bool = kwargs.get("collapse_maps", False)
        start_at: int = kwargs.get("start_at", 0)

        pretty = []
        current_maps = dict()
        current_index = start_at

        for step, action in enumerate(plan.plan):
            new_string = f"[{current_index}] " if line_numbers else ""

            if isinstance(action, Action):
                if collapse_maps and action.name.startswith(BasicOperations.MAPPER.value):
                    current_maps[action.inputs[1]] = action.inputs[0]
                    continue

                inputs = [current_maps.get(item, item) for item in action.inputs]
                input_string = ", ".join(inputs) or None
                input_string = f"({input_string or ''})"

                outputs = ", ".join(action.outputs) or None
                output_string = f"{outputs} = " if outputs and show_output else ""

                new_string += f"{output_string}{action.name}{input_string}"
                current_index += 1

            elif isinstance(action, Constraint):
                new_string += f"assert {'' if action.truth_value else 'not '}{action.constraint}"
                current_index += 1

            pretty.append(new_string)

        return "\n".join(pretty)

    @classmethod
    def parse_token(cls, token: str) -> Union[Step, Constraint, None]:
        raise NotImplementedError
