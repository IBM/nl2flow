from nl2flow.plan.schemas import PlannerResponse
from nl2flow.compile.schemas import Step, ClassicalPlanReference, Constraint
from typing import List, Optional, Union
from pydantic import BaseModel
from enum import Enum, auto


class DiffAction(str, Enum):
    ADD = "+"
    DELETE = "-"


class DebugFlag(str, Enum):
    DIRECT = auto()
    TOKENIZE = auto()


class SolutionQuality(str, Enum):
    SOUND = "SOUND"
    VALID = "VALID"
    OPTIMAL = "OPTIMAL"


class StepDiff(BaseModel):
    diff_type: Optional[DiffAction] = None
    step: Union[Step, Constraint, str]


class Report(BaseModel):
    report_type: SolutionQuality = SolutionQuality.SOUND
    determination: Optional[bool] = None
    planner_response: PlannerResponse = PlannerResponse()
    reference: Optional[ClassicalPlanReference] = None
    plan_diff_obj: List[StepDiff] = []
    plan_diff_str: List[str] = []
