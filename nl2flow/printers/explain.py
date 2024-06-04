from nl2flow.printers.driver import Printer
from nl2flow.plan.schemas import ClassicalPlan as Plan
from nl2flow.compile.schemas import Step, Constraint
from typing import Any, Union


class ExplainPrint(Printer):
    @classmethod
    def pretty_print_plan(cls, plan: Plan, bulleted: bool = True, **kwargs: Any) -> str:
        raise NotImplementedError

    @classmethod
    def parse_token(cls, token: str, **kwargs: Any) -> Union[Step, Constraint, None]:
        raise NotImplementedError
