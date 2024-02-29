from copy import deepcopy
from typing import List, Optional, Tuple
import unittest
from profiler.converters.info_2_flow_converter import (
    get_pddl_plan_str,
    get_operators_for_flow,
    get_goals_for_flow,
    get_slot_fillers_for_flow,
    get_data_mappers_for_flow,
    get_available_data_for_flow,
    get_flow_from_agent_infos,
)
from profiler.data_types.agent_info_data_types import Plan
from profiler.data_types.agent_info_data_types import (
    AgentInfo,
    AgentInfoSignatureItem,
)
from nl2flow.compile.operators import ClassicalOperator as Operator


class TestInfo2FlowConverter(unittest.TestCase):
    def test_get_pddl_plan_str(self) -> None:
        plan: Plan = {"metric": 0, "plan": [{"action_name": "a", "parameters": ["b", "c"]}]}
        res = get_pddl_plan_str(plan)
        self.assertEqual("(a b c)", res)

    def test_get_operators_for_flow(self) -> None:
        item: AgentInfoSignatureItem = {
            "name": "k",
            "sequence_alias": "j",
            "data_type": None,
        }
        agent_info: AgentInfo = {
            "agent_id": "a",
            "actuator_signature": {"in_sig_full": [item], "out_sig_full": [item]},
        }
        agent_infos = [deepcopy(agent_info), deepcopy(agent_info)]
        operators: List[Operator] = get_operators_for_flow(agent_infos)
        self.assertEqual(len(agent_infos), len(operators))

    def test_get_goals_for_flow(self) -> None:
        goals = {"a", "b"}
        goal_items = get_goals_for_flow(goals)
        self.assertEqual(2, len(goal_items.goals))

    def test_get_slot_fillers_for_flow(self) -> None:
        item_0: AgentInfoSignatureItem = {
            "name": "k",
            "sequence_alias": "j",
            "slot_fillable": True,
        }
        item_1: AgentInfoSignatureItem = {"name": "j", "sequence_alias": "j"}
        agent_info: AgentInfo = {
            "agent_id": "a",
            "actuator_signature": {
                "in_sig_full": [item_0, item_1],
                "out_sig_full": [item_0],
            },
        }
        agent_infos = [agent_info]
        slot_properties = get_slot_fillers_for_flow(agent_infos)
        self.assertEqual(2, len(slot_properties))

    def test_get_data_mappers_for_flow(self) -> None:
        mappings = [("a", "b", 1.0)]
        mapping_items = get_data_mappers_for_flow(mappings)
        self.assertEqual(1, len(mapping_items))

    def test_get_available_data_for_flow(self) -> None:
        available_data: List[Tuple[str, Optional[str]]] = [("a", None), ("b", None)]
        memory_items = get_available_data_for_flow(available_data)
        self.assertEqual(2, len(memory_items))

    def test_get_flow_from_agent_infos(self) -> None:
        item_0: AgentInfoSignatureItem = {
            "name": "a",
            "sequence_alias": "a",
            "slot_fillable": True,
            "data_type": None,
        }
        item_1: AgentInfoSignatureItem = {
            "name": "b",
            "sequence_alias": "b",
            "slot_fillable": True,
            "data_type": None,
        }
        agent_info: AgentInfo = {
            "agent_id": "k",
            "actuator_signature": {"in_sig_full": [item_0], "out_sig_full": [item_1]},
        }
        mappings = [("a", "b", 1.0)]
        available_data: List[Tuple[str, Optional[str]]] = [("a", None), ("b", None)]
        goals = {"k"}
        flow = get_flow_from_agent_infos([agent_info], mappings, goals, available_data)
        self.assertIsNotNone(flow)
        pddl, _ = flow.compile_to_pddl()
        self.assertIsNotNone(pddl)
