from nl2flow.compile.schemas import Step, Constraint
from nl2flow.plan.schemas import PlannerResponse, ClassicalPlan as Plan
from abc import ABC, abstractmethod
from typing import Any, Union


class Printer(ABC):
    @classmethod
    @abstractmethod
    def pretty_print_plan(cls, plan: Plan, **kwargs: Any) -> str:
        pass

    @classmethod
    @abstractmethod
    def parse_token(cls, token: str) -> Union[Step, Constraint, None]:
        pass

    @classmethod
    def pretty_print(cls, planner_response: PlannerResponse, **kwargs: Any) -> str:
        pretty = ""

        for index, plan in enumerate(planner_response.list_of_plans):
            pretty += f"\n\n---- Plan #{index} ----\n"
            pretty += f"Cost: {plan.cost}, Length: {plan.length}\n\n"
            pretty += cls.pretty_print_plan(plan, **kwargs)

        return pretty
