from tests.testing import BaseTestAgents
from tests.goals.test_and_or_goals import (
    set_up_agents,
    add_extra_items_to_setup,
    number_of_optimal_plans,
)

from nl2flow.plan.schemas import PlannerResponse
from nl2flow.compile.options import GoalType, GoalOptions, SlotOptions
from nl2flow.compile.schemas import GoalItems, GoalItem


class TestOrAndGoals(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)
        self.flow.goal_type = GoalOptions.OR_AND
        self.flow.slot_options.add(SlotOptions.last_resort)

    def test_or_and_basic(self) -> None:
        set_up_agents(self)

        self.flow.add(
            [
                GoalItems(goals=[GoalItem(goal_name="Agent X"), GoalItem(goal_name="Agent Y")]),
                GoalItems(goals=[GoalItem(goal_name="Agent A"), GoalItem(goal_name="Agent B")]),
            ]
        )

        plans = self.get_plan()
        self.simple_or_and_plan(plans)

    @staticmethod
    def simple_or_and_plan(plans: PlannerResponse) -> None:
        assert plans.list_of_plans, "There should be plans."
        num_plans = number_of_optimal_plans(plans)

        for poi in plans.list_of_plans[:num_plans]:
            operator_names = {operator.name for operator in poi.plan}
            assert operator_names.issuperset({"Agent X", "Agent Y"}) or operator_names.issuperset(
                {"Agent A", "Agent B"}
            ), "One of X and Y or A and B."

    @staticmethod
    def extra_preference_check(plans: PlannerResponse) -> None:
        expected_number_of_optimal_plans = 1
        assert number_of_optimal_plans(plans) == expected_number_of_optimal_plans, "Only one plan left."

        for poi in plans.list_of_plans[:expected_number_of_optimal_plans]:
            operator_names = {operator.name for operator in poi.plan}
            assert len(operator_names.intersection({"Agent A", "Agent B"})) == 0, "None of A and B."

    def test_or_and_with_type_known(self) -> None:
        set_up_agents(self)

        self.flow.add(
            [
                GoalItems(
                    goals=[
                        GoalItem(goal_name="output-type-x", goal_type=GoalType.OBJECT_KNOWN),
                        GoalItem(goal_name="output-type-y", goal_type=GoalType.OBJECT_KNOWN),
                    ]
                ),
                GoalItems(
                    goals=[
                        GoalItem(goal_name="output-type-a", goal_type=GoalType.OBJECT_KNOWN),
                        GoalItem(goal_name="output-type-b", goal_type=GoalType.OBJECT_KNOWN),
                    ]
                ),
            ]
        )

        plans = self.get_plan()
        self.simple_or_and_plan(plans)

        assert number_of_optimal_plans(plans) == 2, "Two selection of objects."
        add_extra_items_to_setup(self, set_agents=["A", "B"])

        plans = self.get_plan()
        self.simple_or_and_plan(plans)
        self.extra_preference_check(plans)

    def test_or_and_with_object_known(self) -> None:
        set_up_agents(self)

        self.flow.add(
            [
                GoalItems(
                    goals=[
                        GoalItem(goal_name="output-x", goal_type=GoalType.OBJECT_KNOWN),
                        GoalItem(goal_name="output-y", goal_type=GoalType.OBJECT_KNOWN),
                    ]
                ),
                GoalItems(
                    goals=[
                        GoalItem(goal_name="output-a", goal_type=GoalType.OBJECT_KNOWN),
                        GoalItem(goal_name="output-b", goal_type=GoalType.OBJECT_KNOWN),
                    ]
                ),
            ]
        )

        plans = self.get_plan()
        self.simple_or_and_plan(plans)

        assert number_of_optimal_plans(plans) == 2, "Two selection of objects."

    def test_or_and_with_type_used(self) -> None:
        set_up_agents(self)

        self.flow.add(
            [
                GoalItems(
                    goals=[
                        GoalItem(goal_name="input-type-x", goal_type=GoalType.OBJECT_USED),
                        GoalItem(goal_name="input-type-y", goal_type=GoalType.OBJECT_USED),
                    ]
                ),
                GoalItems(
                    goals=[
                        GoalItem(goal_name="input-type-a", goal_type=GoalType.OBJECT_USED),
                        GoalItem(goal_name="input-type-b", goal_type=GoalType.OBJECT_USED),
                    ]
                ),
            ]
        )

        plans = self.get_plan()
        self.simple_or_and_plan(plans)

        assert number_of_optimal_plans(plans) == 2, "Two selection of objects."
        add_extra_items_to_setup(self, set_agents=["A", "B"])

        plans = self.get_plan()
        self.simple_or_and_plan(plans)
        self.extra_preference_check(plans)

    def test_or_and_with_object_used(self) -> None:
        set_up_agents(self)

        self.flow.add(
            GoalItems(
                goals=[
                    GoalItem(goal_name="x_2", goal_type=GoalType.OBJECT_USED),
                    GoalItem(goal_name="y_3", goal_type=GoalType.OBJECT_USED),
                ]
            )
        )

        self.flow.add(
            GoalItems(
                goals=[
                    GoalItem(goal_name="a_0", goal_type=GoalType.OBJECT_USED),
                    GoalItem(goal_name="b_1", goal_type=GoalType.OBJECT_USED),
                ]
            )
        )

        plans = self.get_plan()
        self.simple_or_and_plan(plans)

        assert number_of_optimal_plans(plans) == 2, "Two selection of objects."
