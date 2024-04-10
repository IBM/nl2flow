from nl2flow.compile.flow import Flow
from nl2flow.compile.utils import revert_string_transform
from nl2flow.plan.schemas import RawPlannerResult, RawPlan, PlannerResponse, ClassicalPlan as Plan
from nl2flow.plan.options import QUALITY_BOUND, NUM_PLANS, TIMEOUT
from nl2flow.plan.utils import parse_action, group_items
from nl2flow.compile.schemas import PDDL
from nl2flow.compile.options import (
    SlotOptions,
    MappingOptions,
    ConfirmOptions,
)

from abc import ABC, abstractmethod
from typing import Any, List, Set, Dict
from pathlib import Path
from kstar_planner import planners
from concurrent.futures import TimeoutError
from pebble import ProcessPool

import tempfile


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
    def plan(self, pddl: PDDL, **kwargs: Dict[str, Any]) -> PlannerResponse:
        pass

    @abstractmethod
    def parse(self, raw_plans: List[RawPlan], **kwargs: Any) -> List[Plan]:
        pass

    @classmethod
    def pretty_print_plan(cls, plan: Plan) -> str:
        pretty = ""

        for step, action in enumerate(plan.plan):
            inputs = ", ".join([item.item_id for item in action.inputs]) or None
            input_string = f"({inputs})" if inputs else ""

            outputs = ", ".join([item.item_id for item in action.outputs]) or None
            output_string = f" -> {outputs}" if outputs else ""

            pretty += f"[{step}] {action.name}{input_string}{output_string}\n"

        return pretty.strip()

    @classmethod
    def pretty_print_plan_verbose(cls, plan: Plan) -> str:
        pretty = ""

        for step, action in enumerate(plan.plan):
            inputs = ", ".join([f"{item.item_id} ({item.item_type})" for item in action.inputs])
            outputs = ", ".join([f"{item.item_id} ({item.item_type})" for item in action.outputs])

            pretty += (
                f"Step {step}: {action.name}, "
                f"Inputs: {inputs if action.inputs else None}, "
                f"Outputs: {outputs if action.outputs else None}\n"
            )

        return pretty.strip()

    @classmethod
    def pretty_print(cls, planner_response: PlannerResponse, verbose: bool = False) -> str:
        pretty = ""

        for index, plan in enumerate(planner_response.list_of_plans):
            pretty += f"\n\n---- Plan #{index} ----\n"
            pretty += f"Cost: {plan.cost}, Length: {plan.length}\n\n"
            pretty += cls.pretty_print_plan(plan) if not verbose else cls.pretty_print_plan_verbose(plan)

        return pretty


class Kstar(Planner):
    @staticmethod
    def call_to_planner(pddl: PDDL) -> RawPlannerResult:
        with tempfile.NamedTemporaryFile() as domain_temp, tempfile.NamedTemporaryFile() as problem_temp:
            domain_file = Path(tempfile.gettempdir()) / domain_temp.name
            problem_file = Path(tempfile.gettempdir()) / problem_temp.name

            domain_file.write_text(pddl.domain)
            problem_file.write_text(pddl.problem)

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
