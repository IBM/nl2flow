from nl2flow.debug.debug import BasicDebugger
from nl2flow.debug.schemas import SolutionQuality
from nl2flow.compile.flow import Flow
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.schemas import SignatureItem, SlotProperty, MappingItem, MemoryItem, GoalItems, GoalItem
from nl2flow.compile.options import MemoryState, MappingOptions, NL2FlowOptions
from nl2flow.plan.planners.kstar import Kstar

PLANNER = Kstar()


class TestLLMParsing:
    def setup_method(self) -> None:
        self.flow = Flow("LLM")
        self.flow.mapping_options.add(MappingOptions.transitive)
        self.flow.optimization_options.remove(NL2FlowOptions.multi_instance)
        self.flow.optimization_options.remove(NL2FlowOptions.allow_retries)

        self.debugger = BasicDebugger(self.flow)

    def test_1(self) -> None:
        a__0 = Operator("a__0")
        a__0.add_input(SignatureItem(parameters="v__0"))
        a__0.add_output(SignatureItem(parameters="v__2"))

        a__1 = Operator("a__1")
        a__1.add_input(SignatureItem(parameters="v__2"))
        a__1.add_output(SignatureItem(parameters="v__1"))

        self.flow.add(
            [
                a__0,
                a__1,
                SlotProperty(slot_name="v__0", slot_desirability=0.0),
                SlotProperty(slot_name="v__1", slot_desirability=0.0),
                SlotProperty(slot_name="v__2", slot_desirability=0.0),
                MemoryItem(item_id="v__3", item_state=MemoryState.KNOWN),
                MappingItem(source_name="v__1", target_name="v__0"),
                MappingItem(source_name="v__0", target_name="v__3"),
                GoalItems(goals=GoalItem(goal_name="a__1")),
            ]
        )

        llm_plan = ["v__2 = a__0(v__0)", "v__1 = a__1(v__2)"]

        report = self.debugger.debug(llm_plan, report_type=SolutionQuality.VALID)
        diff_string = "\n".join(report.plan_diff_str)
        print(f"\n\n{diff_string}")

    def test_2(self) -> None:
        a__0 = Operator("a__0")
        a__0.add_input(SignatureItem(parameters="v__0"))
        a__0.add_output(SignatureItem(parameters="v__2"))

        a__1 = Operator("a__1")
        a__1.add_input(SignatureItem(parameters="v__2"))
        a__1.add_output(SignatureItem(parameters="v__3"))

        a__2 = Operator("a__2")
        a__2.add_input(SignatureItem(parameters="v__3"))
        a__2.add_output(SignatureItem(parameters="v__1"))

        self.flow.add([a__0, a__1, a__2, GoalItems(goals=GoalItem(goal_name="a__1"))])

        llm_plan = ["ask(v__0)", "v__2 = a__0(v__0)", "a__1(v__2)"]

        report = self.debugger.debug(llm_plan, report_type=SolutionQuality.VALID)
        diff_string = "\n".join(report.plan_diff_str)
        print(f"\n\n{diff_string}")
