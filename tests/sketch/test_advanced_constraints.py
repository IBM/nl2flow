from tests.sketch.test_basic import sketch_to_plan


class TestSketchConstraints:
    def test_with_constraints(self) -> None:
        planner_response = sketch_to_plan(catalog_name="catalog", sketch_name="07-sketch_with_constraints")
        assert planner_response.list_of_plans, "There should be plans."

    # def test_with_complex_goals(self) -> None:
    #     planner_response = sketch_to_plan(catalog_name="catalog", sketch_name="08-sketch_with_complex_goals")
    #     assert planner_response.list_of_plans, "There should be plans."
