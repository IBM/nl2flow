from nl2flow.plan.schemas import RawPlannerResult, PlannerResponse
from nl2flow.plan.options import QUALITY_BOUND, NUM_PLANS
from nl2flow.compile.schemas import PDDL
from typing import Any
from pathlib import Path
from kstar_planner import planners

from nl2flow.utility.file_utility import open_atomic
from nl2flow.plan.planner import Planner, FDDerivedPlanner

import tempfile


class Kstar(Planner, FDDerivedPlanner):
    def __call_to_planner(self, pddl: PDDL) -> RawPlannerResult:
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
                timeout=self.timeout,
                quality_bound=QUALITY_BOUND,
                number_of_plans_bound=NUM_PLANS,
            )
            result = RawPlannerResult(list_of_plans=planner_result.get("plans", []))
            result.error_running_planner = False
            result.is_no_solution = planner_result.get("unsolvable", None)
            result.is_timeout = planner_result.get("timeout_triggered", None)
            result.planner_output = planner_result.get("planner_output")
            result.planner_error = planner_result.get("planner_error")
            return result

    def raw_plan(self, pddl: PDDL) -> RawPlannerResult:
        # noinspection PyBroadException
        try:
            raw_planner_result = self.__call_to_planner(pddl)
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

            planner_response = self.post_process(planner_response, **kwargs)
            return planner_response

        except Exception as error:
            planner_response.is_parse_error = True
            planner_response.stderr = error
            return planner_response
