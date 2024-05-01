from nl2flow.compile.flow import Flow
from nl2flow.compile.utils import revert_string_transform
from nl2flow.plan.schemas import Action, RawPlannerResult, RawPlan, PlannerResponse, ClassicalPlan as Plan
from nl2flow.plan.options import QUALITY_BOUND, NUM_PLANS, TIMEOUT
from nl2flow.plan.utils import parse_action, group_items, is_goal
from nl2flow.compile.schemas import PDDL, Constraint
from nl2flow.compile.options import (
    BasicOperations,
    SlotOptions,
    MappingOptions,
    ConfirmOptions,
)

from abc import ABC, abstractmethod
from typing import Any, List, Set
from pathlib import Path
from kstar_planner import planners
from concurrent.futures import TimeoutError
from pebble import ProcessPool

import tempfile

from nl2flow.utility.file_utility import open_atomic


class Planner(ABC):
    def __init__(self) -> None:
        self._timeout: float = TIMEOUT

    @property
    def timeout(self) -> float:
        return self._timeout

    @timeout.setter
    def timeout(self, set_timeout: float) -> None:
        self._timeout = set_timeout

    @abstractmethod
    def plan(self, pddl: PDDL, **kwargs: Any) -> PlannerResponse:
        pass

    @abstractmethod
    def parse(self, raw_plans: List[RawPlan], **kwargs: Any) -> List[Plan]:
        pass

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
    def pretty_print_plan(cls, plan: Plan, line_numbers: bool = True) -> str:
        pretty = ""

        for step, action in enumerate(plan.plan):
            if isinstance(action, Action):
                inputs = ", ".join(action.inputs) or None
                input_string = f"({inputs or ''})"

                outputs = ", ".join(action.outputs) or None
                output_string = f"{outputs} = " if outputs else ""

                pretty += f"{f'[{step}] ' if line_numbers else ''}{output_string}{action.name}{input_string}\n"

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


class Kstar(Planner):
    @staticmethod
    def call_to_planner(pddl: PDDL) -> RawPlannerResult:
        with tempfile.NamedTemporaryFile() as domain_temp, tempfile.NamedTemporaryFile() as problem_temp:
            domain_file = Path(tempfile.gettempdir()) / domain_temp.name
            problem_file = Path(tempfile.gettempdir()) / problem_temp.name

            with open_atomic(domain_file, "w") as domain_handle:
                domain_handle.write(pddl.domain)

            with open_atomic(problem_file, "w") as problem_handle:
                problem_handle.write(pddl.problem)

            planner_result = planners.plan_unordered_topq(
                domain_file=domain_file,
                problem_file=problem_file,
                quality_bound=QUALITY_BOUND,
                number_of_plans_bound=NUM_PLANS,
            )
            result = RawPlannerResult(list_of_plans=planner_result.get("plans", []))
            result.error_running_planner = False
            result.is_no_solution = len(result.list_of_plans) == 0
            result.is_timeout = False
            return result

    def raw_plan(self, pddl: PDDL) -> RawPlannerResult:
        pool = ProcessPool()
        cc = pool.schedule(self.call_to_planner, args=[pddl], timeout=self.timeout)

        # noinspection PyBroadException
        try:
            raw_planner_result: RawPlannerResult = cc.result()
            return raw_planner_result

        except TimeoutError as error:
            return RawPlannerResult(
                is_timeout=True,
                stderr=error,
            )

        except Exception as error:
            return RawPlannerResult(
                error_running_planner=True,
                is_timeout=False,
                stderr=error,
            )

    def plan(self, pddl: PDDL, **kwargs: Any) -> PlannerResponse:
        raw_planner_result = self.raw_plan(pddl)
        planner_response = PlannerResponse.initialize_from_raw_plans(raw_planner_result)
        # noinspection PyBroadException
        try:
            planner_response.list_of_plans = self.parse(raw_planner_result.list_of_plans, **kwargs)
            planner_response.is_parse_error = (
                len(planner_response.list_of_plans) == 0 and planner_response.is_no_solution is False
            )

            return planner_response

        except Exception as error:
            planner_response.is_parse_error = True
            planner_response.stderr = error
            return planner_response

    def parse(self, raw_plans: List[RawPlan], **kwargs: Any) -> List[Plan]:
        list_of_plans = list()

        flow: Flow = kwargs["flow"]
        slot_options: Set[SlotOptions] = flow.slot_options
        mapping_options: Set[MappingOptions] = flow.mapping_options
        confirm_options: Set[ConfirmOptions] = flow.confirm_options

        for plan in raw_plans:
            new_plan = Plan(cost=plan.cost, reference=plan.actions)
            actions = plan.actions

            for action in actions:
                action_split = action.split()
                action_name = revert_string_transform(action_split[0], kwargs["transforms"])

                if action_name is not None:
                    new_action = parse_action(action_name=action_name, parameters=action_split[1:], **kwargs)
                else:
                    raise ValueError("Could not parse action name.")

                if new_action:
                    new_plan.plan.append(new_action)

            if SlotOptions.group_slots in slot_options:
                new_plan = group_items(new_plan, SlotOptions.group_slots)

            if MappingOptions.group_maps in mapping_options:
                new_plan = group_items(new_plan, MappingOptions.group_maps)

            if ConfirmOptions.group_confirms in confirm_options:
                new_plan = group_items(new_plan, ConfirmOptions.group_confirms)

            new_plan.length = len(new_plan.plan)
            list_of_plans.append(new_plan)

        return list_of_plans
