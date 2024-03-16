from tests.sketch.test_basic import sketch_to_plan


class TestSketchAdvanced:
    def test_with_slots(self) -> None:
        planner_response = sketch_to_plan(catalog_name="catalog", sketch_name="01-simple_sketch")
        assert planner_response.list_of_plans, "There should be plans."

    def test_with_objects(self) -> None:
        planner_response = sketch_to_plan(catalog_name="catalog", sketch_name="01-simple_sketch")
        assert planner_response.list_of_plans, "There should be plans."

    def test_with_objects_and_mapping(self) -> None:
        planner_response = sketch_to_plan(catalog_name="catalog", sketch_name="01-simple_sketch")
        assert planner_response.list_of_plans, "There should be plans."

    def test_with_instantiated_goals(self) -> None:
        planner_response = sketch_to_plan(catalog_name="catalog", sketch_name="01-simple_sketch")
        assert planner_response.list_of_plans, "There should be plans."
