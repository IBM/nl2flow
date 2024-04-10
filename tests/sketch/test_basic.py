from pathlib import Path
from typing import Tuple

import yaml  # type: ignore

from nl2flow.compile.options import BasicOperations
from nl2flow.plan.planners import Kstar
from nl2flow.plan.schemas import PlannerResponse
from nl2flow.services.sketch import BasicSketchCompilation
from nl2flow.services.schemas.sketch_schemas import Sketch, Catalog


FILEPATH = Path(__file__).parent.resolve()
PLANNER = Kstar()


def load_assets(catalog_name: str, sketch_name: str) -> Tuple[Catalog, Sketch]:
    path_to_new_catalog_file = Path.joinpath(FILEPATH, f"sample_catalogs/{catalog_name}.yaml").resolve()

    with open(path_to_new_catalog_file, "r") as new_catalog_file:
        catalog = yaml.safe_load(new_catalog_file)
        catalog_object = Catalog(**catalog)

    path_to_new_sketch_file = Path.joinpath(FILEPATH, f"sample_sketches/{sketch_name}.yaml").resolve()
    with open(path_to_new_sketch_file, "r") as new_sketch_file:
        sketch = yaml.safe_load(new_sketch_file)
        sketch_object = Sketch(**sketch)

    assert len(sketch_object.utterances) == 1
    assert len(sketch_object.descriptions) == 1

    return catalog_object, sketch_object


def sketch_to_plan(catalog_name: str, sketch_name: str) -> PlannerResponse:
    catalog, sketch = load_assets(catalog_name=catalog_name, sketch_name=sketch_name)

    sketch_compilation = BasicSketchCompilation(name=sketch.sketch_name)
    pddl, transforms = sketch_compilation.compile_to_pddl(sketch, catalog)

    planner_response = sketch_compilation.plan_it(pddl, transforms)
    print(PLANNER.pretty_print(planner_response))

    return planner_response


class TestSketchBasic:
    def test_basic(self) -> None:
        planner_response = sketch_to_plan(catalog_name="catalog", sketch_name="01-simple_sketch")
        self.check_basic_plan(planner_response)

    @staticmethod
    def check_basic_plan(planner_response: PlannerResponse) -> None:
        assert planner_response.list_of_plans, "There should be plans."

        for plan in planner_response.list_of_plans:
            action_names = [step.name for step in plan.plan]
            assert (
                len([a for a in action_names if a.startswith(BasicOperations.CONSTRAINT.value)]) == 2
            ), "Two constraint checks."

            assert [
                a.startswith(BasicOperations.CONSTRAINT.value) and "business trip" in a for a in action_names
            ].index(True) < action_names.index("Concur"), "Constraint check for business trip before Concur."

            travel_policy = "$hotel_booking.price + $flight_ticket.price < 150"
            assert [a.startswith(BasicOperations.CONSTRAINT.value) and travel_policy in a for a in action_names].index(
                True
            ) > action_names.index("Concur"), "Constraint check for travel policy after Concur."

            action_names = [
                a
                for a in action_names
                if a not in BasicOperations._value2member_map_ and not a.startswith(BasicOperations.CONSTRAINT.value)
            ]

            assert set(action_names) == {"Workday", "W3 Agent", "Visa Application", "Concur", "Trip Approval"}

    def test_with_order(self) -> None:
        planner_response = sketch_to_plan(catalog_name="catalog", sketch_name="02-simple_sketch_in_order")
        self.check_basic_plan(planner_response)

        for plan in planner_response.list_of_plans:
            action_names = [step.name for step in plan.plan]
            assert action_names.index("Visa Application") > action_names.index(
                "Trip Approval"
            ), "Visa application always occurs after Trip Approval."
