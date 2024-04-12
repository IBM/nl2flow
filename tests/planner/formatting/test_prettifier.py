from nl2flow.plan.planners import Kstar
from nl2flow.compile.flow import Flow
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.schemas import SignatureItem, Parameter, Constraint, GoalItems, GoalItem

PLANNER = Kstar()


class TestPrettifier:
    def setup_method(self) -> None:
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

        self.flow = Flow(name="Test Prettifier")
        self.flow.add([agent_1, agent_0, agent_b, agent_a])

    def test_prettified_plan(self) -> None:
        self.flow.add(GoalItems(goals=[GoalItem(goal_name="Agent B"), GoalItem(goal_name="Agent A")]))
        planner_response = self.flow.plan_it(PLANNER)
        pretty = PLANNER.pretty_print_plan(planner_response.list_of_plans[0])
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
        pretty = PLANNER.pretty_print(planner_response)
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

    def test_prettified_plan_verbose(self) -> None:
        self.flow.add(GoalItems(goals=[GoalItem(goal_name="Agent B"), GoalItem(goal_name="Agent A")]))
        planner_response = self.flow.plan_it(PLANNER)
        pretty = PLANNER.pretty_print_plan_verbose(planner_response.list_of_plans[0])
        print(pretty)

        if "Agent 1" in pretty:
            assert pretty.split("\n") == [
                "Step 0: ask, Inputs: b (generic), Outputs: None",
                "Step 1: Agent 1, Inputs: b (generic), Outputs: a (generic)",
                "Step 2: assert check_if_agent_0_is_done($a, $b), Inputs: None, Outputs: None",
                "Step 3: Agent A, Inputs: a (generic), b (generic), Outputs: c (type_c)",
                "Step 4: map, Inputs: c (generic), x (generic), Outputs: None",
                "Step 5: Agent B, Inputs: a (generic), b (generic), x (type_c), Outputs: None",
            ]
        elif "Agent 0" in pretty:
            assert pretty.split("\n") == [
                "Step 0: ask, Inputs: b (generic), Outputs: None",
                "Step 1: Agent 0, Inputs: b (generic), Outputs: a (generic)",
                "Step 2: assert check_if_agent_0_is_done($a, $b), Inputs: None, Outputs: None",
                "Step 3: Agent A, Inputs: a (generic), b (generic), Outputs: c (type_c)",
                "Step 4: map, Inputs: c (generic), x (generic), Outputs: None",
                "Step 5: Agent B, Inputs: a (generic), b (generic), x (type_c), Outputs: None",
            ]
        else:
            raise ValueError("Either of Agent 0 or 1 has to be there")

    def test_verbose_prettified_planner_response(self) -> None:
        self.flow.add(GoalItems(goals=[GoalItem(goal_name="Agent B"), GoalItem(goal_name="Agent A")]))
        planner_response = self.flow.plan_it(PLANNER)
        planner_response.list_of_plans = planner_response.list_of_plans[:1]
        pretty = PLANNER.pretty_print(planner_response, verbose=True)
        print(pretty)

        if "Agent 1" in pretty:
            assert pretty.strip().split("\n") == [
                "---- Plan #0 ----",
                "Cost: 165100.0, Length: 6",
                "",
                "Step 0: ask, Inputs: b (generic), Outputs: None",
                "Step 1: Agent 1, Inputs: b (generic), Outputs: a (generic)",
                "Step 2: assert check_if_agent_0_is_done($a, $b), Inputs: None, Outputs: None",
                "Step 3: Agent A, Inputs: a (generic), b (generic), Outputs: c (type_c)",
                "Step 4: map, Inputs: c (generic), x (generic), Outputs: None",
                "Step 5: Agent B, Inputs: a (generic), b (generic), x (type_c), Outputs: None",
            ]
        elif "Agent 0" in pretty:
            assert pretty.strip().split("\n") == [
                "---- Plan #0 ----",
                "Cost: 165100.0, Length: 6",
                "",
                "Step 0: ask, Inputs: b (generic), Outputs: None",
                "Step 1: Agent 0, Inputs: b (generic), Outputs: a (generic)",
                "Step 2: assert check_if_agent_0_is_done($a, $b), Inputs: None, Outputs: None",
                "Step 3: Agent A, Inputs: a (generic), b (generic), Outputs: c (type_c)",
                "Step 4: map, Inputs: c (generic), x (generic), Outputs: None",
                "Step 5: Agent B, Inputs: a (generic), b (generic), x (type_c), Outputs: None",
            ]
        else:
            raise ValueError("Either of Agent 0 or 1 has to be there")
