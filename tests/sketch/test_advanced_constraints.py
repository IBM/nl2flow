from nl2flow.compile.schemas import Constraint, MemoryItem, Step
from nl2flow.compile.options import ConstraintState, MemoryState
from nl2flow.plan.planners import Kstar
from nl2flow.plan.schemas import PlannerResponse
from nl2flow.services.sketch import BasicSketchCompilation
from nl2flow.services.schemas.sketch_schemas import Sketch, Catalog
from tests.sketch.test_basic import load_assets
from copy import deepcopy

PLANNER = Kstar()


class TestSketchConstraints:
    @classmethod
    def check_sketch_with_execution(cls, catalog: Catalog, sketch: Sketch) -> PlannerResponse:
        sketch_compilation = BasicSketchCompilation(name=sketch.sketch_name)
        flow_object = sketch_compilation.compile_to_flow(sketch, catalog)

        planner_response = flow_object.plan_it(PLANNER)
        print(PLANNER.pretty_print(planner_response))

        assert planner_response.list_of_plans, "There should be plans."
        for plan in planner_response.list_of_plans:
            action_names = [step.name for step in plan.plan]
            index_of_visa_status_check_failure = action_names.index("assert not $visa.status == SUCCESS")

            assert index_of_visa_status_check_failure > -1
            assert action_names.index("Visa Application") < index_of_visa_status_check_failure
            assert action_names.index("Vacation Bot") > index_of_visa_status_check_failure
            assert action_names.index("Email Agent") > index_of_visa_status_check_failure

        new_flow_object = deepcopy(flow_object)
        new_flow_object.add(
            [
                MemoryItem(item_id="visa", item_state=MemoryState.KNOWN),
                Constraint(
                    constraint="$visa.status == SUCCESS",
                    truth_value=ConstraintState.FALSE.value,
                ),
            ],
        )

        planner_response = new_flow_object.plan_it(PLANNER)
        print(PLANNER.pretty_print(planner_response))

        assert planner_response.list_of_plans, "There should be plans."
        for plan in planner_response.list_of_plans:
            action_names = [step.name for step in plan.plan]

            assert "assert not $visa.status == SUCCESS" not in action_names, "No fresh visa check."
            assert "Trip Approval" not in action_names, "No approval step, manifest not approved."
            assert action_names.index("Vacation Bot") > -1, "Direct to vacation."
            assert action_names.index("Email Agent") > -1, "Direct to email."

        new_flow_object = deepcopy(flow_object)
        new_flow_object.add(
            [
                Step(name="Visa Application", parameters=["Passport", "address", "Employer Letter"]),
                MemoryItem(item_id="visa", item_state=MemoryState.KNOWN),
                Constraint(
                    constraint="$visa.status == SUCCESS",
                    truth_value=ConstraintState.TRUE.value,
                ),
            ],
        )

        planner_response = new_flow_object.plan_it(PLANNER)
        print(PLANNER.pretty_print(planner_response))

        assert planner_response.list_of_plans, "There should be plans."
        for plan in planner_response.list_of_plans:
            action_names = [step.name for step in plan.plan]

            assert action_names.index("Registration Bot") > action_names.index("Trip Approval"), "Explicit order."
            assert action_names.index("Trip Approval") > action_names.index("Concur"), "Explicit order."

            assert len([a for a in action_names if a.startswith("check(visa.status")]) == 0, "No visa checks"

        return planner_response

    def test_with_constraints(self) -> None:
        catalog, sketch = load_assets(catalog_name="catalog", sketch_name="07-sketch_with_constraints")
        final_planner_response = self.check_sketch_with_execution(catalog, sketch)

        for plan in final_planner_response.list_of_plans:
            assert plan.plan[-1].name == "assert not $approval.status == FAILED"

    def test_with_complex_goals(self) -> None:
        catalog, sketch = load_assets(catalog_name="catalog", sketch_name="08-sketch_with_complex_goals")
        final_planner_response = self.check_sketch_with_execution(catalog, sketch)

        for plan in final_planner_response.list_of_plans:
            assert plan.plan[-1].name == "assert $approval.status == SUCCESS"
