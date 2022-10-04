from nl2flow.compile.schemas import GoalItem, GoalItems, SlotProperty
from nl2flow.compile.options import BasicOperations
from nl2flow.plan.schemas import Action, PlannerResponse
from tests.testing import BaseTestAgents

from collections import Counter

# NOTE: This is part of dev dependencies
# noinspection PyPackageRequirements
import pytest


class TestSlotFillerBasic(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

    def test_slot_filler_basic(self) -> None:
        goal = GoalItems(goals=GoalItem(goal_name="Credit Score API"))
        self.flow.add(goal)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 3, "There should be 3 steps."

        assert Counter(["AccountID", "Email"]) == Counter(
            [step.inputs[0].name for step in poi.plan[:2]]
        )
        assert (
            poi.plan[2].name == "Credit Score API"
        ), "Third action should be the goal action."

    def test_not_slot_fillable_no_solution(self) -> None:
        goal = GoalItems(goals=GoalItem(goal_name="Credit Score API"))
        self.flow.add(goal)
        self.flow.add(SlotProperty(slot_name="AccountID", slot_desirability=0))

        plans = self.get_plan()
        assert not plans.list_of_plans, "There should be no empty plans."

    @staticmethod
    def __fallback_and_last_resort_tests_should_look_the_same(
        plans: PlannerResponse,
    ) -> None:
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 3, "There should be 3 steps in the plan."

        step_1: Action = poi.plan[0]
        assert (
            step_1.name == BasicOperations.SLOT_FILLER.value
            and step_1.inputs[0].name == "database link"
        ), "The first step should be looking to slot fill database link."

        step_2: Action = poi.plan[1]
        assert (
            step_2.name == "Find Errors"
        ), "Step 2 acquires list of errors using Find Errors."

        step_3: Action = poi.plan[2]
        assert (
            step_3.name == "Fix Errors"
        ), "Fix Errors without slot filling list of errors."

    def test_not_slot_fillable_fallback(self) -> None:
        goal = GoalItems(goals=GoalItem(goal_name="Fix Errors"))
        self.flow.add(goal)
        self.flow.add(SlotProperty(slot_name="list_of_errors", slot_desirability=0))

        plans = self.get_plan()
        self.__fallback_and_last_resort_tests_should_look_the_same(plans)

    def test_slot_fillable_as_last_resort(self) -> None:
        goal = GoalItems(goals=GoalItem(goal_name="Fix Errors"))
        self.flow.add(goal)

        plans = self.get_plan()
        self.__fallback_and_last_resort_tests_should_look_the_same(plans)

    @pytest.mark.skip(reason="Coming soon.")
    def test_slot_preference(self) -> None:
        raise NotImplementedError
