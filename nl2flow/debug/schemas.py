from nl2flow.plan.schemas import PlannerResponse
from nl2flow.compile.schemas import Step, ClassicalPlanReference, Constraint
from typing import List, Optional, Union
from pydantic import BaseModel
from enum import Enum


class DiffAction(str, Enum):
    ADD = "+"
    DELETE = "-"


class SolutionQuality(str, Enum):
    SOUND = "SOUND"
    VALID = "VALID"
    OPTIMAL = "OPTIMAL"


class StepDiff(BaseModel):
    diff_type: Optional[DiffAction] = None
    step: Union[Step, Constraint, str]


class Report(BaseModel):
    report_type: SolutionQuality
    determination: Optional[bool] = None
    planner_response: PlannerResponse
    reference: Optional[ClassicalPlanReference] = None
    plan_diff_obj: List[StepDiff] = []
    plan_diff_str: List[str] = []
