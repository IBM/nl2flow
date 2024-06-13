from abc import ABC, abstractmethod
from typing import List, Any
from difflib import Differ
from nl2flow.plan.planners.kstar import Kstar
from nl2flow.plan.options import TIMEOUT
from nl2flow.plan.schemas import ClassicalPlan
from nl2flow.compile.flow import Flow
from nl2flow.compile.schemas import ClassicalPlanReference
from nl2flow.debug.schemas import Report, SolutionQuality, StepDiff, DiffAction
from nl2flow.printers.codelike import CodeLikePrint
from nl2flow.printers.driver import Printer

PLANNER = Kstar()
DIFFER = Differ()


class Debugger(ABC):
    def __init__(self, instance: Flow) -> None:
        self.flow = instance

    @abstractmethod
    def debug(
        self,
        list_of_tokens: List[str],
        debug: SolutionQuality,
        timeout: int = TIMEOUT,
        printer: Printer = CodeLikePrint(),
        **kwargs: Any,
    ) -> Report:
        pass

    @classmethod
    @abstractmethod
    def generate_plan_diff(
        cls, printer: Printer, plan: ClassicalPlan, list_of_tokens: List[str], **kwargs: Any
    ) -> List[str]:
        pass

    @classmethod
    @abstractmethod
    def generate_plan_diff_obj(cls, printer: Printer, diff_str: List[str]) -> List[StepDiff]:
        pass


class BasicDebugger(Debugger):
    @classmethod
    def generate_plan_diff(
        cls, printer: Printer, plan: ClassicalPlan, list_of_tokens: List[str], **kwargs: Any
    ) -> List[str]:
        plan_stringify = printer.pretty_print_plan(plan, line_numbers=False, **kwargs).split("\n")
        return list(DIFFER.compare(list_of_tokens, plan_stringify))

    @classmethod
    def generate_plan_diff_obj(cls, printer: Printer, diff_str: List[str], **kwargs: Any) -> List[StepDiff]:
        diff_obj = []
        for item in diff_str:
            item = item.strip()
            new_action = None
            for diff_action in DiffAction:
                if item.startswith(diff_action.value):
                    item = item.replace(f"{diff_action.value} ", "")
                    parsed_token = printer.parse_token(item, **kwargs) or item
                    new_action = StepDiff(
                        diff_type=diff_action,
                        step=parsed_token,
                    )

            if not new_action:
                parsed_token = printer.parse_token(item, **kwargs) or item
                new_action = StepDiff(
                    step=parsed_token,
                )

            diff_obj.append(new_action)

        return diff_obj

    def debug(
        self,
        list_of_tokens: List[str],
        debug: SolutionQuality,
        timeout: int = TIMEOUT,
        printer: Printer = CodeLikePrint(),
        **kwargs: Any,
    ) -> Report:
        PLANNER.timeout = timeout

        reference_plan: ClassicalPlanReference = printer.parse_tokens(list_of_tokens, **kwargs)
        self.flow.add(reference_plan)

        planner_response = self.flow.plan_it(PLANNER, debug_flag=debug)
        new_report = Report(
            report_type=debug.value,
            planner_response=planner_response,
            reference=reference_plan,
        )

        if len(planner_response.list_of_plans) > 0:
            best_plan = planner_response.list_of_plans[0]

            new_report.plan_diff_str = self.generate_plan_diff(printer, best_plan, list_of_tokens, **kwargs)
            new_report.plan_diff_obj = self.generate_plan_diff_obj(printer, new_report.plan_diff_str, **kwargs)

            new_report.determination = len([d for d in new_report.plan_diff_obj if d.diff_type is not None]) == 0

        return new_report
