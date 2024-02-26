from pathlib import Path
from typing import Tuple

import yaml  # type: ignore

from nl2flow.plan.planners import Kstar
from nl2flow.services.sketch import BasicSketchCompilation
from nl2flow.services.schemas.sketch_schemas import Sketch, Catalog


FILEPATH = Path(__file__).parent.resolve()


class TestSketchBasic:
    planner = Kstar()

    @staticmethod
    def load_assets(catalog_name: str, sketch_name: str) -> Tuple[Catalog, Sketch]:
        path_to_new_catalog_file = Path.joinpath(FILEPATH, f"sample_catalogs/{catalog_name}.yaml").resolve()

        with open(path_to_new_catalog_file, "r") as new_catalog_file:
            catalog = yaml.safe_load(new_catalog_file)
            catalog_object = Catalog(**catalog)

        path_to_new_sketch_file = Path.joinpath(FILEPATH, f"sample_sketches/{sketch_name}.yaml").resolve()
        with open(path_to_new_sketch_file, "r") as new_sketch_file:
            sketch = yaml.safe_load(new_sketch_file)
            sketch_object = Sketch(**sketch)

        return catalog_object, sketch_object

    def test_basic(self) -> None:
        catalog, sketch = self.load_assets(catalog_name="catalog", sketch_name="01-simple_sketch")

        sketch_compilation = BasicSketchCompilation(name=sketch.sketch_name)
        pddl, transforms = sketch_compilation.compile(sketch, catalog)

        planner_response = sketch_compilation.plan_it(pddl, transforms)
        print(self.planner.pretty_print(planner_response))

        assert planner_response.list_of_plans, "There should be plans."
