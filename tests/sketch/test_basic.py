from tests.testing import BaseTestAgents
from pathlib import Path

# from nl2flow.plan.schemas import PlannerResponse
# from nl2flow.services.sketch import BasicSketchCompilation
from nl2flow.services.schemas.sketch_schemas import Sketch, Catalog

import yaml  # type: ignore
import os

FILEPATH = Path(__file__).parent.resolve()


class TestSketchBasic(BaseTestAgents):
    def setup_method(self) -> None:
        pass

    def test_parse_all_catalogs(self) -> None:
        path_to_catalog_files = Path.joinpath(FILEPATH, "sample_catalogs").resolve()

        for filename in os.listdir(path_to_catalog_files):
            path_to_new_catalog_file = Path.joinpath(path_to_catalog_files, filename).resolve()
            with open(path_to_new_catalog_file, "r") as new_catalog_file:
                catalog = yaml.safe_load(new_catalog_file)
                _ = Catalog(**catalog)

    def test_parse_all_sketches(self) -> None:
        path_to_sketch_files = Path.joinpath(FILEPATH, "sample_sketches").resolve()

        for filename in os.listdir(path_to_sketch_files):
            path_to_new_sketch_file = Path.joinpath(path_to_sketch_files, filename).resolve()
            with open(path_to_new_sketch_file, "r") as new_sketch_file:
                sketch = yaml.safe_load(new_sketch_file)
                _ = Sketch(**sketch)

    # def test_basic(self) -> None:
    #
    #     sketch_object = Sketch(**sketch)
    #     catalog_object = Catalog(**catalog)
    #     sketch_compilation = BasicSketchCompilation(name=sketch_object.sketch_name)
    #
    #     pddl, transforms = sketch_compilation.compile(sketch_object, catalog_object)
    #     raw_plans = self.planner.plan(pddl=pddl)
    #     planner_response: PlannerResponse = self.planner.parse(
    #         response=raw_plans, flow=sketch_compilation.flow, transforms=transforms
    #     )
    #
    #     print(self.planner.pretty_print(planner_response))
    #
    #     assert planner_response.list_of_plans, "There should be plans."
