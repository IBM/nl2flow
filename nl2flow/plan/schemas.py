from __future__ import annotations
from pydantic import BaseModel
from typing import List, Any, Optional, Union
from nl2flow.compile.schemas import Constraint


class Action(BaseModel):
    name: str
    parameters: List[str] = []
    inputs: List[str] = []
    outputs: List[str] = []


class ClassicalPlan(BaseModel):
    cost: float = 0.0
    length: float = 0.0
    metadata: Optional[Any] = None
    reference: List[str]
    plan: List[Union[Action, Constraint]] = []


class RawPlannerResult(BaseModel):
    list_of_plans: List[RawPlan] = []
    error_running_planner: Optional[bool] = None
    is_no_solution: Optional[bool] = None
    is_timeout: Optional[bool] = None
    stderr: Optional[Any] = None
    planner_output: Optional[str] = None
    planner_error: Optional[str] = None


class PlannerResponse(RawPlannerResult):
    list_of_plans: List[ClassicalPlan] = []
    is_parse_error: Optional[bool] = None

    @classmethod
    def initialize_from_raw_plans(cls, raw_planner_result: RawPlannerResult) -> PlannerResponse:
        return PlannerResponse(
            error_running_planner=raw_planner_result.error_running_planner,
            is_no_solution=raw_planner_result.is_no_solution,
            is_timeout=raw_planner_result.is_timeout,
            stderr=raw_planner_result.stderr,
        )


class RawPlan(BaseModel):
    actions: List[str]
    cost: float = 0.0
