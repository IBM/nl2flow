# from nl2flow.services.schemas.sketch_options import SketchOptions
from typing import List, Optional, Union
from pydantic import BaseModel


class Object(BaseModel):
    type: Optional[str]
    name: str


class Parameter(BaseModel):
    name: str
    value: str


class Goal(BaseModel):
    goal: str
    parameters: List[Parameter] = []


class Ordering(BaseModel):
    ordering: str


class Mapping(BaseModel):
    source: str
    target: str
    preference: float = 1.0


class Slot(BaseModel):
    name: str
    preference: float = 1.0


class Sketch(BaseModel):
    sketch_name: str
    utterances: List[str] = []
    options: List[str] = []
    objects: List[Object] = []
    components: List[Union[Goal, Ordering]] = []
    mapping: List[Mapping] = []
    slots: List[Slot] = []


class Constraint(BaseModel):
    constraint: str
    evaluate: str


class Signature(BaseModel):
    name: str
    type: Optional[str]


class Agent(BaseModel):
    id: str
    inputs: List[Union[Signature, Constraint]] = []
    outputs: List[Union[Signature, Constraint]] = []


class Catalog(BaseModel):
    catalog_name: str
    agents: List[Agent] = []
