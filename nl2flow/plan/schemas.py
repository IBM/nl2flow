from pydantic import BaseModel
from typing import List, Any, Optional


class Parameter(BaseModel):
    name: str
    type: str


class Action(BaseModel):
    name: str
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
