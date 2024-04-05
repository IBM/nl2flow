from __future__ import annotations
from pydantic import BaseModel
from typing import List, Any, Optional, Union

from nl2flow.compile.utils import string_transform, Transform
from nl2flow.compile.options import TypeOptions


class Parameter(BaseModel):
    item_id: str
    item_type: Optional[str] = None

    @classmethod
    def transform(cls, parameter: Parameter, transforms: List[Transform]) -> Parameter:
        return Parameter(
            item_id=string_transform(parameter.item_id, transforms),
            item_type=string_transform(parameter.item_type, transforms)
            if parameter.item_type is not None
            else TypeOptions.ROOT.value,
        )


class Step(BaseModel):
    name: str
    parameters: List[Union[Parameter, str]] = []

    @classmethod
    def transform(cls, step: Step, transforms: List[Transform]) -> Step:
        parameters = [p if isinstance(p, Parameter) else Parameter(item_id=p) for p in step.parameters]
        return Step(
            name=string_transform(step.name, transforms),
            parameters=[p.transform(p, transforms) for p in parameters],
        )


class Action(Step):
    inputs: List[Parameter] = []
    outputs: List[Parameter] = []


class ClassicalPlan(BaseModel):
    cost: float = 0.0
    length: float = 0.0
    metadata: Optional[Any] = None
    reference: List[str]
    plan: List[Action] = []


class RawPlannerResult(BaseModel):
    list_of_plans: List[RawPlan] = []
    error_running_planner: Optional[bool] = None
    is_no_solution: Optional[bool] = None
    is_timeout: Optional[bool] = None
    stderr: Optional[Any] = None


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
