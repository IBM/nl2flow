from nl2flow.plan.planners.kstar import Kstar
from nl2flow.compile.flow import Flow
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.schemas import SignatureItem, Parameter, Constraint, GoalItems, GoalItem
from nl2flow.printers.verbalize import VerbalizePrint

PLANNER = Kstar()


class TestVerbalizePrint:
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

    def test_prettified_plan_verbalize(self) -> None:
        self.flow.add(GoalItems(goals=[GoalItem(goal_name="Agent B"), GoalItem(goal_name="Agent A")]))
        planner_response = self.flow.plan_it(PLANNER)
        pretty = VerbalizePrint.pretty_print_plan(planner_response.list_of_plans[0], flow_object=self.flow)
        print(pretty)

    def test_prettified_plan_verbalize_with_object(self) -> None:
        pass

    def test_prettified_plan_verbalize_with_constraint(self) -> None:
        pass

    def test_prettified_plan_verbalize_with_groups(self) -> None:
        pass
