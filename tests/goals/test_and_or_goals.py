from tests.testing import BaseTestAgents
from typing import List
from nl2flow.plan.schemas import PlannerResponse
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.options import (
    SlotOptions,
    GoalType,
    GoalOptions,
)
from nl2flow.compile.schemas import (
    Parameter,
    MemoryItem,
    SignatureItem,
    GoalItems,
    GoalItem,
)


def number_of_optimal_plans(plans: PlannerResponse) -> int:
    return len([plan for plan in plans.list_of_plans if plan.cost == plans.list_of_plans[0].cost])


def set_up_agents(test_class: BaseTestAgents) -> None:
    test_ids = ["A", "B", "X", "Y"]
    for index, item in enumerate(test_ids):
        agent = Operator(f"Agent {item}")
        item = item.lower()

        agent.add_input(SignatureItem(parameters=[Parameter(item_id=f"input-{item}", item_type=f"input-type-{item}")]))

        agent.add_output(
            SignatureItem(parameters=[Parameter(item_id=f"output-{item}", item_type=f"output-type-{item}")])
        )

        test_class.flow.add(
            [
                agent,
                MemoryItem(
                    item_id=f"{item}_{index}",
                    item_type=f"input-type-{item}",
                ),
            ]
        )


def add_extra_items_to_setup(test_class: BaseTestAgents, set_agents: List[str]) -> None:
    for index, item in enumerate(set_agents):
        item = item.lower()

        test_class.flow.add(
            [
                MemoryItem(
                    item_id=f"{item}_{index}_secondary_input",
                    item_type=f"input-type-{item}",
                ),
                MemoryItem(
                    item_id=f"{item}_{index}_secondary_output",
                    item_type=f"output-type-{item}",
                ),
            ]
        )


class TestAndOrGoals(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)
        self.flow.goal_type = GoalOptions.AND_OR
        self.flow.slot_options.add(SlotOptions.last_resort)

    def test_and_or_basic(self) -> None:
        set_up_agents(self)

        self.flow.add(
            [
                GoalItems(goals=[GoalItem(goal_name="Agent X"), GoalItem(goal_name="Agent Y")]),
                GoalItems(goals=[GoalItem(goal_name="Agent A"), GoalItem(goal_name="Agent B")]),
            ]
        )

        plans = self.get_plan()
        self.simple_and_or_plan(plans)

    @staticmethod
    def simple_and_or_plan(plans: PlannerResponse) -> None:
        assert plans.list_of_plans, "There should be plans."
        num_plans = number_of_optimal_plans(plans)

        for poi in plans.list_of_plans[:num_plans]:
            operator_names = {operator.name for operator in poi.plan}
            assert len(operator_names.intersection({"Agent X", "Agent Y"})) == 1, "One from X and Y."
            assert len(operator_names.intersection({"Agent A", "Agent B"})) == 1, "One from A and B."

    @staticmethod
    def extra_preference_check(plans: PlannerResponse) -> None:
        expected_number_of_optimal_plans = 1
        assert number_of_optimal_plans(plans) == expected_number_of_optimal_plans, "One cheaper combinations left."

        for poi in plans.list_of_plans[:expected_number_of_optimal_plans]:
            operator_names = {operator.name for operator in poi.plan}
            assert len(operator_names.intersection({"Agent B", "Agent Y"})) == 0, "None of B and Y."

    def test_and_or_with_type_known(self) -> None:
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
        self.simple_and_or_plan(plans)

        assert number_of_optimal_plans(plans) == 4, "Four combinations of test ids."
        add_extra_items_to_setup(self, set_agents=["B", "Y"])

        plans = self.get_plan()
        self.simple_and_or_plan(plans)
        self.extra_preference_check(plans)

    def test_and_or_with_object_known(self) -> None:
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
        self.simple_and_or_plan(plans)

        assert number_of_optimal_plans(plans) == 4, "Four combinations of test ids."

    def test_and_or_with_type_used(self) -> None:
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
        self.simple_and_or_plan(plans)

        assert number_of_optimal_plans(plans) == 4, "Four combinations of test ids."
        add_extra_items_to_setup(self, set_agents=["B", "Y"])

        plans = self.get_plan()
        self.simple_and_or_plan(plans)
        self.extra_preference_check(plans)

    def test_and_or_with_object_used(self) -> None:
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
        self.simple_and_or_plan(plans)

        assert number_of_optimal_plans(plans) == 4, "Four combinations of test ids."
