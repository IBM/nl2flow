from nl2flow.debug.debug import BasicDebugger
from nl2flow.debug.schemas import ClassicalPlanReference, DiffAction, SolutionQuality
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

        agent_a = Operator(name="agent_a")
        agent_a.add_output(SignatureItem(parameters=Parameter(item_id="a_1", item_type="type_a")))

        agent_b = Operator(name="agent_b")
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
        agent_c.name = "agent_c"

        agent_d = Operator(name="agent_d")
        agent_d.add_input(SignatureItem(parameters="y"))

        goal = GoalItems(goals=GoalItem(goal_name="agent_d"))
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
        self.tokens = [
            "a_1 = agent_a()",
            "map(a_1, a)",
            "confirm(a)",
            "assert $a > 10",
            "y = agent_b(a)",
            "agent_d(y)",
        ]

    def test_token_production(self) -> None:
        stringify_tokens = "\n".join([f"[{index}] {token}" for index, token in enumerate(self.tokens)])
        planner_response = self.flow.plan_it(PLANNER)
        assert any([stringify_tokens == PLANNER.pretty_print_plan(plan) for plan in planner_response.list_of_plans])

    def test_token_parsing(self) -> None:
        reference_plan: ClassicalPlanReference = self.debugger.parse_tokens(self.tokens)
        assert reference_plan.plan == [
            Step(
                name="agent_a",
                parameters=[],
            ),
            Step(
                name=BasicOperations.MAPPER.value,
                parameters=["a_1", "a"],
            ),
            Step(
                name=BasicOperations.CONFIRM.value,
                parameters=["a"],
            ),
            Constraint(
                constraint="$a > 10",
                truth_value=True,
            ),
            Step(
                name="agent_b",
                parameters=["a"],
            ),
            Step(
                name="agent_d",
                parameters=["y"],
            ),
        ]

    def test_unsound_plan(self) -> None:
        incomplete_unsound_tokens = deepcopy(self.tokens)
        incomplete_unsound_tokens.remove("assert $a > 10")
        incomplete_unsound_tokens.remove("y = agent_b(a)")

        report = self.debugger.debug(incomplete_unsound_tokens, debug=SolutionQuality.SOUND)
        diff_string = "\n".join(report.plan_diff_str)
        print(f"\n\n{diff_string}")

        assert len([d for d in report.plan_diff_obj if d.diff_type is not None]) == 2, "Two edits"
        assert len([d for d in report.plan_diff_obj if d.diff_type == DiffAction.DELETE]) == 0, "No deletes"
        assert report.determination is False, "Reference plan is unsound"

    def test_sound_but_invalid_plan(self) -> None:
        incomplete_sound_tokens = deepcopy(self.tokens)
        incomplete_sound_tokens.remove("agent_d(y)")

        report = self.debugger.debug(incomplete_sound_tokens, debug=SolutionQuality.SOUND)
        assert len([d for d in report.plan_diff_obj if d.diff_type is not None]) == 0, "No edits"
        assert report.determination, "Reference plan is sound"

        report = self.debugger.debug(incomplete_sound_tokens, debug=SolutionQuality.VALID)

        diff_string = "\n".join(report.plan_diff_str)
        print(f"\n\n{diff_string}")

        assert len([d for d in report.plan_diff_obj if d.diff_type is not None]) == 1, "One edit"
        assert len([d for d in report.plan_diff_obj if d.diff_type == DiffAction.DELETE]) == 0, "No deletes"
        assert report.determination is False, "Reference plan is invalid"

    def test_valid_but_not_optimal_plan(self) -> None:
        valid_suboptimal_tokens = [
            "ask(y)",
            "agent_d(y)",
        ]

        report = self.debugger.debug(valid_suboptimal_tokens, debug=SolutionQuality.SOUND)
        assert len([d for d in report.plan_diff_obj if d.diff_type is not None]) == 0, "No edits"
        assert report.determination, "Reference plan is sound"

        report = self.debugger.debug(valid_suboptimal_tokens, debug=SolutionQuality.VALID)
        assert len([d for d in report.plan_diff_obj if d.diff_type is not None]) == 0, "No edits"
        assert report.determination, "Reference plan is valid"

        report = self.debugger.debug(valid_suboptimal_tokens, debug=SolutionQuality.OPTIMAL)
        diff_string = "\n".join(report.plan_diff_str)
        print(f"\n\n{diff_string}")

        assert len([d for d in report.plan_diff_obj if d.diff_type is not None]) == 6, "6 edits"
        assert len([d for d in report.plan_diff_obj if d.diff_type == DiffAction.ADD]) == 5, "5 additions"
        assert len([d for d in report.plan_diff_obj if d.diff_type == DiffAction.DELETE]) == 1, "1 delete"
        assert report.determination is False, "Reference plan is not optimal"

    def test_optimal_plan(self) -> None:
        report = self.debugger.debug(self.tokens, debug=SolutionQuality.OPTIMAL)
        diff_string = "\n".join(report.plan_diff_str)
        print(f"\n\n{diff_string}")

        assert len([d for d in report.plan_diff_obj if d.diff_type is not None]) == 0, "0 edits"
        assert report.determination, "Reference plan is optimal"

    def test_equivalent_optimal_plan(self) -> None:
        alternative_tokens = [
            "a_1 = agent_a()",
            "map(a_1, a)",
            "confirm(a)",
            "assert $a > 10",
            "y = agent_c(a)",
            "agent_d(y)",
        ]

        report = self.debugger.debug(alternative_tokens, debug=SolutionQuality.OPTIMAL)
        assert len([d for d in report.plan_diff_obj if d.diff_type is not None]) == 0, "0 edits"
        assert report.determination, "Reference plan is optimal"

    def test_invalid_tokens(self) -> None:
        messed_up_tokens = [
            "a_1 = agent_aa()",  # unknown agent
            "adsfaerafea",  # random garbage
            "amap(a_1, a)",  # unknown operation
            "map(a_1, a)",
            "a = confirm(a)",  # extra output
            "assert $aa > 10",  # typo in string
            "y = agent_c(a, a)",  # wrong number of inputs
            "a, y = agent_c(a, a)",  # wrong number of outputs
            "agent_d(y)",
        ]

        report = self.debugger.debug(messed_up_tokens, debug=SolutionQuality.SOUND)

        diff_string = "\n".join(report.plan_diff_str)
        print(f"\n\n{diff_string}")

        assert len([d for d in report.plan_diff_obj if d.diff_type is not None]) == 11, "1 edits"
        assert report.determination is False, "Reference plan is not sound"
