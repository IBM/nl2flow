from __future__ import annotations
from pydantic import BaseModel
from typing import List, Any, Optional

from nl2flow.compile.utils import string_transform, Transform


class Parameter(BaseModel):
    name: str
    type: str

    @classmethod
    def transform(cls, parameter: Parameter, transforms: List[Transform]) -> Step:
        return Parameter(
            name=string_transform(parameter.name, transforms),
            type=string_transform(parameter.type, transforms),
        )


class Step(BaseModel):
    name: str
    parameters: List[Parameter] = []

    @classmethod
    def transform(cls, step: Step, transforms: List[Transform]) -> Step:
        return Step(
            name=string_transform(step.name, transforms),
            parameters=[p.transform(p, transforms) for p in step.parameters],
        )


class Action(Step):
    inputs: List[Parameter] = []
    outputs: List[Parameter] = []


class ClassicalPlan(BaseModel):
    cost: float
    length: float
    metadata: Optional[Any]
    plan: List[Action] = []


class PlannerResponse(BaseModel):
    metadata: Any
    list_of_plans: List[ClassicalPlan] = []
