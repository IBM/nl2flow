from nl2flow.plan.schemas import PlannerResponse, ClassicalPlan as Plan
from nl2flow.compile.schemas import ClassicalPlanReference, Step, Constraint
from abc import ABC, abstractmethod
from typing import Any, List, Union


class Printer(ABC):
    @classmethod
    @abstractmethod
    def parse_token(cls, token: str, **kwargs: Any) -> Union[Step, Constraint, None]:
        pass

    @classmethod
    def parse_tokens(cls, list_of_tokens: List[str], **kwargs: Any) -> ClassicalPlanReference:
        parsed_plan = ClassicalPlanReference()

        for index, token in enumerate(list_of_tokens):
            new_action = cls.parse_token(token, **kwargs)

            if new_action:
                parsed_plan.plan.append(new_action)
            else:
                continue

        return parsed_plan

    @classmethod
    @abstractmethod
    def pretty_print_plan(cls, plan: Plan, **kwargs: Any) -> str:
        pass

    @classmethod
    def pretty_print(cls, planner_response: PlannerResponse, **kwargs: Any) -> str:
        pretty = ""

        for index, plan in enumerate(planner_response.list_of_plans):
            pretty += f"\n\n---- Plan #{index} ----\n"
            pretty += f"Cost: {plan.cost}, Length: {plan.length}\n\n"
            pretty += cls.pretty_print_plan(plan, **kwargs)

        return pretty
