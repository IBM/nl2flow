from nl2flow.compile.flow import Flow
from nl2flow.printers.driver import Printer
from nl2flow.plan.schemas import Action, ClassicalPlan as Plan
from nl2flow.plan.utils import find_goal, get_all_goals
from nl2flow.compile.schemas import Step, Constraint
from nl2flow.compile.options import GoalType
from nl2flow.compile.options import BasicOperations
from typing import Any, Union, List, Dict


class VerbalizePrint(Printer):
    @classmethod
    def comma_separate(cls, list_of_strings: List[str]) -> str:
        return (
            " and ".join(list_of_strings)
            if len(list_of_strings) <= 2
            else f"{', '.join(list_of_strings[:-1])}, and {list_of_strings[-1]}"
        )

    @staticmethod
    def verbalize_slot(action: Action) -> str:
        return f"Acquire the value of {action.inputs[0]} by asking the user."

    @staticmethod
    def verbalize_map(action: Action) -> str:
        return f"Get the value of {action.inputs[1]} from {action.inputs[0]} which is already known."

    @staticmethod
    def verbalize_confirm(action: Action) -> str:
        return f"Confirm with the user that the value of {action.inputs[0]} is correct."

    @staticmethod
    def verbalize_constraint(constraint: Constraint, flow_object: Flow) -> str:
        constraint_string = f"Check that {constraint.constraint} is {constraint.truth_value}."
        all_goals = get_all_goals(flow_object=flow_object)

        if find_goal(constraint.constraint, flow_object) is not None:
            constraint_string += f" This was {'a' if len(all_goals) > 1 else 'the'} goal of the plan."

        return constraint_string

    @classmethod
    def verbalize_action(cls, action: Action, flow_object: Flow, mapped_items: Dict[str, str]) -> str:
        input_string = (
            f" with {cls.comma_separate(action.inputs)} as input{'s' if len(action.inputs) > 1 else ''}"
            if action.inputs
            else ""
        )

        output_string = (
            f" This will result in acquiring {cls.comma_separate(action.outputs)}." if action.outputs else ""
        )

        action_string = f"Execute action {action.name}{input_string}.{output_string}"
        action_string += cls.verbalize_goal(action, flow_object, mapped_items)

        return action_string

    @classmethod
    def verbalize_goal(cls, action: Action, flow_object: Flow, mapped_items: Dict[str, str]) -> str:
        inputs = ", ".join(action.inputs) or None

        all_goals = get_all_goals(flow_object)
        is_this_a_goal = find_goal(action.name, flow_object) is not None

        if is_this_a_goal:
            return f" Since executing {action.name} was {'the' if len(all_goals) == 1 else 'a'} goal of this plan, return the results of {action.name}({inputs}) to the user."

        goal_outputs = list()

        for item in action.outputs:
            goal_match = find_goal(item, flow_object)
            if goal_match and goal_match.goal_type == GoalType.OBJECT_KNOWN:
                goal_outputs.append(goal_match.goal_name)

        if goal_outputs:
            goal_outputs_string = cls.comma_separate(goal_outputs)
            return f" Since acquiring {goal_outputs_string} was {'the' if len(all_goals) == 1 else 'a'} goal of this plan, return {goal_outputs_string} to the user."

        goal_inputs = list()

        for item in action.inputs:
            goal_match = find_goal(mapped_items.get(item, item), flow_object)
            if goal_match and goal_match.goal_type == GoalType.OBJECT_USED:
                goal_inputs.append(goal_match.goal_name)

        if goal_inputs:
            goal_inputs_string = cls.comma_separate(goal_inputs)
            return f" The goal of using {goal_inputs_string} is now complete."

        return ""

    @classmethod
    def pretty_print_plan(cls, plan: Plan, **kwargs: Any) -> str:
        flow_object: Flow = kwargs["flow_object"]
        bulleted: bool = kwargs.get("bulleted", True)

        verbose_strings = list()
        mapped_items = dict()

        for step, action in enumerate(plan.plan):
            new_string = f"{step}. " if bulleted else ""

            if isinstance(action, Action):
                if action.name == BasicOperations.SLOT_FILLER.value:
                    new_string += cls.verbalize_slot(action)

                elif action.name == BasicOperations.MAPPER.value:
                    mapped_items[action.inputs[1]] = action.inputs[0]
                    new_string += cls.verbalize_map(action)

                elif action.name == BasicOperations.CONFIRM.value:
                    new_string += cls.verbalize_confirm(action)

                else:
                    new_string += cls.verbalize_action(action, flow_object, mapped_items)

            elif isinstance(action, Constraint):
                new_string += cls.verbalize_constraint(action, flow_object)

            verbose_strings.append(new_string)

        delimiter = "\n" if bulleted else " "
        return delimiter.join(verbose_strings)

    @classmethod
    def parse_token(cls, token: str, **kwargs: Any) -> Union[Step, Constraint, None]:
        raise NotImplementedError
