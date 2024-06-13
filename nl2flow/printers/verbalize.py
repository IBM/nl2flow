from nl2flow.compile.flow import Flow
from nl2flow.printers.driver import Printer
from nl2flow.plan.schemas import Action, ClassicalPlan as Plan
from nl2flow.plan.utils import find_goal, get_all_goals
from nl2flow.compile.schemas import Step, Constraint
from nl2flow.compile.options import GoalType
from nl2flow.compile.options import BasicOperations
from typing import Any, Union, List, Set, Dict


def who_need_it(constraint_string: str, flow_object: Flow, postfix: List[Union[Action, Constraint]]) -> List[str]:
    item_map = set()

    for step in postfix:
        if isinstance(step, Action) and not BasicOperations.is_basic(step.name):
            action_definition = next(filter(lambda x: x.name == step.name, flow_object.flow_definition.operators))
            constraints = []

            for signature_item in action_definition.inputs:
                constraints.extend(signature_item.constraints)

            if constraint_string in [item.constraint for item in constraints]:
                item_map.add(step.name)

    return sorted(list(item_map))


def who_run_it(items: List[str], postfix: List[Union[Action, Constraint]]) -> Dict[str, List[str]]:
    item_map: Dict[str, Set[str]] = {item: set() for item in items}

    for item in items:
        for step in postfix:
            if isinstance(step, Constraint):
                parameters = step.get_variable_references_from_constraint(step.constraint, transforms=[])

                if item in parameters:
                    constraint_string = f"constraint {step.constraint}"
                    item_map[item].add(constraint_string)
            else:
                if item in step.inputs:
                    if step.name == BasicOperations.MAPPER.value:
                        index_of_map = postfix.index(step)
                        new_postfix = postfix[index_of_map + 1 :] if index_of_map < len(postfix) - 1 else []
                        recursive_lookahead = get_lookahead_string(step.inputs[1:], new_postfix)
                        action_string = f"action {step.name} to produce {step.inputs[1]} ({recursive_lookahead})"
                    else:
                        action_string = f"action {step.name}"

                    item_map[item].add(action_string)

    item_map_list_sorted = {item: sorted(list(item_map[item])) for item in item_map}
    return item_map_list_sorted


def get_lookahead_string(items: List[str], postfix: List[Union[Action, Constraint]]) -> str:
    lookahead_string = ""

    for item in items:
        who_run_this = who_run_it(items=[item], postfix=postfix)
        who_all = who_run_this.get(item, [])

        if who_all:
            who_run_it_string = comma_separate(who_all)
            lookahead_string += f"{item} is required later by {who_run_it_string}"

    return lookahead_string


def comma_separate(list_of_strings: List[str]) -> str:
    return (
        " and ".join(list_of_strings)
        if len(list_of_strings) <= 2
        else f"{', '.join(list_of_strings[:-1])}, and {list_of_strings[-1]}"
    )


class VerbalizePrint(Printer):
    @staticmethod
    def verbalize_slot(action: Action, lookahead: bool, postfix: List[Union[Action, Constraint]]) -> str:
        slot_string = f"Acquire the value of {action.inputs[0]} by asking the user."

        if lookahead:
            lookahead_string = get_lookahead_string(items=[action.inputs[0]], postfix=postfix)
            return f"{slot_string} {lookahead_string}."

        else:
            return slot_string

    @staticmethod
    def verbalize_map(action: Action, lookahead: bool, postfix: List[Union[Action, Constraint]]) -> str:
        map_string = f"Get the value of {action.inputs[1]} from {action.inputs[0]} which is already known."

        if lookahead:
            lookahead_string = get_lookahead_string(items=[action.inputs[1]], postfix=postfix)
            return f"{map_string} {lookahead_string}."

        else:
            return map_string

    @staticmethod
    def verbalize_confirm(action: Action) -> str:
        return f"Confirm with the user that the value of {action.inputs[0]} is correct."

    @staticmethod
    def verbalize_constraint(
        constraint: Constraint, flow_object: Flow, lookahead: bool, postfix: List[Union[Action, Constraint]]
    ) -> str:
        constraint_string = f"Check that {constraint.constraint} is {constraint.truth_value}."
        all_goals = get_all_goals(flow_object=flow_object)

        if lookahead:
            who_need_it_string = comma_separate(who_need_it(constraint.constraint, flow_object, postfix))
            constraint_string += f" This is needed to execute {who_need_it_string}." if who_need_it_string else ""

        if find_goal(constraint.constraint, flow_object) is not None:
            constraint_string += f" This was {'a' if len(all_goals) > 1 else 'the'} goal of the plan."

        return constraint_string

    @classmethod
    def verbalize_action(
        cls,
        action: Action,
        flow_object: Flow,
        mapped_items: Dict[str, str],
        lookahead: bool,
        postfix: List[Union[Action, Constraint]],
    ) -> str:
        input_string = (
            f" with {comma_separate(action.inputs)} as input{'s' if len(action.inputs) > 1 else ''}"
            if action.inputs
            else ""
        )

        output_string = f" This will result in acquiring {comma_separate(action.outputs)}." if action.outputs else ""
        action_string = f"Execute action {action.name}{input_string}.{output_string}"

        if lookahead:
            lookahead_string = get_lookahead_string(action.outputs, postfix)
            action_string += f" {lookahead_string}." if lookahead_string else ""

        action_string += cls.verbalize_goal(action, flow_object, mapped_items)
        return action_string

    @staticmethod
    def verbalize_goal(action: Action, flow_object: Flow, mapped_items: Dict[str, str]) -> str:
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
            goal_outputs_string = comma_separate(goal_outputs)
            return f" Since acquiring {goal_outputs_string} was {'the' if len(all_goals) == 1 else 'a'} goal of this plan, return {goal_outputs_string} to the user."

        goal_inputs = list()

        for item in action.inputs:
            goal_match = find_goal(mapped_items.get(item, item), flow_object)
            if goal_match and goal_match.goal_type == GoalType.OBJECT_USED:
                goal_inputs.append(goal_match.goal_name)

        if goal_inputs:
            goal_inputs_string = comma_separate(goal_inputs)
            return f" The goal of using {goal_inputs_string} is now complete."

        return ""

    @classmethod
    def pretty_print_plan(cls, plan: Plan, **kwargs: Any) -> str:
        flow_object: Flow = kwargs["flow_object"]
        bulleted: bool = kwargs.get("bulleted", True)
        lookahead: bool = kwargs.get("lookahead", False)

        verbose_strings = list()
        mapped_items = dict()

        for step, action in enumerate(plan.plan):
            new_string = f"{step}. " if bulleted else ""
            postfix = plan.plan[step + 1 :] if step != len(plan.plan) else []

            if isinstance(action, Action):
                if action.name == BasicOperations.SLOT_FILLER.value:
                    new_string += cls.verbalize_slot(action, lookahead, postfix)

                elif action.name == BasicOperations.MAPPER.value:
                    mapped_items[action.inputs[1]] = action.inputs[0]
                    new_string += cls.verbalize_map(action, lookahead, postfix)

                elif action.name == BasicOperations.CONFIRM.value:
                    new_string += cls.verbalize_confirm(action)

                else:
                    new_string += cls.verbalize_action(action, flow_object, mapped_items, lookahead, postfix)

            elif isinstance(action, Constraint):
                new_string += cls.verbalize_constraint(action, flow_object, lookahead, postfix)

            verbose_strings.append(new_string)

        delimiter = "\n" if bulleted else " "
        return delimiter.join(verbose_strings)

    @classmethod
    def parse_token(cls, token: str, **kwargs: Any) -> Union[Step, Constraint, None]:
        raise NotImplementedError
