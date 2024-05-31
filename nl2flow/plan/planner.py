from nl2flow.compile.flow import Flow
from nl2flow.compile.utils import Transform, revert_string_transform
from nl2flow.plan.schemas import Action, RawPlan, PlannerResponse, ClassicalPlan as Plan
from nl2flow.plan.options import TIMEOUT
from nl2flow.plan.utils import parse_action, group_items, is_goal

from nl2flow.compile.schemas import (
    Constraint,
    PDDL,
)

from nl2flow.compile.options import (
    BasicOperations,
    SlotOptions,
    MappingOptions,
    ConfirmOptions,
)

from abc import ABC, abstractmethod
from typing import Any, List, Set
from copy import deepcopy


class Planner(ABC):
    def __init__(self) -> None:
        self._timeout: int = TIMEOUT

    @property
    def timeout(self) -> int:
        return self._timeout

    @timeout.setter
    def timeout(self, set_timeout: int) -> None:
        self._timeout = int(set_timeout)

    @abstractmethod
    def plan(self, pddl: PDDL, **kwargs: Any) -> PlannerResponse:
        pass

    @classmethod
    def post_process(cls, planner_response: PlannerResponse, **kwargs: Any) -> PlannerResponse:
        flow_object: Flow = kwargs["flow"]

        slot_options: Set[SlotOptions] = flow_object.slot_options
        mapping_options: Set[MappingOptions] = flow_object.mapping_options
        confirm_options: Set[ConfirmOptions] = flow_object.confirm_options

        for index, plan in enumerate(planner_response.list_of_plans):
            new_plan = deepcopy(plan)

            if SlotOptions.group_slots in slot_options:
                new_plan = group_items(new_plan, SlotOptions.group_slots)

            if MappingOptions.group_maps in mapping_options:
                new_plan = group_items(new_plan, MappingOptions.group_maps)

            if ConfirmOptions.group_confirms in confirm_options:
                new_plan = group_items(new_plan, ConfirmOptions.group_confirms)

            new_plan.length = len(new_plan.plan)
            planner_response.list_of_plans[index] = new_plan

        return planner_response

    @classmethod
    def pretty_print_plan_verbose(cls, flow_object: Flow, plan: Plan) -> str:
        verbose_strings = []

        for step, action in enumerate(plan.plan):
            if isinstance(action, Action):
                if action.name == BasicOperations.SLOT_FILLER.value:
                    verbose_strings.append(f"{step}. Acquire the value of {action.inputs[0]} by asking the user.")

                elif action.name == BasicOperations.MAPPER.value:
                    verbose_strings.append(
                        f"{step}. Get the value of {action.inputs[1]} from {action.inputs[0]} which is already known."
                    )

                elif action.name == BasicOperations.CONFIRM.value:
                    verbose_strings.append(
                        f"{step}. Confirm with the user that the value of {action.inputs[0]} is correct."
                    )

                else:
                    inputs = ", ".join(action.inputs) or None
                    input_string = f" with {inputs} as input{'s' if len(action.inputs) > 1 else ''}" if inputs else ""

                    outputs = ", ".join(action.outputs) or None
                    output_string = f" This will result in acquiring {outputs}." if outputs else ""

                    action_string = f"{step}. Execute action {action.name}{input_string}.{output_string}"

                    if is_goal(action.name, flow_object):
                        action_string += f" Since {action.name} was a goal of this plan, return the results of {action.name}({inputs}) to the user."

                    verbose_strings.append(action_string)

            elif isinstance(action, Constraint):
                constraint_string = f"Check that {action.constraint} is {action.truth_value}"
                verbose_strings.append(f"{step}. {constraint_string}.")

        return "\n".join(verbose_strings)

    @classmethod
    def pretty_print_plan(cls, plan: Plan, show_output: bool = True, line_numbers: bool = True) -> str:
        pretty = ""

        for step, action in enumerate(plan.plan):
            if isinstance(action, Action):
                inputs = ", ".join(action.inputs) or None
                input_string = f"({inputs or ''})"

                outputs = ", ".join(action.outputs) or None
                output_string = f"{outputs} = " if outputs else ""

                pretty += f"{f'[{step}] ' if line_numbers else ''}{output_string if show_output else ''}{action.name}{input_string}\n"

            elif isinstance(action, Constraint):
                constraint_string = f"assert {'' if action.truth_value else 'not '}{action.constraint}"
                pretty += f"{f'[{step}] ' if line_numbers else ''}{constraint_string}\n"

        return pretty.strip()

    @classmethod
    def pretty_print(cls, planner_response: PlannerResponse) -> str:
        pretty = ""

        for index, plan in enumerate(planner_response.list_of_plans):
            pretty += f"\n\n---- Plan #{index} ----\n"
            pretty += f"Cost: {plan.cost}, Length: {plan.length}\n\n"
            pretty += cls.pretty_print_plan(plan)

        return pretty


class FDDerivedPlanner(ABC):
    @classmethod
    def parse(cls, raw_plans: List[RawPlan], **kwargs: Any) -> List[Plan]:
        list_of_plans = list()

        flow_object: Flow = kwargs["flow"]
        transforms: List[Transform] = kwargs.get("transforms", [])

        for plan in raw_plans:
            new_plan = Plan(cost=plan.cost, reference=plan.actions)
            actions = plan.actions

            for action in actions:
                action_split = action.split()
                action_name = revert_string_transform(action_split[0], transforms)

                if action_name is not None:
                    new_action = parse_action(
                        action_name=action_name,
                        parameters=action_split[1:],
                        flow_object=flow_object,
                        transforms=transforms,
                    )
                else:
                    raise ValueError("Could not parse action name.")

                if new_action:
                    new_plan.plan.append(new_action)

            new_plan.length = len(new_plan.plan)
            list_of_plans.append(new_plan)

        return list_of_plans
