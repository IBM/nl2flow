from nl2flow.compile.schemas import Constraint
from nl2flow.compile.options import BasicOperations, ConstraintState
from nl2flow.plan.planners import Kstar
from nl2flow.services.sketch import BasicSketchCompilation
from tests.sketch.test_basic import sketch_to_plan, load_assets

PLANNER = Kstar()


class TestSketchAdvanced:
    def test_with_objects(self) -> None:
        planner_response = sketch_to_plan(catalog_name="catalog", sketch_name="03-sketch_with_objects")
        assert planner_response.list_of_plans, "There should be plans."

        for plan in planner_response.list_of_plans:
            assert plan.plan[-1].name == "Visa Application", "Plan ends with Visa Application agent."

    def test_with_slots(self) -> None:
        planner_response = sketch_to_plan(catalog_name="catalog", sketch_name="04-sketch_with_slots")
        assert planner_response.list_of_plans, "There should be plans."

        for plan in planner_response.list_of_plans:
            assert plan.plan[-1].name == "Workday", "Get letter from Workday."

            for step in plan.plan:
                if step.name == BasicOperations.SLOT_FILLER.value:
                    assert step.inputs[0].item_id == "w3", "Prefer to ask for w3."

                else:
                    assert step.name in {"W3 Agent", "Workday"}

    def test_with_objects_and_mapping(self) -> None:
        planner_response = sketch_to_plan(catalog_name="catalog", sketch_name="05-sketch_with_objects_and_mapping")
        assert planner_response.list_of_plans, "There should be plans."

        for plan in planner_response.list_of_plans:
            for step in plan.plan:
                if step.name == BasicOperations.MAPPER.value:
                    parameters = [i.item_id for i in step.inputs]
                    if "destination" in parameters:
                        assert (
                            "home" not in parameters and "address" not in parameters
                        ), "No mapping involving home, address to destination."

                    if "ticket to conference" in parameters:
                        assert "flight_ticket" in parameters

    def test_with_instantiated_goals(self) -> None:
        planner_response = sketch_to_plan(catalog_name="catalog", sketch_name="06-sketch_with_instantiated_goals")
        assert planner_response.list_of_plans, "There should be plans."

        for plan in planner_response.list_of_plans:
            assert len([step for step in plan.plan if step.name == "Taxi"]) == 4, "Four taxis."
            assert (
                len([step for step in plan.plan if step.name.startswith(BasicOperations.CONSTRAINT.value)]) == 2
            ), "Two constraint checks."

            for target in ["address", "destination"]:
                assert set(
                    [
                        step.inputs[0].item_id
                        for step in plan.plan
                        if step.name.startswith(BasicOperations.MAPPER.value) and step.inputs[1].item_id == target
                    ]
                ) == {
                    "BOS",
                    "LAX",
                    "JW Marriott Los Angeles LA 900 W Olympic Blvd",
                    "home",
                }

    def test_with_execution(self) -> None:
        catalog, sketch = load_assets(catalog_name="catalog", sketch_name="01-simple_sketch")

        sketch_compilation = BasicSketchCompilation(name=sketch.sketch_name)
        flow_object = sketch_compilation.compile_to_flow(sketch, catalog)

        flow_object.add(
            [
                Constraint(
                    constraint_id="is a business trip",
                    constraint="eval.state",
                    parameters=[],
                    truth_value=ConstraintState.FALSE.value,
                ),
            ]
        )

        planner_response = flow_object.plan_it(PLANNER)
        print(PLANNER.pretty_print(planner_response))

        assert planner_response.list_of_plans, "There should be plans."

        for plan in planner_response.list_of_plans:
            action_names = [step.name for step in plan.plan]
            assert "Kayak" in action_names and "Concur" not in action_names

            assert "check(is not a business trip) = True" in action_names
            assert (
                len([step.name for step in plan.plan if step.name.startswith(BasicOperations.CONSTRAINT.value)]) == 4
            ), "Extra checks for travel policy due to Kayak."
