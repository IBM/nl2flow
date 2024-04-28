from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.schemas import GoalItem, GoalItems, SignatureItem
from nl2flow.compile.options import NL2FlowOptions, SlotOptions
from tests.testing import BaseTestAgents


class TestBasicButNotBasic(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)
        self.flow.optimization_options.remove(NL2FlowOptions.multi_instance)
        self.flow.optimization_options.remove(NL2FlowOptions.allow_retries)
        self.flow.slot_options.add(SlotOptions.last_resort)

    def test_lots_of_parameters(self) -> None:
        agent_a = Operator(name="Agent A")
        agent_a.add_input(SignatureItem(parameters=["a", "b", "c", "d", "e", "f"]))

        agent_b = Operator(name="Agent X")
        agent_b.add_input(SignatureItem(parameters=["x", "y", "z", "p", "q", "r", "s"]))

        self.flow.add([agent_b, agent_a])
        self.flow.add(GoalItems(goals=[GoalItem(goal_name="Agent A"), GoalItem(goal_name="Agent X")]))

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

    def test_basic_plan_is_the_same(self) -> None:
        goal = GoalItems(goals=GoalItem(goal_name="Fix Errors"))
        self.flow.add(goal)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

    def test_constraints_with_no_instance(self) -> None:
        pass

    def test_goal_with_no_instance(self) -> None:
        pass

    def test_goal_with_repeat_entries(self) -> None:
        pass

    def test_history_with_no_instance(self) -> None:
        pass

    def test_history_with_repeat_entries(self) -> None:
        pass
