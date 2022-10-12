from nl2flow.compile.schemas import GoalItem, GoalItems, SlotProperty
from nl2flow.compile.options import BasicOperations, LifeCycleOptions
from tests.testing import BaseTestAgents


class TestBasicButNotBasic(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

    def test_confirm_on_determination(self) -> None:
        self.flow.add(GoalItems(goals=GoalItem(goal_name="Fix Errors")))
        self.flow.add(SlotProperty(slot_name="list of errors", slot_desirability=0.0))
        self.flow.variable_life_cycle.add(LifeCycleOptions.confirm_on_determination)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 4, "The plan should have 3 steps."

        assert (
            poi.plan[2].name == BasicOperations.CONFIRM.value
        ), "The third step should be a confirmation."
