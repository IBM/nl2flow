from nl2flow.compile.options import BasicOperations
from tests.sketch.test_basic import sketch_to_plan


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

    # def test_with_instantiated_goals(self) -> None:
    #     planner_response = sketch_to_plan(catalog_name="catalog", sketch_name="01-simple_sketch")
    #     assert planner_response.list_of_plans, "There should be plans."

    # def test_with_execution(self) -> None:
    #     planner_response = sketch_to_plan(catalog_name="catalog", sketch_name="01-simple_sketch")
    #     assert planner_response.list_of_plans, "There should be plans."
