from nl2flow.debug.debug import BasicDebugger
from nl2flow.debug.schemas import ClassicalPlanReference, DiffAction, SolutionQuality
from nl2flow.compile.flow import Flow
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.schemas import SignatureItem, Parameter, Constraint, GoalItems, GoalItem, Step
from nl2flow.compile.options import LifeCycleOptions, BasicOperations
from nl2flow.plan.planners.kstar import Kstar
from nl2flow.printers.codelike import CodeLikePrint
from tests.debugger.custom_formatter.custom_print import CustomPrint
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

        agent_e = Operator(name="agent_e")
        agent_e.add_input(SignatureItem(parameters=["i1", "i2"]))
        agent_e.add_output(SignatureItem(parameters=["o1", "o2", "y"]))

        goal = GoalItems(goals=GoalItem(goal_name="agent_d"))
        self.flow.add(
            [
                agent_a,
                agent_b,
                agent_c,
                agent_d,
                agent_e,
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
        assert any(
            [stringify_tokens == CodeLikePrint.pretty_print_plan(plan) for plan in planner_response.list_of_plans]
        )

    def test_token_parsing(self) -> None:
        reference_plan: ClassicalPlanReference = CodeLikePrint.parse_tokens(self.tokens)
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

        report = self.debugger.debug(incomplete_unsound_tokens, report_type=SolutionQuality.SOUND)
        diff_string = "\n".join(report.plan_diff_str)
        print(f"\n\n{diff_string}")

        assert len([d for d in report.plan_diff_obj if d.diff_type is not None]) == 2, "Two edits"
        assert len([d for d in report.plan_diff_obj if d.diff_type == DiffAction.DELETE]) == 0, "No deletes"
        assert report.determination is False, "Reference plan is unsound"

    def test_sound_but_invalid_plan(self) -> None:
        incomplete_sound_tokens = deepcopy(self.tokens)
        incomplete_sound_tokens.remove("agent_d(y)")

        report = self.debugger.debug(incomplete_sound_tokens, report_type=SolutionQuality.SOUND)
        assert len([d for d in report.plan_diff_obj if d.diff_type is not None]) == 0, "No edits"
        assert report.determination, "Reference plan is sound"

        report = self.debugger.debug(incomplete_sound_tokens, report_type=SolutionQuality.VALID)

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

        report = self.debugger.debug(valid_suboptimal_tokens, report_type=SolutionQuality.SOUND)
        assert len([d for d in report.plan_diff_obj if d.diff_type is not None]) == 0, "No edits"
        assert report.determination, "Reference plan is sound"

        report = self.debugger.debug(valid_suboptimal_tokens, report_type=SolutionQuality.VALID)
        assert len([d for d in report.plan_diff_obj if d.diff_type is not None]) == 0, "No edits"
        assert report.determination, "Reference plan is valid"

        report = self.debugger.debug(valid_suboptimal_tokens, report_type=SolutionQuality.OPTIMAL)
        diff_string = "\n".join(report.plan_diff_str)
        print(f"\n\n{diff_string}")

        assert len([d for d in report.plan_diff_obj if d.diff_type is not None]) == 6, "6 edits"
        assert len([d for d in report.plan_diff_obj if d.diff_type == DiffAction.ADD]) == 5, "5 additions"
        assert len([d for d in report.plan_diff_obj if d.diff_type == DiffAction.DELETE]) == 1, "1 delete"
        assert report.determination is False, "Reference plan is not optimal"

    def test_optimal_plan(self) -> None:
        report = self.debugger.debug(self.tokens, report_type=SolutionQuality.OPTIMAL)
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

        report = self.debugger.debug(alternative_tokens, report_type=SolutionQuality.OPTIMAL)
        assert len([d for d in report.plan_diff_obj if d.diff_type is not None]) == 0, "0 edits"
        assert report.determination, "Reference plan is optimal"

    def test_optimal_plan_without_outputs(self) -> None:
        alternative_tokens = [
            "agent_a()",
            "map(a_1, a)",
            "confirm(a)",
            "assert $a > 10",
            "agent_c(a)",
            "agent_d(y)",
        ]

        report = self.debugger.debug(alternative_tokens, report_type=SolutionQuality.OPTIMAL, show_output=False)
        assert len([d for d in report.plan_diff_obj if d.diff_type is not None]) == 0, "0 edits"
        assert report.determination, "Reference plan is optimal"

    def test_optimal_plan_with_collapsed_maps(self) -> None:
        alternative_tokens = [
            "a_1 = agent_a()",
            "confirm(a_1)",
            "assert $a_1 > 10",
            "y = agent_c(a_1)",
            "agent_d(y)",
        ]

        report = self.debugger.debug(alternative_tokens, report_type=SolutionQuality.OPTIMAL, collapse_maps=True)

        diff_string = "\n".join(report.plan_diff_str)
        print(f"\n\n{diff_string}")

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

        report = self.debugger.debug(messed_up_tokens, report_type=SolutionQuality.SOUND)

        diff_string = "\n".join(report.plan_diff_str)
        print(f"\n\n{diff_string}")

        assert len([d for d in report.plan_diff_obj if d.diff_type is not None]) == 11, "1 edits"
        assert report.determination is False, "Reference plan is not sound"

    def test_custom_formatter(self) -> None:
        alternative_tokens = [
            "agent_a() -> a_1",
            "map a_1 -> a",
            "confirm a",
            "check if $a > 10 is True",
            "agent_c(a) -> y",
            "agent_d(y)",
        ]

        for mode in SolutionQuality:
            report = self.debugger.debug(alternative_tokens, report_type=mode, printer=CustomPrint())
            diff_string = "\n".join(report.plan_diff_str)
            print(f"\n\n{diff_string}")

            assert report.determination, f"Reference plan is {mode.value}"

    def test_optional_parameter(self) -> None:
        agent_x = Operator(name="agent_x")
        agent_x.add_input(SignatureItem(parameters=Parameter(item_id="x_1", required=False)))
        agent_x.add_output(SignatureItem(parameters="y"))

        self.flow.add(agent_x)

        messed_up_tokens = [
            "ask(x_1)",
            "y = agent_x(x_1)",
            "agent_d(y)",
        ]

        report = self.debugger.debug(messed_up_tokens, report_type=SolutionQuality.VALID)

        diff_string = "\n".join(report.plan_diff_str)
        print(f"\n\n{diff_string}")

        assert report.determination

    def test_disorder_in_input(self) -> None:
        goal = GoalItems(goals=[GoalItem(goal_name="agent_d"), GoalItem(goal_name="agent_e")])
        self.flow.add(goal)

        tokens = [
            "ask(i1)",
            "ask(i2)",
            # Should have been: "o1, o2, y = agent_e(i1, i2)"
            "o1, o2, y = agent_e(i2, i1)",
            "agent_d(y)",
        ]

        report = self.debugger.debug(tokens, report_type=SolutionQuality.SOUND)
        assert report.determination is None

    def test_disorder_with_output(self) -> None:
        goal = GoalItems(goals=[GoalItem(goal_name="agent_d"), GoalItem(goal_name="agent_e")])
        self.flow.add(goal)

        tokens = [
            "ask(i1)",
            "ask(i2)",
            # Should have been: "o1, o2, y = agent_e(i1, i2)"
            "o1, y, o2 = agent_e(i1, i2)",
            "agent_d(y)",
        ]

        report = self.debugger.debug(tokens, report_type=SolutionQuality.SOUND)

        diff_string = "\n".join(report.plan_diff_str)
        print(f"\n\n{diff_string}")

        assert report.determination is False

    def test_disorder_without_output(self) -> None:
        goal = GoalItems(goals=[GoalItem(goal_name="agent_d"), GoalItem(goal_name="agent_e")])
        self.flow.add(goal)

        tokens = [
            "ask(i1)",
            "ask(i2)",
            "agent_e(i1, i2)",
            "agent_d(y)",
        ]

        report = self.debugger.debug(tokens, report_type=SolutionQuality.SOUND, show_output=False)

        diff_string = "\n".join(report.plan_diff_str)
        print(f"\n\n{diff_string}")

        assert report.determination is True

    def test_disorder_ignore_output(self) -> None:
        goal = GoalItems(goals=[GoalItem(goal_name="agent_d"), GoalItem(goal_name="agent_e")])
        self.flow.add(goal)

        tokens = [
            "ask(i1)",
            "ask(i2)",
            # Should have been: "o1, o2, y = agent_e(i1, i2)"
            "o1, y, o2 = agent_e(i1, i2)",
            # NOTE: This plan will fail while executing because y would have taken the value intended for o2
            "agent_d(y)",
        ]

        report = self.debugger.debug(tokens, report_type=SolutionQuality.SOUND, show_output=None)

        diff_string = "\n".join(report.plan_diff_str)
        print(f"\n\n{diff_string}")

        assert report.determination is True
