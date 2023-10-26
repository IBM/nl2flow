from tests.testing import BaseTestAgents

# from nl2flow.plan.schemas import PlannerResponse
# from nl2flow.services.sketch import BasicSketchCompilation
# from nl2flow.services.schemas.sketch_schemas import Sketch, Catalog

# import yaml
# import pytest

# with open("data/01-simple_sketch.yaml", "r") as sketch_file:
#     sketch = yaml.safe_load(sketch_file)
#
# with open("data/catalog.yaml", "r") as catalog_file:
#     catalog = yaml.safe_load(catalog_file)


class TestSketchBasic(BaseTestAgents):
    def setup_method(self) -> None:
        pass

    # @pytest.mark.skip(reason="Coming soon.")
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
