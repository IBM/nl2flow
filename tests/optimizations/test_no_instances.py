from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.schemas import GoalItem, GoalItems, SignatureItem, Step, SlotProperty
from nl2flow.compile.options import NL2FlowOptions, SlotOptions

from tests.testing import BaseTestAgents
from tests.slots.test_slots_basic import fallback_and_last_resort_tests_should_look_the_same


class TestBasicButNotBasic(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)
        self.flow.slot_options.add(SlotOptions.last_resort)

        agent_1 = Operator("Agent 1")
        agent_1.add_input(SignatureItem(parameters="x"))
        agent_1.add_output(SignatureItem(parameters="y"))
        agent_1.max_try = 2

        agent_2 = Operator("Agent 2")
        agent_2.add_input(SignatureItem(parameters="y"))

        self.flow.add([agent_1, agent_2])
        self.flow.add(SlotProperty(slot_name="y", slot_desirability=0.0))

    def test_lots_of_parameters(self) -> None:
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
        goal = GoalItems(goals=GoalItem(goal_name="Agent 2"))
        self.flow.add(goal)

        self.flow.optimization_options.remove(NL2FlowOptions.allow_retries)
        # planner_response = self.get_plan()
        # print(Kstar.pretty_print(planner_response))

        # self.flow.add(
        #     Step(
        #         name="Agent 1",
        #         parameters=["x"],
        #     )
        # )

        # self.flow.add(
        #     Step(
        #         name="Agent 1",
        #         parameters=["x"],
        #     )
        # )

        planner_response = self.get_plan()

    def test_history_with_repeat_entries(self) -> None:
        pass

    def test_constraints_with_no_instance(self) -> None:
        pass

    def test_goal_with_no_instance(self) -> None:
        pass

    def test_goal_with_repeat_entries(self) -> None:
        pass
