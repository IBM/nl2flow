from nl2flow.plan.planners.kstar import Kstar
from nl2flow.compile.schemas import GoalItems, GoalItem, MappingItem, MemoryItem, Constraint
from nl2flow.compile.options import GoalType, MemoryState
from nl2flow.printers.codelike import CodeLikePrint
from nl2flow.printers.explain import ExplainPrint
from tests.planner.formatting.test_codelike_print import generate_problem_for_testing_printers

PLANNER = Kstar()


class TestExplainPrint:
    def setup_method(self) -> None:
        self.flow = generate_problem_for_testing_printers()

    def test_explain_print(self) -> None:
        self.flow.add(GoalItems(goals=[GoalItem(goal_name="Agent B"), GoalItem(goal_name="Agent A")]))
        planner_response = self.flow.plan_it(PLANNER)
        pretty = ExplainPrint.pretty_print_plan(planner_response.best_plan, flow_object=self.flow)

        print(CodeLikePrint.pretty_print_plan(planner_response.best_plan))
        print(pretty)

        pretty_split = pretty.split("\n")

        assert pretty_split == [
            "The goal of the plan is to execute action Agent B and execute action Agent A.",
            "In order to execute Agent B, the values of its parameters a, b, and x must be known.",
            "The value of a is acquired from action Agent 1.",
            "In order to execute Agent 1, the values of its parameters b must be known.",
            "The value of b is acquired by asking the user.",
            "The value of x is acquired by mapping from the value of variable c.",
            "The value of c is acquired from action Agent A.",
            "In order to execute Agent A, the values of its parameters a and b must be known.",
            "Values of a and b have already been acquired by the rest of the plan.",
            "check_if_agent_0_is_done($a, $b) is required to be True.",
            "This is required by Agent A.",
            "To evaluate the constraint, the values of its parameters a and b must be known.",
            "Values of a and b have already been acquired by the rest of the plan.",
        ]

    def test_explain_object_acquired_as_goal(self) -> None:
        self.flow.add(
            GoalItems(goals=[GoalItem(goal_name="Agent B"), GoalItem(goal_name="c", goal_type=GoalType.OBJECT_KNOWN)])
        )

        planner_response = self.flow.plan_it(PLANNER)
        pretty = ExplainPrint.pretty_print_plan(planner_response.best_plan, flow_object=self.flow)

        print(CodeLikePrint.pretty_print_plan(planner_response.best_plan))
        print(pretty)

        pretty_split = pretty.split("\n")
        assert pretty_split == [
            "The goal of the plan is to execute action Agent B and acquire the value of variable c.",
            "In order to execute Agent B, the values of its parameters a, b, and x must be known.",
            "The value of a is acquired from action Agent 1.",
            "In order to execute Agent 1, the values of its parameters b must be known.",
            "The value of b is acquired by asking the user.",
            "The value of x is acquired by mapping from the value of variable c.",
            "The value of c is acquired from action Agent A.",
            "Action Agent A produces c which is a goal of the plan.",
            "In order to execute Agent A, the values of its parameters a and b must be known.",
            "Values of a and b have already been acquired by the rest of the plan.",
            "check_if_agent_0_is_done($a, $b) is required to be True.",
            "This is required by Agent A.",
            "To evaluate the constraint, the values of its parameters a and b must be known.",
            "Values of a and b have already been acquired by the rest of the plan.",
        ]

    def test_explain_object_used_as_goal(self) -> None:
        self.flow.add(
            [
                MemoryItem(item_id="id123", item_state=MemoryState.KNOWN),
                MemoryItem(item_id="id345", item_state=MemoryState.KNOWN),
                MappingItem(source_name="id123", target_name="a"),
                MappingItem(source_name="id345", target_name="b"),
                GoalItems(
                    goals=[
                        GoalItem(goal_name="id123", goal_type=GoalType.OBJECT_USED),
                        GoalItem(goal_name="id345", goal_type=GoalType.OBJECT_USED),
                    ]
                ),
            ]
        )

        planner_response = self.flow.plan_it(PLANNER)
        pretty = ExplainPrint.pretty_print_plan(planner_response.best_plan, flow_object=self.flow)

        print(CodeLikePrint.pretty_print_plan(planner_response.best_plan))
        print(pretty)

        pretty_split = pretty.split("\n")
        assert pretty_split == [
            "The goal of the plan is to operate on the variable id123 and operate on the variable id345.",
            "In order to execute Agent A, the values of its parameters a and b must be known.",
            "The value of a is acquired by mapping from the value of variable id123.",
            "The value of b is acquired by mapping from the value of variable id345.",
            "check_if_agent_0_is_done($a, $b) is required to be True.",
            "This is required by Agent A.",
            "To evaluate the constraint, the values of its parameters a and b must be known.",
            "Values of a and b have already been acquired by the rest of the plan.",
        ]

    def test_explain_constraint_as_goal(self) -> None:
        self.flow.add(
            GoalItems(
                goals=[
                    GoalItem(
                        goal_name=Constraint(constraint="check_if_agent_0_is_done($a, $b)"),
                        goal_type=GoalType.CONSTRAINT,
                    )
                ]
            )
        )

        planner_response = self.flow.plan_it(PLANNER)
        pretty = ExplainPrint.pretty_print_plan(planner_response.best_plan, flow_object=self.flow)

        print(CodeLikePrint.pretty_print_plan(planner_response.best_plan))
        print(pretty)

        pretty_split = pretty.split("\n")
        assert pretty_split == [
            "The goal of the plan is to check check_if_agent_0_is_done($a, $b).",
            "check_if_agent_0_is_done($a, $b) is required to be True.",
            "To evaluate the constraint, the values of its parameters a and b must be known.",
            "The value of a is acquired from action Agent 1.",
            "In order to execute Agent 1, the values of its parameters b must be known.",
            "The value of b is acquired by asking the user.",
        ]
