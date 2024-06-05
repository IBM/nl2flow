from nl2flow.printers.verbalize import VerbalizePrint
from nl2flow.plan.schemas import ClassicalPlan as Plan
from typing import Any


class ExplainPrint(VerbalizePrint):
    @classmethod
    def pretty_print_plan(cls, plan: Plan, bulleted: bool = True, **kwargs: Any) -> str:
        raise NotImplementedError
