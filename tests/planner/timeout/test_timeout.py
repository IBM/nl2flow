from nl2flow.compile.flow import Flow
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.schemas import SignatureItem, GoalItems, GoalItem
from nl2flow.compile.options import GoalType, SlotOptions
from nl2flow.plan.planners.kstar import Kstar
from nl2flow.debug.debug import BasicDebugger
from nl2flow.debug.schemas import SolutionQuality

PLANNER = Kstar()


class TestTimeout:
    def setup_method(self) -> None:
        self.flow = Flow(name="Test Flow")
        self.flow.slot_options.add(SlotOptions.last_resort)

        self.operator = Operator(name="operator with many parameters")
        self.operator.add_input(SignatureItem(parameters=["a", "b", "c", "d", "x", "y", "z"]))
        self.operator.add_output(SignatureItem(parameters=["p"]))

        goal = GoalItems(goals=GoalItem(goal_name="p", goal_type=GoalType.OBJECT_KNOWN))
        self.flow.add(goal)

    def test_normal_with_timeout(self) -> None:
        operator = Operator(name="small operator")
        operator.add_input(SignatureItem(parameters=["a", "b", "c"]))
        operator.add_output(SignatureItem(parameters=["p"]))

        self.flow.add(operator)

        result_without_timeout = self.flow.plan_it(PLANNER)
        result_with_timeout = self.flow.plan_it(PLANNER, timeout=5)

        assert result_with_timeout.best_plan is not None
        assert result_with_timeout.best_plan == result_without_timeout.best_plan

    def test_planner_timeout(self) -> None:
        self.flow.add(self.operator)
        result = self.flow.plan_it(PLANNER, timeout=5)

        assert result.best_plan is None
        assert result.is_timeout is True

    def test_debugger_timeout(self) -> None:
        self.flow.add(self.operator)

        tokens = [
            "operator with many parameters(a, b, c, d, x, y, z)",
        ]

        debugger = BasicDebugger(self.flow)
        report = debugger.debug(tokens, report_type=SolutionQuality.SOUND, timeout=5)

        assert report.determination is None
        assert report.planner_response.is_timeout is True
