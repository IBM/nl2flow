from nl2flow.compile.schemas import GoalItem, GoalItems, SlotProperty, MappingItem
from nl2flow.compile.options import (
    BasicOperations,
    LifeCycleOptions,
    MappingOptions,
    SlotOptions,
)
from tests.testing import BaseTestAgents


class TestBasicButNotBasic(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

    def test_basic_with_prohibition(self) -> None:
        goal = GoalItems(goals=GoalItem(goal_name="Fix Errors"))
        self.flow.add(goal)

        self.flow.mapping_options.add(MappingOptions.prohibit_direct)
        self.flow.slot_options.add(SlotOptions.last_resort)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 2, "Plan of length 2."
        assert (
            poi.plan[0].name == BasicOperations.SLOT_FILLER.value
            and poi.plan[0].inputs[0].item_id == "list of errors"
        ), "Ask directly for list of errors."

        self.flow.add(
            MappingItem(
                source_name="list of errors",
                target_name="list of errors",
                probability=1.0,
            )
        )

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 4, "Plan of length 4."
        assert (
            poi.plan[0].name == BasicOperations.SLOT_FILLER.value
            and poi.plan[0].inputs[0].item_id == "database link"
        ), "Ask directly for database link."
        assert poi.plan[2].name == BasicOperations.MAPPER.value and set(
            i.item_id for i in poi.plan[2].inputs
        ) == {"list of errors"}, "Map list of errors."

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
