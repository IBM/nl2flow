from abc import ABC, abstractmethod
from typing import Union

from nl2flow.plan.schemas import RawPlan
from nl2flow.compile.schemas import PDDL
from nl2flow.compile.flow import Flow
from nl2flow.debug.schemas import ClassicalPlanReference


class Debugger(ABC):
    def __init__(self, instance: Union[Flow, PDDL]) -> None:
        if isinstance(instance, Flow):
            self.flow = instance
            self.pddl = instance.compile_to_pddl()

        elif isinstance(instance, PDDL):
            self.flow = None
            self.pddl = instance

        else:
            raise ValueError(f"Debugger must initiated with a Flow or PDDL object, found {type(instance)} instead.")

    @abstractmethod
    def debug_raw_plan(self, raw_plan: RawPlan) -> None:
        pass

    @abstractmethod
    def debug(self, plan: ClassicalPlanReference) -> None:
        pass


class BasicDebugger(Debugger):
    def debug_raw_plan(self, raw_plan: RawPlan) -> None:
        raise NotImplementedError

    def debug(self, plan: ClassicalPlanReference) -> None:
        pass
