from __future__ import annotations
from pydantic import BaseModel
from typing import List, Any, Optional

from nl2flow.compile.utils import string_transform, Transform
from nl2flow.compile.options import TypeOptions


class Parameter(BaseModel):
    item_id: str
    item_type: Optional[str]

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
    parameters: List[Parameter] = []

    @classmethod
    def transform(cls, step: Step, transforms: List[Transform]) -> Step:
        return Step(
            name=string_transform(step.name, transforms),
            parameters=[p.transform(p, transforms) for p in step.parameters],
        )


class HistoricalStep(Step):
    pass

    @classmethod
    def transform(
        cls, step: HistoricalStep, transforms: List[Transform]
    ) -> HistoricalStep:
        return HistoricalStep(
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
