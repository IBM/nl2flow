from tests.testing import BaseTestAgents

from nl2flow.plan.schemas import Action
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.options import BasicOperations
from nl2flow.compile.schemas import (
    GoalItem,
    GoalItems,
    MemoryItem,
    TypeItem,
    SignatureItem,
    SlotProperty,
)

# NOTE: This is part of dev dependencies
# noinspection PyPackageRequirements
import pytest


class TestTypingAdvanced(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

        self.flow.add(TypeItem(name="Contact"))

        new_credit_score_agent = Operator("New Credit Score API")
        new_credit_score_agent.add_input(
            SignatureItem(
                parameters=[
                    MemoryItem(item_id="New Email", item_type="Contact"),
                    MemoryItem(item_id="New AccountID"),
                ]
            )
        )

        goal = GoalItems(goals=GoalItem(goal_name="New Credit Score API"))
        self.flow.add([new_credit_score_agent, goal])

    def test_not_slot_fillable_with_typing_without_propagation(self) -> None:
        self.flow.add(SlotProperty(slot_name="New Email", slot_desirability=0))

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 4, "There should be 4 steps in the plan."

        step_1: Action = poi.plan[0]
        step_2: Action = poi.plan[1]
        assert (
            step_1.name == BasicOperations.SLOT_FILLER.value
            and step_2.name == BasicOperations.SLOT_FILLER.value
        ), "Two slot fills to start with."

        assert any(
            [
                "new_object_contact" in item
                for item in [step_1.inputs[0].name, step_2.inputs[0].name]
            ]
        ), "Ask for new object."

        step_3: Action = poi.plan[2]
        assert step_3.name == BasicOperations.MAPPER.value, "Followed by a mapping."

    def test_not_slot_fillable_with_typing_with_propagation(self) -> None:
        self.flow.add(
            SlotProperty(
                slot_name="New Email", slot_desirability=0, propagate_desirability=True
            )
        )

        plans = self.get_plan()
        assert not plans.list_of_plans, "There should be no plans."

    @pytest.mark.skip(reason="Coming soon.")
    def test_slot_desirability_with_propagation(self) -> None:
        raise NotImplementedError
