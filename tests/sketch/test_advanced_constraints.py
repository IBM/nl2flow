# from nl2flow.compile.schemas import Constraint, MemoryItem
# from nl2flow.compile.options import ConstraintState, MemoryState
from nl2flow.plan.planners import Kstar
from nl2flow.services.sketch import BasicSketchCompilation
from tests.sketch.test_basic import load_assets

PLANNER = Kstar()


class TestSketchConstraints:
    def test_with_constraints(self) -> None:
        catalog, sketch = load_assets(catalog_name="catalog", sketch_name="07-sketch_with_constraints")

        sketch_compilation = BasicSketchCompilation(name=sketch.sketch_name)
        flow_object = sketch_compilation.compile_to_flow(sketch, catalog)

        planner_response = flow_object.plan_it(PLANNER)
        print(PLANNER.pretty_print(planner_response))

        assert planner_response.list_of_plans, "There should be plans."

        for plan in planner_response.list_of_plans:
            action_names = [step.name for step in plan.plan]
            assert action_names.index("check(visa.status == SUCCESS) = False") > -1

            # if "Registration Bot" in action_names:
            #     assert action_names.index("Registration Bot") > action_names.index("Trip Approval"), "Explicit order."
            #
            # if "Trip Approval" in action_names:
            #     assert action_names.index("Visa Application") < action_names.index(
            #         "Trip Approval"
            #     ), "Implicit order due to constraint."

        # flow_object.add(
        #     [
        #         MemoryItem(item_id="visa", item_state=MemoryState.KNOWN),
        #         Constraint(
        #             constraint_id="visa.status == SUCCESS",
        #             constraint="visa.status == SUCCESS",
        #             parameters=["visa"],
        #             truth_value=ConstraintState.FALSE.value,
        #         ),
        #     ],
        # )

        # flow_object.add(
        #     [
        #         MemoryItem(item_id="visa", item_state=MemoryState.KNOWN),
        #         MemoryItem(item_id="approval", item_state=MemoryState.KNOWN),
        #         Constraint(
        #             constraint_id="visa.status == SUCCESS",
        #             constraint="visa.status == SUCCESS",
        #             parameters=["visa"],
        #             truth_value=ConstraintState.FALSE.value,
        #         ),
        #         Constraint(
        #             constraint_id="approval.status == FAILURE",
        #             constraint="approval.status == FAILURE",
        #             parameters=["visa"],
        #             truth_value=ConstraintState.TRUE.value,
        #         ),
        #     ],
        # )

        # planner_response = flow_object.plan_it(PLANNER)
        # print(PLANNER.pretty_print(planner_response))
        #
        # assert planner_response.list_of_plans, "There should be plans."

    # def test_with_complex_goals(self) -> None:
    #     planner_response = sketch_to_plan(catalog_name="catalog", sketch_name="08-sketch_with_complex_goals")
    #     assert planner_response.list_of_plans, "There should be plans."
