from tests.testing import BaseTestAgents
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.plan.schemas import PlannerResponse, Parameter
from nl2flow.compile.options import (
    MemoryState,
    GoalType,
    BasicOperations,
)
from nl2flow.compile.schemas import (
    MemoryItem,
    SignatureItem,
    GoalItems,
    GoalItem,
)


def plan_with_type_of_single_instance_same_as_direct_instance(
    plans: PlannerResponse,
) -> None:
    assert plans.list_of_plans, "There should be plans."

    poi = plans.list_of_plans[0]
    assert len(poi.plan) == 2, "There should be 2 step plan."
    assert poi.plan[0].name == BasicOperations.MAPPER.value, "Beginning with a map ..."
    assert poi.plan[1].name.startswith("Agent"), "... followed by the Agent."


def seperated_ands_should_be_same_as_combined_ands(plans: PlannerResponse) -> None:
    assert plans.list_of_plans, "There should be plans."

    poi = plans.list_of_plans[0]
    assert len(poi.plan) == 3, "There should be 3 step plan."
    assert (
        poi.plan[0].name == BasicOperations.SLOT_FILLER.value
    ), "Beginning with a slot fill ..."
    assert poi.plan[1].name == "Agent B", "... followed by Agent B ..."
    assert poi.plan[2].name == "Agent C", "... and ending with Agent A."


class TestGoalsBasic(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

        self.agent_names = ["A", "B", "C"]
        for index, item in enumerate(self.agent_names):
            new_agent = Operator(f"Agent {item}")

            item = item.lower()
            self.flow.add(MemoryItem(item_id=item, item_type="Mappable"))

            new_agent.add_input(
                SignatureItem(
                    parameters=[Parameter(item_id=item)],
                )
            )

            index = (index + 1) % len(self.agent_names)
            new_agent.add_output(
                SignatureItem(
                    parameters=[Parameter(item_id=self.agent_names[index].lower())],
                )
            )

            self.flow.add(new_agent)

    def test_goal_with_operator(self) -> None:
        target_agent_name = "Agent B"

        goal = GoalItems(goals=GoalItem(goal_name=target_agent_name))
        self.flow.add(goal)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 2, "There should be a 2 step plan."
        assert poi.plan[0].name == BasicOperations.SLOT_FILLER.value, "Slot filler ..."
        assert (
            poi.plan[1].name == target_agent_name
        ), "... followed by the target agent."

    def test_and_goals_in_same_goal_item(self) -> None:
        target_agents = ["Agent C", "Agent B"]
        for agent in target_agents:
            goal = GoalItems(goals=GoalItem(goal_name=agent))
            self.flow.add(goal)

        plans = self.get_plan()
        seperated_ands_should_be_same_as_combined_ands(plans)

    def test_and_goals_spread_across_goal_items(self) -> None:
        target_agents = ["Agent C", "Agent B"]
        goal = GoalItems(goals=[GoalItem(goal_name=agent) for agent in target_agents])
        self.flow.add([goal])

        plans = self.get_plan()
        seperated_ands_should_be_same_as_combined_ands(plans)

    def test_goal_with_object_used(self) -> None:
        self.flow.add(
            MemoryItem(
                item_id="id123", item_type="Mappable", item_state=MemoryState.KNOWN
            )
        )
        self.flow.add(
            GoalItems(goals=GoalItem(goal_name="id123", goal_type=GoalType.OBJECT_USED))
        )

        plans = self.get_plan()
        plan_with_type_of_single_instance_same_as_direct_instance(plans)

    def test_goal_with_typing_used(self) -> None:
        self.flow.add(
            MemoryItem(
                item_id="id123", item_type="Mappable", item_state=MemoryState.KNOWN
            )
        )

        self.flow.add(
            GoalItems(
                goals=GoalItem(goal_name="Mappable", goal_type=GoalType.OBJECT_USED)
            )
        )

        plans = self.get_plan()
        plan_with_type_of_single_instance_same_as_direct_instance(plans)

    def test_goal_with_typing_known(self) -> None:
        self.flow.add(
            GoalItems(
                goals=[
                    GoalItem(goal_name="Mappable", goal_type=GoalType.OBJECT_KNOWN),
                ]
            )
        )

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 3, "There should be 3 step plan."

        action_names = [operator.name for operator in poi.plan]

        assert (
            BasicOperations.SLOT_FILLER.value == action_names[0]
        ), "One slot fill first ..."
        assert {BasicOperations.MAPPER.value} == set(
            action_names[1:]
        ), "... followed by two mappings."

    def test_goal_with_object_known(self) -> None:
        agent_names = ["X", "Y"]
        for index, item in enumerate(agent_names):
            new_agent = Operator(f"Agent {item}")
            new_agent.add_output(
                SignatureItem(
                    parameters=[MemoryItem(item_id="same thing")],
                )
            )
            self.flow.add(new_agent)

        self.flow.add(
            GoalItems(
                goals=GoalItem(goal_name="same thing", goal_type=GoalType.OBJECT_KNOWN)
            )
        )

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 1, "There should be 1 step plan ..."
        assert poi.plan[0].name == "Agent Y", "... with Agent Y."
