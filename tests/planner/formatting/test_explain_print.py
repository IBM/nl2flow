from nl2flow.plan.planners.kstar import Kstar
from nl2flow.compile.schemas import GoalItems, GoalItem
from nl2flow.printers.explain import ExplainPrint
from tests.planner.formatting.test_codelike_print import generate_problem_for_testing_printers

PLANNER = Kstar()


class TestVerbalizePrint:
    def setup_method(self) -> None:
        self.flow = generate_problem_for_testing_printers()

    def test_explain_print(self) -> None:
        self.flow.add(GoalItems(goals=[GoalItem(goal_name="Agent B"), GoalItem(goal_name="Agent A")]))
        planner_response = self.flow.plan_it(PLANNER)
        pretty = ExplainPrint.pretty_print_plan(planner_response.list_of_plans[0], flow_object=self.flow)
        print(pretty)

        pretty_split = pretty.split("\n")

        assert pretty_split == [
            "The goal of the plan is to execute action Agent B and to execute action Agent A.",
            "In order to execute Agent B, the values of its parameters a, b, and x must be known.",
            "The value of a is acquired from action Agent 1.",
            "In order to execute Agent 1, the values of its parameters b must be known.",
            "The value of b is acquired by asking the user.",
            "The value of x is acquired by mapping from the value of variable c.",
            "The value of c is acquired from action Agent A.",
            "In order to execute Agent A, the values of its parameters a and b must be known.",
            "Values of a and b have already been acquired by the rest of the plan.",
            "check_if_agent_0_is_done($a, $b) is required to be True. This is required by Agent A.",
        ]
