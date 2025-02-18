# from tests.testing import BaseTestAgents
# from nl2flow.plan.schemas import Action, PlannerResponse
# from nl2flow.printers.codelike import CodeLikePrint
# from nl2flow.compile.flow import Flow
# from nl2flow.compile.operators import ClassicalOperator as Operator
# from nl2flow.compile.options import BasicOperations, MappingOptions, NL2FlowOptions, ConstraintState, MemoryState
# from nl2flow.compile.schemas import (
#     Parameter,
#     SlotProperty,
#     GoalItem,
#     GoalItems,
#     MappingItem,
#     SignatureItem,
#     MemoryItem,
#     Constraint,
# )
#
#
# class TestEnum(BaseTestAgents):
#     def setup_method(self) -> None:
#         BaseTestAgents.setup_method(self)
#
#         self.flow = Flow("TestEnum")
#         self.flow.optimization_options.remove(NL2FlowOptions.multi_instance)
#         self.flow.optimization_options.remove(NL2FlowOptions.allow_retries)
#
#         agent = Operator("test_agent")
#         agent.add_input(
#             SignatureItem(
#                 parameters=[
#                     # Parameter(item_id="x", allowed_valeus=['x\"', "\"He said what??\"", 'What\'s going on?']),
#                     Parameter(item_id="x", allowed_valeus=["one", "two", "three"]),
#                 ]
#             )
#         )
#
#         self.flow.add(agent)
#
#     def test_direct_usage(self) -> None:
#         self.flow.add(GoalItems(goals=GoalItem(goal_name="test_agent")))
#
#         self.flow.add(MemoryItem(item_id="one"))
#         self.flow.add(MappingItem(source_name="one", target_name="x", is_mapped=True))
#
#         plans = self.get_plan()
#         assert plans.best_plan
#         assert len(plans.best_plan.plan) == 2
#
#     def test_direct_usage_gone_wrong(self) -> None:
#         self.flow.add(GoalItems(goals=GoalItem(goal_name="test_agent")))
#         self.flow.add(MemoryItem(item_id='"He said "what"??"'))
#
#         plans = self.get_plan()
#         assert plans.best_plan
#         assert len(plans.best_plan.plan) == 2
#
#     def test_direct_determination(self) -> None:
#         self.flow.add(GoalItems(goals=GoalItem(goal_name="test_agent")))
#
#         plans = self.get_plan()
#         assert plans.best_plan
#         assert len(plans.best_plan.plan) == 3
#         assert plans.best_plan.plan[1] == Constraint(
#             constraint='$x in ["x", "y", "z"]', truth_value=ConstraintState.TRUE
#         )
#
#     def test_usage_from_production(self) -> None:
#         pass
#
#     def test_usage_memory(self) -> None:
#         pass
#
#     def test_usage_multi_instance(self) -> None:
#         pass
#
#     def test_usage_with_type_map(self) -> None:
#         pass
#
#     def test_two_enums_in_signature(self) -> None:
#         pass
