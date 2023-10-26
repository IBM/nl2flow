from nl2flow.compile.schemas import GoalItem, GoalItems, SlotProperty
from nl2flow.compile.options import BasicOperations, SlotOptions, LifeCycleOptions
from nl2flow.plan.schemas import Action

from tests.testing import BaseTestAgents
from tests.slots.test_slots_basic import (
    fallback_and_last_resort_tests_should_look_the_same,
)

from collections import Counter
import pytest


class TestSlotFillerAdvanced(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

    def test_do_not_last_resort(self) -> None:
        goal = GoalItems(goals=GoalItem(goal_name="Fix Errors"))
        self.flow.add(goal)

        self.flow.slot_options.add(SlotOptions.last_resort)
        self.flow.add(SlotProperty(slot_name="list of errors", do_not_last_resort=True))

        plans = self.get_plan()

        with pytest.raises(Exception):
            fallback_and_last_resort_tests_should_look_the_same(plans)

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 2, "There should be 2 steps."

        assert (
            poi.plan[0].name == BasicOperations.SLOT_FILLER.value and poi.plan[0].inputs[0].item_id == "list of errors"
        ), "Directly fill slot instead of mapping as last resort."

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
            [param.item_id for param in step_1.inputs]
        ), "Slot fill AccountID and Email together."

        step_2: Action = poi.plan[1]
        assert step_2.name == "Credit Score API", "Third action should be the goal action."

    def test_slot_filler_with_confirm(self) -> None:
        goal = GoalItems(goals=GoalItem(goal_name="Credit Score API"))
        self.flow.add(goal)

        self.flow.slot_options.add(SlotOptions.last_resort)
        self.flow.variable_life_cycle.add(LifeCycleOptions.confirm_on_slot)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 5, "There should be 5 steps."

        assert Counter(["AccountID", "Email"]) == Counter(
            set([step.inputs[0].item_id for step in poi.plan[: len(poi.plan) - 1]])
        )

        assert [step.name for step in poi.plan].count(BasicOperations.SLOT_FILLER.value) == 2, "Two slot fills."
        assert [step.name for step in poi.plan].count(BasicOperations.CONFIRM.value) == 2, "Two slot confirmations."

        assert poi.plan[len(poi.plan) - 1].name == "Credit Score API", "Final action should be the goal action."
