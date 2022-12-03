from tests.testing import BaseTestAgents
from nl2flow.plan.schemas import Step, Parameter
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.options import GoalType, MemoryState, BasicOperations
from nl2flow.compile.schemas import (
    MemoryItem,
    SignatureItem,
    GoalItems,
    GoalItem,
)

import pytest


class TestRetryBasic(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

    def test_retry_basic_blocked(self) -> None:
        basic_agent = Operator("Basic Agent")
        self.flow.add(
            [
                basic_agent,
                Step(name="Basic Agent"),
                GoalItems(goals=GoalItem(goal_name="Basic Agent")),
            ]
        )

        plans = self.get_plan()
        assert not plans.list_of_plans, "There should be no plans."

    def test_retry_multiple_times(self) -> None:
        basic_agent = Operator("Basic Agent")
        basic_agent.max_try = 3

        self.flow.add(
            [
                basic_agent,
                Step(name="Basic Agent"),
                Step(name="Basic Agent"),
                GoalItems(goals=GoalItem(goal_name="Basic Agent")),
            ]
        )

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert (
            len(poi.plan) == 1 and poi.plan[0].name == "Basic Agent"
        ), "One step with the target agent."

        self.flow.add(Step(name="Basic Agent"))

        plans = self.get_plan()
        assert not plans.list_of_plans, "There should be no plans."

    def test_retry_blocked_with_alternative(self) -> None:

        new_agent = Operator("New Agent")
        new_agent.add_output(SignatureItem(parameters=[MemoryItem(item_id="x")]))

        alternative_agent = Operator("Alternative Agent")
        alternative_agent.add_output(
            SignatureItem(parameters=[MemoryItem(item_id="x")])
        )

        self.flow.add(
            [
                new_agent,
                alternative_agent,
                GoalItems(
                    goals=GoalItem(goal_name="x", goal_type=GoalType.OBJECT_KNOWN)
                ),
            ]
        )

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert (
            sum([int(poi.cost == p.cost) for p in plans.list_of_plans]) == 2
        ), "Two plans possible."

        self.flow.add(Step(name="New Agent"))

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert (
            poi.plan[0].name == "Alternative Agent"
        ), "Alternative Agent used instead."
        assert (
            sum([int(poi.cost == p.cost) for p in plans.list_of_plans]) == 1
        ), "One plan possible."

    def test_retry_with_instance(self) -> None:
        agent = Operator("Agent")
        agent.add_input(
            SignatureItem(parameters=[MemoryItem(item_id="x", item_type="shareable")])
        )
        agent.max_try = 2

        self.flow.add(agent)
        self.flow.add(GoalItems(goals=GoalItem(goal_name="Agent")))
        self.flow.add(Step(name="Agent", parameters=[Parameter(item_id="x")]))

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert (
            len(poi.plan) == 2
            and poi.plan[0].name == BasicOperations.SLOT_FILLER.value
            and poi.plan[0].inputs[0].item_id == "x"
        ), "Same old 2 step plan."

    def test_retry_with_instance_blocked(self) -> None:
        agent = Operator("Agent")
        agent.add_input(
            SignatureItem(parameters=[MemoryItem(item_id="x", item_type="shareable")])
        )

        self.flow.add(agent)
        self.flow.add(GoalItems(goals=GoalItem(goal_name="Agent")))
        self.flow.add(Step(name="Agent", parameters=[Parameter(item_id="x")]))

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert (
            len(poi.plan) == 3
            and poi.plan[0].name == BasicOperations.SLOT_FILLER.value
            and poi.plan[0].inputs[0].item_id.startswith("new_object")
        ), "3 step plan with a new spwaned object."

        self.flow.add(
            MemoryItem(
                item_id="id123", item_type="shareable", item_state=MemoryState.KNOWN
            )
        )

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert (
            len(poi.plan) == 2 and poi.plan[1].name == "Agent"
        ), "Two step plan with the target agent."

    @pytest.mark.skip(reason="Coming soon.")
    def test_blocked_agent(self) -> None:
        raise NotImplementedError

    @pytest.mark.skip(reason="This will be supported with history compilation.")
    def test_retry_with_confirmation(self) -> None:
        raise NotImplementedError
