from nl2flow.debug.debug import BasicDebugger
from nl2flow.debug.schemas import ClassicalPlanReference
from nl2flow.compile.flow import Flow
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.schemas import SignatureItem, Parameter, Constraint, GoalItems, GoalItem
from nl2flow.compile.options import LifeCycleOptions, BasicOperations
from nl2flow.plan.schemas import Step
from nl2flow.plan.planners import Kstar
from copy import deepcopy

PLANNER = Kstar()


class TestBasic:
    def setup_method(self) -> None:
        self.flow = Flow("Debug Test")
        self.flow.variable_life_cycle.add(LifeCycleOptions.confirm_on_mapping)

        agent_a = Operator(name="Agent A")
        agent_a.add_output(SignatureItem(parameters=Parameter(item_id="a_star", item_type="type_a")))

        agent_b = Operator(name="Agent B")
        agent_b.add_output(SignatureItem(parameters="y"))
        agent_b.add_input(SignatureItem(parameters=Parameter(item_id="a", item_type="type_a")))
        agent_b.add_input(
            SignatureItem(
                constraints=[
                    Constraint(
                        constraint="$a > 10",
                    )
                ]
            )
        )

        agent_c = deepcopy(agent_b)
        agent_c.name = "Agent C"

        agent_d = Operator(name="Agent D")
        agent_d.add_input(SignatureItem(parameters="y"))

        goal = GoalItems(goals=GoalItem(goal_name="Agent D"))
        self.flow.add(
            [
                agent_a,
                agent_b,
                agent_c,
                agent_d,
                goal,
            ]
        )

        self.debugger = BasicDebugger(self.flow)

    def test_token_production(self) -> None:
        tokens = [
            "a_star = Agent A",
            "map(a_star, a)",
            "confirm(a)",
            "assert $a > 10",
            "y = Agent B(a)",
            "Agent D(y)",
        ]

        stringify_tokens = "\n".join([f"[{index}] {token}" for index, token in enumerate(tokens)])
        planner_response = self.flow.plan_it(PLANNER)

        assert any([stringify_tokens == PLANNER.pretty_print_plan(plan) for plan in planner_response.list_of_plans])

    def test_token_parsing(self) -> None:
        tokens = [
            "a_star = Agent A",
            "map(a_star, a)",
            "confirm(a)",
            "assert $a > 10",
            "y = Agent B(a)",
            "Agent D(y)",
        ]

        reference_plan: ClassicalPlanReference = self.debugger.parse_tokens(tokens)
        assert reference_plan.plan == [
            Step(
                name="Agent A",
                parameters=[],
            ),
            Step(
                name=BasicOperations.MAPPER.value,
                parameters=["a_star", "a"],
            ),
            Step(
                name=BasicOperations.CONFIRM.value,
                parameters=["a"],
            ),
            Step(
                name=BasicOperations.CONSTRAINT.value,
                parameters=["a", "True"],
            ),
            Step(
                name="Agent B",
                parameters=["a"],
            ),
            Step(
                name="Agent D",
                parameters=["y"],
            ),
        ]

    def test_unsound_plan(self) -> None:
        # ask(z)
        # xx = A(z)
        # x = map(x)
        # confirm(x)
        # y = B(x)
        # D(y, z)
        pass

    def test_sound_but_invalid_plan(self) -> None:
        # xx = A(z)
        # x = map(x)
        # confirm(x)
        # assert check_x(x)
        # y = B(x, z)
        pass

    def test_valid_but_not_optimal_plan(self) -> None:
        # ask(y)
        # y = B(x, z)
        pass

    def test_optimal_plan(self) -> None:
        # xx = A(z)
        # x = map(x)
        # confirm(x)
        # assert x > 10
        # y = B(x, z)
        # D(y)
        pass

    def test_equivalent_optimal_plan(self) -> None:
        # xx = A(z)
        # x = map(x)
        # confirm(x)
        # assert check_x(x)
        # y = C(x, z)
        # D(y)
        pass

    def test_invalid_tokens(self) -> None:
        pass
