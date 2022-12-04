from tests.testing import BaseTestAgents

from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.options import BasicOperations
from nl2flow.plan.schemas import Parameter
from nl2flow.compile.schemas import (
    GoalItem,
    GoalItems,
    TypeItem,
    SignatureItem,
    SlotProperty,
)


class TestTypingAdvanced(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

        self.flow.add(TypeItem(name="Contact"))

        helper_agent = Operator("Helper Agent")
        helper_agent.add_input(
            SignatureItem(
                parameters=[
                    Parameter(item_id="Email ID", item_type="Contact"),
                ]
            )
        )
        helper_agent.add_output(SignatureItem(parameters=["New AccountID"]))

        new_credit_score_agent = Operator("New Credit Score API")
        new_credit_score_agent.add_input(
            SignatureItem(
                parameters=[
                    Parameter(item_id="New Email", item_type="Contact"),
                    Parameter(item_id="New AccountID"),
                ]
            )
        )

        goal = GoalItems(goals=GoalItem(goal_name="New Credit Score API"))
        self.flow.add([new_credit_score_agent, helper_agent, goal])

    def test_not_slot_fillable_with_typing_with_propagation(self) -> None:
        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 4, "Plan of length 4."
        assert BasicOperations.MAPPER.value in [
            action.name for action in poi.plan
        ], "Mapper in the plan."

        self.flow.add(
            SlotProperty(
                slot_name="New Email", slot_desirability=0, propagate_desirability=True
            )
        )

        plans = self.get_plan()
        assert not plans.list_of_plans, "There should be no plans."

    def test_slot_desirability_with_propagation(self) -> None:
        fake_helper_agent = Operator("Fake Helper Agent")
        fake_helper_agent.add_input(
            SignatureItem(
                parameters=[
                    Parameter(item_id="Fake Email ID", item_type="Contact"),
                ]
            )
        )
        fake_helper_agent.add_output(SignatureItem(parameters=["New AccountID"]))

        self.flow.add(
            [
                fake_helper_agent,
                SlotProperty(slot_name="Fake Email ID", slot_desirability=1.0),
            ]
        )

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 4, "Plan of length 4."
        assert "Fake Helper Agent" in [
            action.name for action in poi.plan
        ], "Fake helper agent in the plan."

        self.flow.add(
            SlotProperty(
                slot_name="Fake Email ID",
                slot_desirability=1.0,
                propagate_desirability=True,
            )
        )

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        is_helper_agent_there = False
        count = 0
        optimal_cost = plans.list_of_plans[0].cost
        for plan_object in plans.list_of_plans:
            if plan_object.cost == optimal_cost:
                count += 1
                is_helper_agent_there = is_helper_agent_there or "Helper Agent" in [
                    action.name for action in plan_object.plan
                ]
            else:
                break

        assert count >= 2, "There must be at least two optimal plans."
        assert (
            is_helper_agent_there
        ), "Original helper agent must be there among the optimal plans."
