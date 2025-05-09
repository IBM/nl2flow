from __future__ import annotations
from pydantic import BaseModel
from typing import List, Any, Optional, Union
from nl2flow.compile.schemas import Constraint, ClassicalPlanReference, Step, Parameter


class Action(BaseModel):
    name: str
    parameters: List[str] = []
    inputs: List[str] = []
    outputs: List[str] = []

    @classmethod
    def from_reference(cls, reference: Step) -> Action:
        inputs = (
            reference.maps
            if len(reference.maps) > 0
            else [item.item_id if isinstance(item, Parameter) else item for item in reference.parameters]
        )

        return Action(
            name=reference.name,
            inputs=inputs,
        )


class ClassicalPlan(BaseModel):
    cost: float = 0.0
    length: float = 0.0
    metadata: Optional[Any] = None
    reference: List[str] = []
    plan: List[Union[Action, Constraint]] = []

    @classmethod
    def from_reference(cls, reference: ClassicalPlanReference) -> ClassicalPlan:
        new_plan = [Action.from_reference(item) if isinstance(item, Step) else item for item in reference.plan]

        return ClassicalPlan(
            plan=new_plan,
            length=len(new_plan),
        )


class RawPlannerResult(BaseModel):
    list_of_plans: List[RawPlan] = []
    error_running_planner: Optional[bool] = None
    is_no_solution: Optional[bool] = None
    no_plan_needed: Optional[bool] = None
    is_timeout: Optional[bool] = None
    stderr: Optional[Any] = None
    planner_output: Optional[str] = None
    planner_error: Optional[str] = None

    @property
    def best_plan(self) -> Optional[RawPlan]:
        if self.list_of_plans:
            return self.list_of_plans[0]

        return None


class PlannerResponse(RawPlannerResult):
    list_of_plans: List[ClassicalPlan] = []
    is_parse_error: Optional[bool] = None

    @property
    def best_plan(self) -> Optional[ClassicalPlan]:
        if self.list_of_plans:
            return self.list_of_plans[0]

        return None

    @classmethod
    def initialize_from_raw_plans(cls, raw_planner_result: RawPlannerResult) -> PlannerResponse:
        return PlannerResponse(
            error_running_planner=raw_planner_result.error_running_planner,
            is_no_solution=raw_planner_result.is_no_solution,
            no_plan_needed=raw_planner_result.no_plan_needed,
            is_timeout=raw_planner_result.is_timeout,
            stderr=raw_planner_result.stderr,
        )


class RawPlan(BaseModel):
    actions: List[str]
    cost: float = 0.0
