from nl2flow.plan.schemas import Step
from typing import List
from pydantic import BaseModel


class ClassicalPlanReference(BaseModel):
    plan: List[Step]


class Report(BaseModel):
    valid: bool
    complete: bool
    optimal: bool
    reference: ClassicalPlanReference
    plan_diff: List[str]
