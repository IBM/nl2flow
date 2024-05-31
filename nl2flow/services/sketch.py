from nl2flow.compile.flow import Flow
from nl2flow.compile.schemas import PDDL, Transform
from nl2flow.compile.options import SlotOptions, MappingOptions
from nl2flow.plan.schemas import PlannerResponse
from nl2flow.plan.planners.kstar import Kstar

from nl2flow.services.schemas.sketch_schemas import Sketch, Catalog
from nl2flow.services.schemas.sketch_options import SketchOptions
from nl2flow.services.compilations.catalog_compilations import basic_catalog_compilation
from nl2flow.services.compilations.sketch_compilations import basic_sketch_compilation

from abc import ABC, abstractmethod
from typing import Set, Tuple, List


class SketchCompilation(ABC):
    def __init__(self, name: str) -> None:
        self.sketch = Sketch(sketch_name=name)
        self.flow = Flow(name=name)
        self.flow.slot_options.add(SlotOptions.ordered)
        self.flow.mapping_options.add(MappingOptions.transitive)
        self._options: Set[SketchOptions] = set()

    @property
    def options(self) -> Set[SketchOptions]:
        return self._options

    @options.setter
    def options(self, options: Set[SketchOptions]) -> None:
        self._options = options

    @abstractmethod
    def compile_to_flow(self, sketch: Sketch, catalog: Catalog) -> Flow:
        pass

    @abstractmethod
    def compile_to_pddl(self, sketch: Sketch, catalog: Catalog) -> Tuple[PDDL, List[Transform]]:
        pass

    def plan_it(self, pddl: PDDL, transforms: List[Transform]) -> PlannerResponse:
        planner = Kstar()
        parsed_plans: PlannerResponse = planner.plan(pddl=pddl, flow=self.flow, transforms=transforms)
        return parsed_plans


class BasicSketchCompilation(SketchCompilation):
    def compile_to_flow(self, sketch: Sketch, catalog: Catalog) -> Flow:
        basic_catalog_compilation(self.flow, catalog)
        basic_sketch_compilation(self.flow, sketch, catalog)
        return self.flow

    def compile_to_pddl(self, sketch: Sketch, catalog: Catalog) -> Tuple[PDDL, List[Transform]]:
        self.compile_to_flow(sketch, catalog)
        pddl, transforms = self.flow.compile_to_pddl()
        return pddl, transforms
