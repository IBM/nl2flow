from nl2flow.plan.schemas import Step, ClassicalPlan as Plan, RawPlan
from typing import List, Optional, Union
from pydantic import BaseModel


class StoryConfig(BaseModel):
    ordered: bool = True
    optimal: bool = True
    partial: bool = False
    noise: bool = False


class Story(BaseModel):
    goal: List[str]
    plan: List[Step]


class StoryBoard(BaseModel):
    id: str
    story: Story
    reference: Union[Plan, RawPlan]
    parameters: List[str]
    config: StoryConfig


class Completion(BaseModel):
    raw: RawPlan
    plan: Plan


class PlanDiff(BaseModel):
    present: List[Union[Step, str]]
    absent: List[Union[Step, str]]


class ReferenceReport(BaseModel):
    same: bool
    equivalent: bool
    diff: Optional[PlanDiff]


class Report(BaseModel):
    id: str
    good: bool
    completion: Optional[Completion]
    valid: bool
    complete: bool
    optimal: Optional[bool]
    reference: ReferenceReport
