from nl2flow.compile.schemas import GoalItem, GoalItems
from nl2flow.compile.options import BasicOperations, SlotOptions
from nl2flow.plan.schemas import Action
from tests.testing import BaseTestAgents

from collections import Counter


class TestSlotFillerAdvanced(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

    def test_slot_filler_grouping(self) -> None:
        goal = GoalItems(goals=GoalItem(goal_name="Credit Score API"))
        self.flow.add(goal)
        self.flow.slot_options.add(SlotOptions.group_slots)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 2, "There should be 2 steps."

        step_1: Action = poi.plan[0]
        assert step_1.name == BasicOperations.SLOT_FILLER.value, "Slot fill first."
        assert Counter(["AccountID", "Email"]) == Counter(
            [param.name for param in step_1.inputs]
        ), "Slot fill AccountID and Email together."

        step_2: Action = poi.plan[1]
        assert (
            step_2.name == "Credit Score API"
        ), "Third action should be the goal action."
