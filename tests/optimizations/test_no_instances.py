from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.options import NL2FlowOptions, SlotOptions, ConstraintState, MemoryState
from nl2flow.compile.schemas import (
    GoalItem,
    GoalItems,
    SignatureItem,
    Step,
    SlotProperty,
    Constraint,
    MemoryItem,
    MappingItem,
)

from tests.testing import BaseTestAgents
from tests.slots.test_slots_basic import fallback_and_last_resort_tests_should_look_the_same


class TestBasicButNotBasic(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)
        self.flow.slot_options.add(SlotOptions.last_resort)

        agent_1 = Operator("Agent 1")
        agent_1.add_input(SignatureItem(parameters="x", constraints=[Constraint(constraint="$x > 5")]))
        agent_1.add_output(SignatureItem(parameters="y"))
        agent_1.max_try = 2

        agent_2 = Operator("Agent 2")
        agent_2.add_input(SignatureItem(parameters="y"))

        self.flow.add([agent_1, agent_2])
        self.flow.add(SlotProperty(slot_name="y", slot_desirability=0.0))

    def test_lots_of_parameters(self) -> None:
        self.flow.optimization_options.remove(NL2FlowOptions.multi_instance)
        self.flow.optimization_options.remove(NL2FlowOptions.allow_retries)

        agent_a = Operator(name="Agent A")
        agent_a.add_input(SignatureItem(parameters=["a", "b", "c", "d", "e", "f"]))

        agent_b = Operator(name="Agent X")
        agent_b.add_input(SignatureItem(parameters=["x", "y", "z", "p", "q", "r", "s"]))

        self.flow.add([agent_b, agent_a])
        self.flow.add(GoalItems(goals=[GoalItem(goal_name="Agent A"), GoalItem(goal_name="Agent X")]))

        planner_response = self.get_plan()
        assert planner_response.list_of_plans, "There should be plans."

    def test_basic_plan_is_the_same(self) -> None:
        self.flow.optimization_options.remove(NL2FlowOptions.multi_instance)
        self.flow.optimization_options.remove(NL2FlowOptions.allow_retries)

        goal = GoalItems(goals=GoalItem(goal_name="Fix Errors"))
        self.flow.add(goal)

        planner_response = self.get_plan()
        fallback_and_last_resort_tests_should_look_the_same(planner_response)

    def test_history_with_no_instance(self) -> None:
        self.flow.optimization_options.remove(NL2FlowOptions.multi_instance)

        goal = GoalItems(goals=GoalItem(goal_name="Agent 2"))
        self.flow.add(goal)

        self.flow.add(
            Step(
                name="Agent 1",
                parameters=["x"],
            )
        )

        planner_response = self.get_plan()
        assert planner_response.list_of_plans, "There should be plans."
        assert len(planner_response.best_plan.plan) == 4, "Best plan is of length 4."

        self.flow.add(
            Step(
                name="Agent 1",
                parameters=["x"],
            )
        )

        planner_response = self.get_plan()
        assert planner_response.is_no_solution, "There should be no plans."

    def test_history_with_no_retry(self) -> None:
        self.flow.optimization_options.remove(NL2FlowOptions.allow_retries)

        goal = GoalItems(goals=GoalItem(goal_name="Agent 2"))
        self.flow.add(goal)

        self.flow.add(
            Step(
                name="Agent 1",
                parameters=["x"],
            )
        )

        planner_response = self.get_plan()
        assert planner_response.is_no_solution, "There should be no plans."

    # def test_history_with_no_instance_no_retry(self) -> None:
    #     self.flow.optimization_options.remove(NL2FlowOptions.multi_instance)
    #     self.flow.optimization_options.remove(NL2FlowOptions.allow_retries)
    #
    #     goal = GoalItems(goals=GoalItem(goal_name="Agent 2"))
    #     self.flow.add(goal)
    #
    #     self.flow.add(
    #         [
    #             MemoryItem(
    #                 item_id="item123",
    #                 item_state=MemoryState.KNOWN,
    #             ),
    #             MappingItem(
    #                 source_name="item123",
    #                 target_name="x",
    #                 probability=1.0,
    #             ),
    #             Step(
    #                 name="Agent 1",
    #                 parameters=["x"],
    #             ),
    #         ]
    #     )
    #
    #     planner_response = self.get_plan()
    #     assert planner_response.list_of_plans, "There should be plans."

    def test_constraints_with_no_instance(self) -> None:
        self.flow.optimization_options.remove(NL2FlowOptions.multi_instance)

        goal = GoalItems(goals=GoalItem(goal_name="Agent 2"))
        self.flow.add(goal)

        self.flow.add(
            Constraint(
                constraint="$x > 5",
                truth_value=ConstraintState.TRUE.value,
            )
        )

        planner_response = self.get_plan()
        assert planner_response.list_of_plans, "There should be plans."
        assert len(planner_response.best_plan.plan) == 3, "Best plan is of length 3."

    def test_goal_with_no_instance(self) -> None:
        self.flow.optimization_options.remove(NL2FlowOptions.multi_instance)

        self.flow.add(
            [
                MemoryItem(item_id="id123", item_state=MemoryState.KNOWN),
                MappingItem(source_name="id123", target_name="y", probability=1.0),
            ]
        )

        goal = GoalItems(goals=GoalItem(goal_name=Step(name="Agent 2", parameters=["id123"])))
        self.flow.add(goal)

        planner_response = self.get_plan()
        assert planner_response.list_of_plans, "There should be plans."
        assert len(planner_response.best_plan.plan) == 2, "Best plan is of length 2."

        self.flow.add(
            Step(
                name="Agent 2",
                parameters=["id123"],
            )
        )

        planner_response = self.get_plan()
        assert planner_response.is_no_solution, "There should be no plans."

        agent_2 = next(filter(lambda x: x.name == "Agent 2", self.flow.flow_definition.operators))
        agent_2.max_try = 5

        planner_response = self.get_plan()
        assert planner_response.list_of_plans, "There should be plans."

        self.flow.optimization_options.remove(NL2FlowOptions.allow_retries)
        planner_response = self.get_plan()
        assert planner_response.is_no_solution, "There should be no plans."
