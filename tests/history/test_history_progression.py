from tests.testing import BaseTestAgents
from tests.test_slots.test_slots_basic import (
    fallback_and_last_resort_tests_should_look_the_same,
)

from nl2flow.plan.schemas import PlannerResponse
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.options import (
    MemoryState,
    LifeCycleOptions,
    BasicOperations,
)
from nl2flow.compile.schemas import (
    MemoryItem,
    SignatureItem,
    SlotProperty,
    MappingItem,
    GoalItems,
    GoalItem,
)


def basic_plan_with_two_steps(planner_response: PlannerResponse) -> None:
    assert planner_response.list_of_plans, "There should be plans."

    poi = planner_response.list_of_plans[0]
    assert len(poi.plan) == 2, "There should be 2 step plan."

    first_step = poi.plan[0]
    first_step_parameter = first_step.inputs[0]
    assert (
        first_step.name == BasicOperations.SLOT_FILLER.value
        and first_step_parameter.item_id == "list of errors"
    ), "First step should slot fill list of errors directly."


class TestHistoryProgression(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

        account_agent = Operator("Account Agent")
        account_agent.add_output(
            SignatureItem(
                parameters=[
                    MemoryItem(item_id="account name", item_type="Email Object")
                ]
            )
        )

        w3_agent = Operator("W3 Agent")
        w3_agent.add_input(
            SignatureItem(
                parameters=[MemoryItem(item_id="W3 ID", item_type="Email Object")]
            )
        )

        self.flow.add([w3_agent, account_agent])

    def test_history_progress(self) -> None:
        goal = GoalItems(goals=GoalItem(goal_name="Fix Errors"))
        self.flow.add(goal)

        plans = self.get_plan()
        basic_plan_with_two_steps(plans)

        self.flow.add(
            MemoryItem(item_id="list of errors", item_state=MemoryState.KNOWN)
        )

        plans = self.get_plan()
        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 1, "There should be 1 step plan."
        assert (
            poi.plan[0].name == "Fix Errors"
        ), "First and (orignally final) step is the goal action."

    def test_history_slot_ban(self) -> None:
        goal = GoalItems(goals=GoalItem(goal_name="Fix Errors"))
        self.flow.add(goal)

        plans = self.get_plan()
        basic_plan_with_two_steps(plans)

        self.flow.add(SlotProperty(slot_name="list of errors", slot_desirability=0))

        plans = self.get_plan()
        fallback_and_last_resort_tests_should_look_the_same(plans)

    def test_history_progress_with_types(self) -> None:
        goal = GoalItems(goals=GoalItem(goal_name="W3 Agent"))
        self.flow.add(goal)
        self.flow.variable_life_cycle.add(LifeCycleOptions.confirm_on_mapping)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 4, "There should be 4 step plan."
        assert poi.plan[0].name == "Account Agent", "Acquires email from Account Agent."
        assert (
            poi.plan[1].name == BasicOperations.MAPPER.value
        ), "Followed by a mapping step."

        self.flow.add(
            MemoryItem(
                item_id="id123", item_type="Email Object", item_state=MemoryState.KNOWN
            )
        )

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 3, "There should be 3 step plan."

        step_1 = poi.plan[0]
        assert (
            step_1.name == BasicOperations.MAPPER.value
            and step_1.inputs[0].item_id == "id123"
        ), "Must be mapping the new thing."

    def test_history_mapping_ban_step_1(self) -> None:
        goal = GoalItems(goals=GoalItem(goal_name="W3 Agent"))
        self.flow.add(goal)
        self.flow.variable_life_cycle.add(LifeCycleOptions.confirm_on_mapping)

        self.flow.add(
            [
                MemoryItem(
                    item_id="id123",
                    item_type="Email Object",
                    item_state=MemoryState.KNOWN,
                ),
                MemoryItem(
                    item_id="W3 ID",
                    item_type="Email Object",
                    item_state=MemoryState.UNCERTAIN,
                ),
            ]
        )

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 2, "There should be 2 step plan."

        step_0 = poi.plan[0]
        assert (
            step_0.name == BasicOperations.CONFIRM.value
            and step_0.inputs[0].item_id == "W3 ID"
        ), "Confirm the W3 ID value."

    def test_history_mapping_ban_step_2(self) -> None:
        goal = GoalItems(goals=GoalItem(goal_name="W3 Agent"))
        self.flow.add(goal)
        self.flow.variable_life_cycle.add(LifeCycleOptions.confirm_on_mapping)

        self.flow.add(
            [
                MappingItem(source_name="id123", target_name="W3 ID", probability=0),
                MemoryItem(
                    item_id="id123",
                    item_type="Email Object",
                    item_state=MemoryState.KNOWN,
                ),
            ]
        )

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 4, "There should be 4 step plan."
        assert poi.plan[0].name == "Account Agent", "Acquires email from Account Agent."
        assert (
            poi.plan[1].name == BasicOperations.MAPPER.value
        ), "Followed by a mapping step."
