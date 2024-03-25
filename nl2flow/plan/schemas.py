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


class PlannerResponse(BaseModel):
    list_of_plans: List[ClassicalPlan] = []


class RawPlan(BaseModel):
    actions: List[str]
    cost: float = 0.0


class RawPlannerResult(BaseModel):
    plans: List[RawPlan]
