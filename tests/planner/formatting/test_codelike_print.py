from nl2flow.plan.planners.kstar import Kstar
from nl2flow.compile.flow import Flow
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.schemas import SignatureItem, Parameter, Constraint, GoalItems, GoalItem, Step
from nl2flow.printers.codelike import CodeLikePrint, parse_parameters

PLANNER = Kstar()


def generate_problem_for_testing_printers() -> Flow:
    agent_1 = Operator("Agent 1")
    agent_1.add_input(SignatureItem(parameters=["b"]))
    agent_1.add_output(SignatureItem(parameters="a"))

    agent_0 = Operator("Agent 0")
    agent_0.add_input(SignatureItem(parameters=["b"]))
    agent_0.add_output(SignatureItem(parameters="a"))

    agent_a = Operator("Agent A")
    agent_a.add_input(SignatureItem(parameters=["a", "b"]))
    agent_a.add_input(
        SignatureItem(
            constraints=[
                Constraint(
                    constraint="check_if_agent_0_is_done($a, $b)",
                )
            ]
        )
    )
    agent_a.add_output(SignatureItem(parameters=Parameter(item_id="c", item_type="type_c")))

    agent_b = Operator("Agent B")
    agent_b.add_input(SignatureItem(parameters=["a", "b"]))
    agent_b.add_input(SignatureItem(parameters=Parameter(item_id="x", item_type="type_c")))

    flow = Flow(name="Test Prettifier")
    flow.add([agent_1, agent_0, agent_b, agent_a])

    return flow


class TestCodeLikePrint:
    def setup_method(self) -> None:
        self.flow = generate_problem_for_testing_printers()

    def test_prettified_plan(self) -> None:
        self.flow.add(GoalItems(goals=[GoalItem(goal_name="Agent B"), GoalItem(goal_name="Agent A")]))
        planner_response = self.flow.plan_it(PLANNER)
        pretty = CodeLikePrint.pretty_print_plan(planner_response.list_of_plans[0])
        print(pretty)

        if "Agent 1" in pretty:
            assert pretty.split("\n") == [
                "[0] ask(b)",
                "[1] a = Agent 1(b)",
                "[2] assert check_if_agent_0_is_done($a, $b)",
                "[3] c = Agent A(a, b)",
                "[4] map(c, x)",
                "[5] Agent B(a, b, x)",
            ]

        elif "Agent 0" in pretty:
            assert pretty.split("\n") == [
                "[0] ask(b)",
                "[1] a = Agent 0(b)",
                "[2] assert check_if_agent_0_is_done($a, $b)",
                "[3] c = Agent A(a, b)",
                "[4] map(c, x)",
                "[5] Agent B(a, b, x)",
            ]
        else:
            raise ValueError("Either of Agent 0 or 1 has to be there")

    def test_prettified_planner_response(self) -> None:
        self.flow.add(GoalItems(goals=[GoalItem(goal_name="Agent B"), GoalItem(goal_name="Agent A")]))
        planner_response = self.flow.plan_it(PLANNER)
        planner_response.list_of_plans = planner_response.list_of_plans[:1]
        pretty = CodeLikePrint.pretty_print(planner_response)
        print(pretty)

        if "Agent 1" in pretty:
            assert pretty.strip().split("\n") == [
                "---- Plan #0 ----",
                "Cost: 165100.0, Length: 6",
                "",
                "[0] ask(b)",
                "[1] a = Agent 1(b)",
                "[2] assert check_if_agent_0_is_done($a, $b)",
                "[3] c = Agent A(a, b)",
                "[4] map(c, x)",
                "[5] Agent B(a, b, x)",
            ]
        elif "Agent 0" in pretty:
            assert pretty.strip().split("\n") == [
                "---- Plan #0 ----",
                "Cost: 165100.0, Length: 6",
                "",
                "[0] ask(b)",
                "[1] a = Agent 0(b)",
                "[2] assert check_if_agent_0_is_done($a, $b)",
                "[3] c = Agent A(a, b)",
                "[4] map(c, x)",
                "[5] Agent B(a, b, x)",
            ]
        else:
            raise ValueError("Either of Agent 0 or 1 has to be there")

    def test_prettified_plan_no_output(self) -> None:
        self.flow.add(
            GoalItems(
                goals=[GoalItem(goal_name="Agent 0"), GoalItem(goal_name="Agent B"), GoalItem(goal_name="Agent A")]
            )
        )

        planner_response = self.flow.plan_it(PLANNER)
        pretty = CodeLikePrint.pretty_print_plan(planner_response.list_of_plans[0], show_output=False)

        assert pretty.strip().split("\n") == [
            "[0] ask(b)",
            "[1] Agent 0(b)",
            "[2] assert check_if_agent_0_is_done($a, $b)",
            "[3] Agent A(a, b)",
            "[4] map(c, x)",
            "[5] Agent B(a, b, x)",
        ]

    def test_prettified_plan_start_at_1(self) -> None:
        self.flow.add(
            GoalItems(
                goals=[GoalItem(goal_name="Agent 0"), GoalItem(goal_name="Agent B"), GoalItem(goal_name="Agent A")]
            )
        )

        planner_response = self.flow.plan_it(PLANNER)
        pretty = CodeLikePrint.pretty_print_plan(planner_response.list_of_plans[0], show_output=False, start_at=1)

        assert pretty.strip().split("\n") == [
            "[1] ask(b)",
            "[2] Agent 0(b)",
            "[3] assert check_if_agent_0_is_done($a, $b)",
            "[4] Agent A(a, b)",
            "[5] map(c, x)",
            "[6] Agent B(a, b, x)",
        ]

    def test_prettified_plan_no_line_numbers(self) -> None:
        self.flow.add(
            GoalItems(
                goals=[GoalItem(goal_name="Agent 0"), GoalItem(goal_name="Agent B"), GoalItem(goal_name="Agent A")]
            )
        )

        planner_response = self.flow.plan_it(PLANNER)
        pretty = CodeLikePrint.pretty_print_plan(planner_response.list_of_plans[0], line_numbers=False)

        assert pretty.strip().split("\n") == [
            "ask(b)",
            "a = Agent 0(b)",
            "assert check_if_agent_0_is_done($a, $b)",
            "c = Agent A(a, b)",
            "map(c, x)",
            "Agent B(a, b, x)",
        ]

    def test_prettified_plan_no_output_no_line_numbers(self) -> None:
        self.flow.add(
            GoalItems(
                goals=[GoalItem(goal_name="Agent 0"), GoalItem(goal_name="Agent B"), GoalItem(goal_name="Agent A")]
            )
        )

        planner_response = self.flow.plan_it(PLANNER)
        pretty = CodeLikePrint.pretty_print_plan(
            planner_response.list_of_plans[0], line_numbers=False, show_output=False
        )

        assert pretty.strip().split("\n") == [
            "ask(b)",
            "Agent 0(b)",
            "assert check_if_agent_0_is_done($a, $b)",
            "Agent A(a, b)",
            "map(c, x)",
            "Agent B(a, b, x)",
        ]

    def test_prettified_plan_collapsed_maps(self) -> None:
        self.flow.add(
            GoalItems(
                goals=[GoalItem(goal_name="Agent 0"), GoalItem(goal_name="Agent B"), GoalItem(goal_name="Agent A")]
            )
        )

        planner_response = self.flow.plan_it(PLANNER)
        pretty = CodeLikePrint.pretty_print_plan(
            planner_response.list_of_plans[0], line_numbers=False, show_output=False, collapse_maps=True
        )

        assert pretty.strip().split("\n") == [
            "ask(b)",
            "Agent 0(b)",
            "assert check_if_agent_0_is_done($a, $b)",
            "Agent A(a, b)",
            "Agent B(a, b, c)",
        ]

    def test_parse_token(self) -> None:
        target = Step(name="a", parameters=["b", "c"])

        assert CodeLikePrint.parse_token("a(b,c)") == target
        assert CodeLikePrint.parse_token("[2] a(b,c)") == target
        assert CodeLikePrint.parse_token(" [2] a(b,c) ") == target
        assert CodeLikePrint.parse_token(" a(b,c) ") == target
        assert CodeLikePrint.parse_token("a(b, c)") == target
        assert CodeLikePrint.parse_token("x = a(b,c)") == target
        assert CodeLikePrint.parse_token(" x = a(b,c) ") == target

    def test_parse_parameters(self) -> None:
        assert parse_parameters(signature="a(b,c)") == ("a", ["b", "c"])
        assert parse_parameters(signature="a(b, c)") == ("a", ["b", "c"])
        assert parse_parameters(signature=" a(b,c) ") == ("a", ["b", "c"])

        assert parse_parameters(signature="a(c)") == ("a", ["c"])
        assert parse_parameters(signature="a()") == ("a", [])

        assert parse_parameters(signature="agent_a(b,c)") == ("agent_a", ["b", "c"])
        assert parse_parameters(signature="3a-1(b-2,c3)") == ("3a-1", ["b-2", "c3"])
