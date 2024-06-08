from nl2flow.plan.planners.kstar import Kstar
from nl2flow.compile.schemas import GoalItems, GoalItem
from nl2flow.printers.verbalize import VerbalizePrint
from tests.planner.formatting.test_codelike_print import generate_problem_for_testing_printers

PLANNER = Kstar()


class TestVerbalizePrint:
    def setup_method(self) -> None:
        self.flow = generate_problem_for_testing_printers()

    def test_explain_print(self) -> None:
        self.flow.add(GoalItems(goals=[GoalItem(goal_name="Agent B"), GoalItem(goal_name="Agent A")]))
        planner_response = self.flow.plan_it(PLANNER)
        pretty = VerbalizePrint.pretty_print_plan(planner_response.list_of_plans[0], flow_object=self.flow)
        print(pretty)

        pretty_split = pretty.split("\n")

        assert pretty_split == [
            "Executing Agent B and Agent A is the goal of the plan."
            "In order to execute Agent B we need to acquire the values of its inputs a, b, and x.",
            "The value of a is acquired from Agent 0.",
            "Agent 0 requires the value of b as its input.",
            "The value of b is acquired by asking the user.",
            "The value of x is acquired from c.",
            "The value of c is acquired from Agent A which is also a goal of this plan.",
            "Agent A requires the values a and b as its inputs.",
            "The value of a is acquired from Agent 0.",
            "Agent 0 requires the value of b as its input.",
            "The value of b is acquired by asking the user.",
            "check_if_agent_0_is_done($a, $b) is required to be True to execute Agent A.",
        ]
