from nl2flow.compile.operators import ClassicalOperator as Operator, OperatorDefinition
from nl2flow.compile.flow import Flow
from nl2flow.compile.schemas import (
    GoalItem,
    GoalItems,
    SlotProperty,
    SignatureItem,
    MemoryItem,
    Step,
)

from nl2flow.compile.options import (
    LifeCycleOptions,
    MemoryState,
    SlotOptions,
    GoalType,
)

from nl2flow.plan.planners.kstar import Kstar
from nl2flow.printers.codelike import CodeLikePrint
from nl2flow.debug.debug import BasicDebugger
from nl2flow.debug.schemas import SolutionQuality

PLANNER = Kstar()


class TestMonday:
    def setup_method(self) -> None:
        self.flow = Flow("Monday")
        self.flow.slot_options.add(SlotOptions.last_resort)

        w3_agent = Operator(name="w3")
        w3_agent.add_input(SignatureItem(parameters=["email"]))
        w3_agent.add_output(SignatureItem(parameters=["name", "employee_id", "manager", "peers"]))

        aw_1 = Operator(name="aw/{conf_id}")
        aw_1.add_input(SignatureItem(parameters=["conf_id"]))
        aw_1.add_output(SignatureItem(parameters=["papers"]))

        aw_2 = Operator(name="aw/{name}")
        aw_2.add_input(SignatureItem(parameters=["name"]))
        aw_2.add_output(SignatureItem(parameters=["papers"]))

        self.flow.add([w3_agent, aw_1, aw_2])
        self.flow.add(GoalItems(goals=GoalItem(goal_name="papers", goal_type=GoalType.OBJECT_KNOWN)))

    def print_plan(self) -> None:
        plans = self.flow.plan_it(PLANNER)
        print()
        print(CodeLikePrint.pretty_print_plan(plans.list_of_plans[0]))

    def test_first_plan(self) -> None:
        self.print_plan()

    def test_other_plan(self) -> None:
        the_other_plan = [
            "ask(email)",
            "name, employee_id, manager, peers = w3(email)",
            "papers = aw/{name}(name)",
        ]

        debugger = BasicDebugger(self.flow)
        report = debugger.debug(the_other_plan, debug=SolutionQuality.VALID)
        assert report.determination

        report = debugger.debug(the_other_plan, debug=SolutionQuality.OPTIMAL)
        assert report.determination is False

    def test_progression_of_first_plan(self) -> None:
        self.flow.add(MemoryItem(item_id="conf_id", item_state=MemoryState.KNOWN))
        self.print_plan()

    def test_already_tried_conf_id_endpoint_once(self) -> None:
        self.flow.add(
            [
                MemoryItem(item_id="conf_id", item_state=MemoryState.KNOWN),
                Step(name="aw/{conf_id}", parameters=["conf_id"]),
            ]
        )

        self.print_plan()

    def test_already_tried_conf_id_endpoint_once_with_retry(self) -> None:
        aw_2: OperatorDefinition = next(filter(lambda o: o.name == "aw/{conf_id}", self.flow.flow_definition.operators))
        aw_2.max_try = 4

        self.flow.add(
            [
                MemoryItem(item_id="conf_id", item_state=MemoryState.KNOWN),
                Step(name="aw/{conf_id}", parameters=["conf_id"]),
                Step(name="aw/{conf_id}", parameters=["conf_id"]),
                Step(name="aw/{conf_id}", parameters=["conf_id"]),
                Step(name="aw/{conf_id}", parameters=["conf_id"]),
            ]
        )

        self.print_plan()

    def test_already_tried_conf_id_endpoint_once_with_retry_and_slot_ban(self) -> None:
        aw_2: OperatorDefinition = next(filter(lambda o: o.name == "aw/{conf_id}", self.flow.flow_definition.operators))
        aw_2.max_try = 2

        self.flow.add(
            [
                MemoryItem(item_id="conf_id", item_state=MemoryState.KNOWN),
                Step(name="aw/{conf_id}", parameters=["conf_id"]),
                Step(name="aw/{conf_id}", parameters=["conf_id"]),
                SlotProperty(slot_name="email", slot_desirability=0),
            ]
        )

        self.print_plan()

    def test_first_plan_with_defensive_execution(self) -> None:
        aw_2: OperatorDefinition = next(filter(lambda o: o.name == "aw/{conf_id}", self.flow.flow_definition.operators))
        aw_2.max_try = 1

        self.flow.add(
            [
                MemoryItem(item_id="conf_id", item_state=MemoryState.KNOWN),
                Step(name="aw/{conf_id}", parameters=["conf_id"]),
            ]
        )

        self.flow.variable_life_cycle.add(LifeCycleOptions.confirm_on_slot)
        self.flow.variable_life_cycle.add(LifeCycleOptions.confirm_on_determination)

        self.print_plan()
