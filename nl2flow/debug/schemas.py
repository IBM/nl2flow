from nl2flow.plan.schemas import Step
from nl2flow.compile.schemas import Constraint
from typing import List, Optional, Union
from pydantic import BaseModel
from enum import Enum


class DiffAction(Enum):
    ADD = "ADD"
    DELETE = "DELETE"


class SolutionQuality(Enum):
    SOUND = "SOUND"
    VALID = "VALID"
    OPTIMAL = "OPTIMAL"


class ClassicalPlanReference(BaseModel):
    plan: List[Union[Step, Constraint]] = []


class StepDiff(BaseModel):
    diff_type: Optional[DiffAction] = None
    step: Step


class Report(BaseModel):
    report_type: SolutionQuality
    determination: Optional[bool] = None
    reference: Optional[ClassicalPlanReference] = None
    plan_diff: List[StepDiff] = []
