from tests.testing import BaseTestAgents
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.plan.schemas import Step
from nl2flow.compile.options import (
    MemoryState,
    BasicOperations,
)
from nl2flow.compile.schemas import (
    PartialOrder,
    MemoryItem,
    SignatureItem,
    GoalItems,
    GoalItem,
)


class TestOrderings(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

        agent_names = ["X", "Y"]
        for index, item in enumerate(agent_names):
            new_agent = Operator(f"Agent {item}")
            new_agent.add_output(
                SignatureItem(
                    parameters=item.lower(),
                )
            )
            self.flow.add(new_agent)

        final_agent = Operator("Final Agent")
        final_agent.add_input(
            SignatureItem(
                parameters=["x", "y"],
            )
        )

        another_agent = Operator("Another Agent")
        another_agent.add_input(
            SignatureItem(
                parameters=["x", "y"],
            )
        )

        self.flow.add([final_agent, another_agent])

    def test_start_with(self) -> None:
        self.flow.set_start("Agent Y")
        self.flow.add(
            GoalItems(
                goals=[
                    GoalItem(goal_name="Final Agent"),
                    GoalItem(goal_name="Another Agent"),
                ]
            )
        )

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 4, "There should be 4 step plan."
        assert poi.plan[0].name == "Agent Y", "Starts with Agent Y."

    def test_ends_with(self) -> None:
        self.flow.set_start("Agent X")
        self.flow.set_end("Another Agent")
        self.flow.add(
            GoalItems(
                goals=[
                    GoalItem(goal_name="Final Agent"),
                    GoalItem(goal_name="Another Agent"),
                ]
            )
        )

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 4, "There should be 4 step plan."
        assert poi.plan[3].name == "Another Agent", "Ends with Another Agent."

    def test_partial_order(self) -> None:
        self.flow.add(
            [
                PartialOrder(antecedent="Final Agent", consequent="Another Agent"),
                PartialOrder(antecedent="Agent Y", consequent="Agent X"),
            ]
        )

        self.flow.add(
            GoalItems(
                goals=[
                    GoalItem(goal_name="Final Agent"),
                    GoalItem(goal_name="Another Agent"),
                ]
            )
        )

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 4, "There should be 4 step plan."
        assert poi.plan[0].name == "Agent Y", "Starts with Agent Y."
        assert poi.plan[3].name == "Another Agent", "Ends with Another Agent."
        assert len([p for p in plans.list_of_plans if p.cost == poi.cost]) == 1, "Only one POI."

    def test_partial_order_with_history_not_allowed(self) -> None:
        self.flow.add(
            [
                PartialOrder(antecedent="Final Agent", consequent="Another Agent"),
                PartialOrder(antecedent="Agent Y", consequent="Agent X"),
                Step(name="Agent X"),
            ]
        )

        self.flow.add(
            GoalItems(
                goals=[
                    GoalItem(goal_name="Final Agent"),
                    GoalItem(goal_name="Another Agent"),
                ]
            )
        )

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 4, "There should be 4 step plan."
        assert {poi.plan[0].name, poi.plan[1].name} == {BasicOperations.SLOT_FILLER.value}, "Two slot fills."
        assert "Agent Y" not in [o.name for o in poi.plan], "No Agent Y."

    def test_partial_order_with_history_already_done(self) -> None:
        self.flow.add(
            [
                PartialOrder(antecedent="Final Agent", consequent="Another Agent"),
                PartialOrder(antecedent="Agent Y", consequent="Agent X"),
                Step(name="Agent Y"),
                MemoryItem(item_id="y", item_state=MemoryState.KNOWN),
            ]
        )

        self.flow.add(
            GoalItems(
                goals=[
                    GoalItem(goal_name="Final Agent"),
                    GoalItem(goal_name="Another Agent"),
                ]
            )
        )

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 3, "There should be 3 step plan."
        assert poi.plan[0].name == "Agent X", "Agent X only."
