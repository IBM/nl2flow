from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.options import BasicOperations, LifeCycleOptions
from nl2flow.plan.schemas import Action
from nl2flow.compile.schemas import (
    Parameter,
    GoalItem,
    GoalItems,
    MappingItem,
    SignatureItem,
    MemoryItem,
    SlotProperty,
    TypeItem,
)

from tests.testing import BaseTestAgents
from collections import Counter


class TestMappingsAdvanced(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

    def test_mapper_no_slot_fill(self) -> None:
        test_agent = Operator("Test Agent")
        test_agent.add_input(SignatureItem(parameters=[Parameter(item_id="random", item_type="something_random")]))

        goal = GoalItems(goals=GoalItem(goal_name="Test Agent"))
        self.flow.add([test_agent, goal, SlotProperty(slot_name="random", slot_desirability=0.0)])

        plans = self.get_plan()
        assert not plans.list_of_plans, "There should be no plans."

    def test_mapper_no_slot_fill_with_type_propagation(self) -> None:
        self.flow.add(TypeItem(name="random"))
        self.flow.add(
            [
                MemoryItem(item_id="random_1", item_type="random"),
                MemoryItem(item_id="random_2", item_type="random"),
            ]
        )

        test_agent = Operator("Test Agent")
        test_agent.add_input(SignatureItem(parameters=["random_1"]))

        goal = GoalItems(goals=GoalItem(goal_name="Test Agent"))
        self.flow.add(
            [
                test_agent,
                goal,
                SlotProperty(slot_name="random_1", slot_desirability=0.0),
            ]
        )

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        self.flow.add(SlotProperty(slot_name="random_2", slot_desirability=0.0, propagate_desirability=True))

        plans = self.get_plan()
        assert not plans.list_of_plans, "There should be no plans."

    def test_mapper_basic_with_confirm(self) -> None:
        self.flow.add(
            [
                MappingItem(source_name="Username", target_name="Email"),
                MappingItem(source_name="Account Info", target_name="AccountID"),
            ]
        )

        goal = GoalItems(goals=GoalItem(goal_name="Credit Score API"))
        self.flow.add(goal)

        self.flow.variable_life_cycle.add(LifeCycleOptions.confirm_on_mapping)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 6, "The plan should have 6 steps."

        step_1: Action = poi.plan[0]
        assert step_1.name == "User Info", "Call user info agent to map later."

        assert Counter(2 * [BasicOperations.MAPPER.value, BasicOperations.CONFIRM.value]) == Counter(
            [step.name for step in poi.plan[1 : len(poi.plan) - 1]]
        ), "Followed by two mappings and two confirms."

        step_6: Action = poi.plan[5]
        assert step_6.name == "Credit Score API", "Final action should be the goal action."
