from nl2flow.printers.driver import Printer
from nl2flow.plan.schemas import Action, ClassicalPlan as Plan
from nl2flow.compile.schemas import Step, Constraint
from nl2flow.compile.options import BasicOperations
from typing import List, Union, Tuple, Any
from re import match
from warnings import warn


def parse_parameters(signature: str) -> Tuple[str, List[str]]:
    try:
        match_object = match(pattern=r"\s*(?P<action_name>.*)\((?P<parameters>.*)\)\s*", string=signature)

        if match_object:
            action_name = match_object.groupdict().get("action_name", "")
            parameters = match_object.groupdict().get("parameters", None)

            return action_name, [] if not parameters else [p.strip() for p in parameters.split(",")]
        else:
            return "", []

    except Exception as e:
        warn(message=f"Could not parse {signature}: {e}", category=SyntaxWarning)
        return "", []


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
                constraint_string = action.constraint

                if collapse_maps:
                    constraint_parameters = action.get_variable_references_from_constraint(
                        action.constraint, transforms=[]
                    )

                    for p in constraint_parameters:
                        constraint_string = constraint_string.replace(f"${p}", f"${current_maps.get(p, p)}")

                new_string += f"assert {'' if action.truth_value else 'not '}{constraint_string}"
                current_index += 1

            pretty.append(new_string)

        return "\n".join(pretty)

    @classmethod
    def parse_token(cls, token: str, **kwargs: Any) -> Union[Step, Constraint, None]:
        try:
            match_object = match(pattern=r"\s*(\[[0-9]+]\s+)?(?P<token>.*)\s*", string=token)
            token = "" if match_object is None else match_object.groupdict().get("token", "")
            token = token.strip()

            new_action = None

            for operation in BasicOperations:
                action_name = operation.value

                if token.startswith(action_name):
                    if token.startswith(BasicOperations.CONSTRAINT.value):
                        new_action = Constraint(
                            constraint=token.replace(f"{BasicOperations.CONSTRAINT.value} ", "")
                            .replace("not ", "")
                            .strip(),
                            truth_value=not token.startswith(f"{BasicOperations.CONSTRAINT.value} not"),
                        )
                    else:
                        action_name, parameters = parse_parameters(token)
                        new_action = Step(name=action_name, parameters=parameters)

            if new_action is None:
                action_split = token.split(" = ")
                agent_signature = action_split[0] if len(action_split) == 1 else action_split[1]
                action_name, parameters = parse_parameters(agent_signature)
                new_action = Step(name=action_name, parameters=parameters)

            if new_action:
                return new_action
            else:
                warn(message=f"Unrecognized token: {token}", category=SyntaxWarning)
                return None

        except Exception as e:
            warn(message=f"Unrecognized token: {token}, {e}")
            return None
