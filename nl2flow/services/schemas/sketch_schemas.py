from __future__ import annotations
from typing import List, Optional, Union
from pydantic import BaseModel
from nl2flow.compile.schemas import Constraint


class Parameter(BaseModel):
    name: str
    value: Optional[str] = None
    target: Optional[str] = None


class Goal(BaseModel):
    item: str
    parameters: List[Parameter] = []


class Disjunction(BaseModel):
    OR: List[Union[Goal, Condition]]


class Ordering(BaseModel):
    order: str


class Condition(BaseModel):
    condition: str
    if_outcomes: List[Union[Goal, Condition]] = []
    else_outcomes: List[Union[Goal, Condition]] = []


class Mapping(BaseModel):
    source: str
    target: str
    goodness: float = 1.0


class Slot(BaseModel):
    name: str
    goodness: float = 1.0


class Sketch(BaseModel):
    sketch_name: str
    utterances: List[str] = []
    descriptions: List[str] = []
    options: List[str] = []
    components: List[Union[Goal, Condition, Disjunction, Ordering]] = []
    mappings: List[Mapping] = []
    slots: List[Slot] = []


class Signature(BaseModel):
    name: str
    type: Optional[str] = None


class Agent(BaseModel):
    id: str
    inputs: List[Union[Signature, Constraint]] = []
    outputs: List[Union[Signature, Constraint]] = []


class Catalog(BaseModel):
    catalog_name: str
    agents: List[Agent] = []
