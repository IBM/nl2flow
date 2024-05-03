from nl2flow.plan.planners import Kstar
from nl2flow.compile.flow import Flow
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.schemas import SignatureItem, GoalItems, GoalItem, SlotProperty
from nl2flow.compile.options import SlotOptions, BasicOperations


class TestFlags:
    def setup_method(self) -> None:
        agent_a = Operator(name="Agent A")

        for i in range(6):
            agent_a.add_input(SignatureItem(parameters=f"a_{i}"))

        self.empty_flow = Flow(name="Empty Flow")
        self.flow = Flow(name="Test Flags")
        self.flow.slot_options.add(SlotOptions.ordered)
        self.flow.add(agent_a)
        self.PLANNER = Kstar()

    def test_error_running_planner(self) -> None:
        raw_plans = self.PLANNER.raw_plan(None)  # type: ignore

        assert len(raw_plans.list_of_plans) == 0
        assert raw_plans.error_running_planner is True
        assert raw_plans.is_no_solution is None
        assert raw_plans.is_timeout is False
        assert isinstance(raw_plans.stderr, BaseException)

    def test_empty_plan(self) -> None:
        planner_response = self.flow.plan_it(self.PLANNER)
        assert len(planner_response.list_of_plans) == 0
        assert planner_response.error_running_planner is False
        assert planner_response.is_no_solution is False
        assert planner_response.is_timeout is False
        assert planner_response.error_running_planner is False
        assert planner_response.stderr is None

    def test_no_solution(self) -> None:
        for i in range(6):
            self.flow.add(SlotProperty(slot_name=f"a_{i}", slot_desirability=0.0))

        self.flow.add(GoalItems(goals=GoalItem(goal_name="Agent A")))
        planner_response = self.flow.plan_it(self.PLANNER)

        assert len(planner_response.list_of_plans) == 0
        assert planner_response.error_running_planner is False
        assert planner_response.is_no_solution is True
        assert planner_response.is_timeout is False
        assert planner_response.error_running_planner is False
        assert planner_response.stderr is None

    def test_happy_situation(self) -> None:
        self.flow.add(GoalItems(goals=GoalItem(goal_name="Agent A")))
        planner_response = self.flow.plan_it(self.PLANNER)
        print(self.PLANNER.pretty_print(planner_response))

        assert len(planner_response.list_of_plans) == 1
        assert planner_response.is_timeout is False
        assert planner_response.is_no_solution is False
        assert planner_response.error_running_planner is False
        assert planner_response.is_parse_error is False
        assert planner_response.stderr is None

        plan = planner_response.list_of_plans[0]
        assert all([step.name == BasicOperations.SLOT_FILLER.value for step in plan.plan[:-1]])

        slot_order = [step.inputs[0] for step in plan.plan[:-1]]
        assert slot_order == ["a_0", "a_1", "a_2", "a_3", "a_4", "a_5"]

    def test_timeout(self) -> None:
        self.PLANNER.timeout = 1

        self.flow.add(GoalItems(goals=GoalItem(goal_name="Agent A")))
        planner_response = self.flow.plan_it(self.PLANNER)

        assert len(planner_response.list_of_plans) == 0
        assert planner_response.is_timeout is True
        assert planner_response.is_no_solution is None
        assert planner_response.error_running_planner is None
        assert planner_response.is_parse_error is False
        assert isinstance(planner_response.stderr, BaseException)

    def test_parse_error(self) -> None:
        self.flow.add(GoalItems(goals=GoalItem(goal_name="Agent A")))
        pddl, transforms = self.flow.compile_to_pddl()
        planner_response = self.PLANNER.plan(pddl, flow=self.empty_flow, transforms=transforms)

        assert len(planner_response.list_of_plans) == 0
        assert planner_response.is_timeout is False
        assert planner_response.is_no_solution is False
        assert planner_response.error_running_planner is False
        assert planner_response.is_parse_error is True
        assert isinstance(planner_response.stderr, BaseException)
