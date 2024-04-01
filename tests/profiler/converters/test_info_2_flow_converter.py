from copy import deepcopy
from typing import List, Optional, Tuple
from profiler.converters.info_2_flow_converter import (
    get_pddl_plan_str,
    get_operators_for_flow,
    get_goals_for_flow,
    get_slot_fillers_for_flow,
    get_data_mappers_for_flow,
    get_available_data_for_flow,
    get_flow_from_agent_infos,
)
from profiler.data_types.agent_info_data_types import AgentInfoSignature, Plan, PlanAction
from profiler.data_types.agent_info_data_types import (
    AgentInfo,
    AgentInfoSignatureItem,
)
from nl2flow.compile.operators import ClassicalOperator as Operator


class TestInfo2FlowConverter:
    def test_get_pddl_plan_str(self) -> None:
        plan = Plan(plan=[PlanAction(action_name="a", parameters=["b", "c"])], metric=0.0)
        res = get_pddl_plan_str(plan)
        assert "(a b c)" == res

    def test_get_operators_for_flow(self) -> None:
        item = AgentInfoSignatureItem(name="k")
        agent_info = AgentInfo(
            agent_id="a", actuator_signature=AgentInfoSignature(in_sig_full=[item], out_sig_full=[item])
        )

        agent_infos = [deepcopy(agent_info), deepcopy(agent_info)]
        operators: List[Operator] = get_operators_for_flow(agent_infos)
        assert len(agent_infos) == len(operators)

    def test_get_goals_for_flow(self) -> None:
        goals = {"a", "b"}
        goal_items = get_goals_for_flow(goals)
        assert len(goal_items.goals) == 2

    def test_get_slot_fillers_for_flow(self) -> None:
        item_0 = AgentInfoSignatureItem(name="k", slot_fillable=True)
        item_1 = AgentInfoSignatureItem(name="j")
        agent_info = AgentInfo(
            agent_id="a", actuator_signature=AgentInfoSignature(in_sig_full=[item_0, item_1], out_sig_full=[item_0])
        )
        agent_infos = [agent_info]
        slot_properties = get_slot_fillers_for_flow(agent_infos)
        assert len(slot_properties) == 2

    def test_get_data_mappers_for_flow(self) -> None:
        mappings = [("a", "b", 1.0)]
        mapping_items = get_data_mappers_for_flow(mappings)
        assert len(mapping_items) == 1

    def test_get_available_data_for_flow(self) -> None:
        available_data: List[Tuple[str, Optional[str]]] = [("a", None), ("b", None)]
        memory_items = get_available_data_for_flow(available_data)
        assert len(memory_items) == 2

    def test_get_flow_from_agent_infos(self) -> None:
        item_0 = AgentInfoSignatureItem(name="a", slot_fillable=True)
        item_1 = AgentInfoSignatureItem(name="b", slot_fillable=True)
        agent_info = AgentInfo(
            agent_id="k", actuator_signature=AgentInfoSignature(in_sig_full=[item_0], out_sig_full=[item_1])
        )
        mappings = [("a", "b", 1.0)]
        available_data: List[Tuple[str, Optional[str]]] = [("a", None), ("b", None)]
        goals = {"k"}
        flow = get_flow_from_agent_infos([agent_info], mappings, goals, available_data)
        assert flow is not None
        pddl, _ = flow.compile_to_pddl()
        assert pddl is not None
