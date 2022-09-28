from nl2flow.compile.schemas import FlowDefinition, PDDL
from abc import ABC, abstractmethod
from typing import Dict, Any


class Compilation(ABC):
    def __init__(self, flow_definition: FlowDefinition):
        self.flow_definition = flow_definition

    @abstractmethod
    def compile(self, **kwargs: Dict[str, Any]) -> PDDL:
        pass


class ClassicPDDL(Compilation):
    def compile(self, **kwargs: Dict[str, Any]) -> PDDL:
        pass
