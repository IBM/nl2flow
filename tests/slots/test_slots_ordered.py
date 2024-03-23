from nl2flow.compile.schemas import GoalItem, GoalItems, SignatureItem
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.options import BasicOperations, SlotOptions
from tests.testing import BaseTestAgents


class TestSlotFillerOrdered(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

        agent_a = Operator("Agent A")
        agent_a.add_input(SignatureItem(parameters=["x", "y"]))
        agent_a.add_output(SignatureItem(parameters="a"))

        agent_b = Operator("Agent B")
        agent_b.add_input(SignatureItem(parameters=["a", "b", "c"]))

        self.flow.add([agent_b, agent_a])

    def test_in_order(self) -> None:
        self.flow.slot_options.add(SlotOptions.ordered)

        goal = GoalItems(goals=GoalItem(goal_name="Agent B"))
        self.flow.add(goal)

        plans = self.get_plan()
        assert len(plans.list_of_plans) == 1, "There should be exactly one plan."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 4, "There should be 4 steps in the plan."

        assert all([step.name == BasicOperations.SLOT_FILLER.value for step in poi.plan[:3]]), "Three slot fills..."
        assert [step.inputs[0].item_id for step in poi.plan[:3]] == ["a", "b", "c"], "... of a, b, c in order."

    def test_in_order_with_last_resort(self) -> None:
        self.flow.slot_options.add(SlotOptions.ordered)
        self.flow.slot_options.add(SlotOptions.last_resort)

        goal = GoalItems(goals=GoalItem(goal_name="Agent B"))
        self.flow.add(goal)

        plans = self.get_plan()
        assert len(plans.list_of_plans) == 1, "There should be exactly one plan."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 6, "There should be 6 steps in the plan."
        assert poi.plan[2].name == "Agent A", "Agent A is used to get value of a."
        assert [step.inputs[0].item_id for step in poi.plan if step.name == BasicOperations.SLOT_FILLER.value] == [
            "x",
            "y",
            "b",
            "c",
        ]

    def test_slot_all_together(self) -> None:
        self.flow.slot_options.add(SlotOptions.all_together)

        goal = GoalItems(goals=GoalItem(goal_name="Agent B"))
        self.flow.add(goal)

        plans = self.get_plan()
        assert len(plans.list_of_plans) == 1, "There should be exactly one plan."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 2, "There should be 2 steps in the plan."

        assert poi.plan[0].name == BasicOperations.SLOT_FILLER.value and poi.plan[0].inputs, "One slot fill..."
        assert [item.item_id for item in poi.plan[0].inputs] == ["a", "b", "c"], "... of a, b, c in order."

    def test_slot_all_together_conflict_with_last_resort(self) -> None:
        self.flow.slot_options.add(SlotOptions.all_together)
        self.flow.slot_options.add(SlotOptions.last_resort)

        goal = GoalItems(goals=GoalItem(goal_name="Agent B"))
        self.flow.add(goal)

        plans = self.get_plan()
        assert len(plans.list_of_plans) == 2, "There should be two plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 5, "There should be 5 steps in the plan."

        slots_filled = set()
        for step in poi.plan:
            if step.name.startswith(BasicOperations.SLOT_FILLER.value):
                slots_filled.update({input.item_id for input in step.inputs})

        assert slots_filled == {
            "x",
            "y",
            "b",
            "c",
        }

        self.flow.slot_options.add(SlotOptions.group_slots)
        plans = self.get_plan()

        assert len(plans.list_of_plans) == 2, "There should be two plans."
        assert set([item.item_id for item in plans.list_of_plans[0].plan[0].inputs]) == set(
            [item.item_id for item in plans.list_of_plans[0].plan[0].inputs]
        ), "All the slots grouped together."
