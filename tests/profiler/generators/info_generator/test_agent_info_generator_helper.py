from collections import deque
from copy import deepcopy
from typing import List
import unittest
from profiler.generators.info_generator.agent_info_generator_helper import (
    get_names_dataset,
    get_agent_variable_names_with_number,
    get_agent_variable_names_with_haikunator,
    get_names_from_haikunator,
    get_agents_with_variables,
    get_agent_info_with_remaining_variables,
    get_agent_infos_with_coupled_agents,
    get_uncoupled_agents,
    get_agents,
    get_variables,
    get_goals,
    get_mappings,
    get_new_signature_from_variable_info,
)
from profiler.generators.info_generator.generator_variables import (
    AGENT_INFO_SIGNATURE_TEMPLATE,
    AGENT_INFO_SIGNATURE_ITEM_TEMPLATE,
)
from profiler.generators.info_generator.agent_info_data_types import (
    AgentInfo,
    AgentInfoSignatureItem,
)
from profiler.generators.info_generator.generator_data_type import VariableInfo
from profiler.validators.agent_info_generator_test_utils import get_stats_coupled_agents


class TestAgentInfoGeneratorHelper(unittest.TestCase):
    def test_get_agents(self):
        agent_names = ["a", "b", "c"]
        num_input_sig = 3
        agent_infos = get_agents(agent_names, num_input_sig)
        self.assertEqual(len(agent_names), len(agent_infos))
        for agent_info in agent_infos:
            self.assertEqual(2, len(agent_info["evaluator_signature"]))
            self.assertEqual(0, len(agent_info["evaluator_signature"]["in_sig_full"]))
            self.assertEqual(0, len(agent_info["evaluator_signature"]["out_sig_full"]))
            self.assertEqual(2, len(agent_info["actuator_signature"]))
            self.assertEqual(
                num_input_sig, len(agent_info["actuator_signature"]["in_sig_full"])
            )
            self.assertEqual(
                num_input_sig, len(agent_info["actuator_signature"]["out_sig_full"])
            )

    def test_get_variables(self):
        variable_names = ["a", "b", "c", "d"]
        proportion_mappable_variable = 0.5
        proportion_slot_fillable_variable = 0.5
        variables: List[VariableInfo] = get_variables(
            variable_names,
            proportion_slot_fillable_variable,
            proportion_mappable_variable,
        )
        self.assertEqual(len(variable_names), len(variables))
        cnt_mappable = 0
        cnt_slot_fillable = 0
        for variable in variables:
            if variable.mappable:
                cnt_mappable += 1
            if variable.slot_fillable:
                cnt_slot_fillable += 1
        self.assertEqual(len(variable_names) // 2, cnt_mappable)
        self.assertEqual(len(variable_names) // 2, cnt_slot_fillable)

    def test_get_goals(self):
        num_agents = 10
        num_goals = 5
        agent_infos: List[AgentInfo] = list()
        for i in range(num_agents):
            agent_info: AgentInfo = AgentInfo()
            agent_info["agent_id"] = str(i)
            agent_infos.append(agent_info)
        agent_ids = set(map(lambda info: info["agent_id"][:], agent_infos))
        goals = get_goals(num_goals, agent_infos)
        self.assertEqual(num_goals, len(goals))
        for goal in goals:
            assert goal in agent_ids

    def test_get_mappings(self):
        variable_0 = VariableInfo(variable_name="a", slot_fillable=False, mappable=True)
        variable_1 = VariableInfo(
            variable_name="b", slot_fillable=False, mappable=False
        )
        variable_2 = VariableInfo(variable_name="c", slot_fillable=False, mappable=True)
        mappings = get_mappings([variable_0, variable_1, variable_2])
        self.assertEqual(2, len(mappings))

    def test_get_new_signature_from_variable_info(self):
        signature_item_input: AgentInfoSignatureItem = {
            "name": "a",
            "sequence_alias": "b",
            "slot_fillable": False,
        }
        name = "k"
        variable_info = VariableInfo(
            variable_name=name, mappable=True, slot_fillable=True
        )
        res = get_new_signature_from_variable_info(signature_item_input, variable_info)
        self.assertEqual(name, res["name"])
        self.assertEqual(name, res["sequence_alias"])
        self.assertTrue(res["slot_fillable"])

    def test_get_uncoupled_agents(self):
        item: AgentInfoSignatureItem = {"name": "k"}
        agent_info: AgentInfo = {
            "actuator_signature": {"in_sig_full": [item], "out_sig_full": [item]}
        }
        agent_infos = [deepcopy(agent_info), deepcopy(agent_info)]
        variable_infos = [
            VariableInfo(variable_name="a", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="b", mappable=False, slot_fillable=False),
        ]
        res = get_uncoupled_agents(agent_infos, variable_infos)
        self.assertEqual(len(agent_infos), len(res))
        for agent_info in res:
            self.assertEqual(1, len(agent_info["actuator_signature"]["in_sig_full"]))
            self.assertEqual(
                "a", agent_info["actuator_signature"]["in_sig_full"][0]["name"]
            )
            self.assertEqual(1, len(agent_info["actuator_signature"]["out_sig_full"]))
            self.assertEqual(
                "b", agent_info["actuator_signature"]["out_sig_full"][0]["name"]
            )

    def test_get_agent_infos_with_coupled_agents_two_agents_no_extra_variable_all_coupling_agents(
        self,
    ):
        agent_info: AgentInfo = {
            "actuator_signature": {
                "in_sig_full": [
                    {"name": "a", "mappable": False, "slot_fillable": False},
                    {"name": "b", "mappable": False, "slot_fillable": False},
                ],
                "out_sig_full": [
                    {"name": "c", "mappable": False, "slot_fillable": False},
                    {"name": "d", "mappable": False, "slot_fillable": False},
                ],
            }
        }
        agent_0 = deepcopy(agent_info)
        agent_0["agent_id"] = "A"
        agent_1 = deepcopy(agent_info)
        agent_1["agent_id"] = "B"
        agent_infos = [agent_0, agent_1]
        variable_infos = [
            VariableInfo(variable_name="a", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="b", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="c", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="d", mappable=False, slot_fillable=False),
        ]
        proportion_coupled_agents = 1.0
        num_input_parameters = 2
        (
            agent_infos_res,
            position_item_coupled,
            variables_remaining_deque,
        ) = get_agent_infos_with_coupled_agents(
            agent_infos, variable_infos, proportion_coupled_agents, num_input_parameters
        )
        self.assertEqual(2, len(agent_infos_res))
        self.assertEqual(2, len(position_item_coupled))
        self.assertEqual(0, len(variables_remaining_deque))
        num_coupled_agents, connections = get_stats_coupled_agents(agent_infos_res)
        self.assertEqual(2, num_coupled_agents)

    def test_get_agent_infos_with_coupled_agents_two_agents_extra_variable_all_coupling_agents(
        self,
    ):
        agent_info: AgentInfo = {
            "actuator_signature": {
                "in_sig_full": [
                    {"name": "a", "mappable": False, "slot_fillable": False},
                    {"name": "b", "mappable": False, "slot_fillable": False},
                ],
                "out_sig_full": [
                    {"name": "c", "mappable": False, "slot_fillable": False},
                    {"name": "d", "mappable": False, "slot_fillable": False},
                ],
            }
        }
        agent_0 = deepcopy(agent_info)
        agent_0["agent_id"] = "A"
        agent_1 = deepcopy(agent_info)
        agent_1["agent_id"] = "B"
        agent_infos = [agent_0, agent_1]
        variable_infos = [
            VariableInfo(variable_name="a", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="b", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="c", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="d", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="e", mappable=False, slot_fillable=False),
        ]
        proportion_coupled_agents = 1.0
        num_input_parameters = 2
        (
            agent_infos_res,
            position_item_coupled,
            variables_remaining_deque,
        ) = get_agent_infos_with_coupled_agents(
            agent_infos, variable_infos, proportion_coupled_agents, num_input_parameters
        )
        self.assertEqual(2, len(agent_infos_res))
        self.assertEqual(2, len(position_item_coupled))
        self.assertEqual(0, len(variables_remaining_deque))
        num_coupled_agents, connections = get_stats_coupled_agents(agent_infos_res)
        self.assertEqual(2, num_coupled_agents)

    def test_get_agent_infos_with_coupled_agents_three_agents_extra_variable_all_coupling_agents(
        self,
    ):
        agent_info: AgentInfo = {
            "actuator_signature": {
                "in_sig_full": [
                    {"name": "a", "mappable": False, "slot_fillable": False},
                    {"name": "b", "mappable": False, "slot_fillable": False},
                ],
                "out_sig_full": [
                    {"name": "c", "mappable": False, "slot_fillable": False},
                    {"name": "d", "mappable": False, "slot_fillable": False},
                ],
            }
        }
        agent_0 = deepcopy(agent_info)
        agent_0["agent_id"] = "A"
        agent_1 = deepcopy(agent_info)
        agent_1["agent_id"] = "B"
        agent_2 = deepcopy(agent_info)
        agent_2["agent_id"] = "C"
        agent_infos = [agent_0, agent_1, agent_2]
        variable_infos = [
            VariableInfo(variable_name="a", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="b", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="c", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="d", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="e", mappable=False, slot_fillable=False),
        ]
        proportion_coupled_agents = 1.0
        num_input_parameters = 2
        (
            agent_infos_res,
            position_item_coupled,
            variables_remaining_deque,
        ) = get_agent_infos_with_coupled_agents(
            agent_infos, variable_infos, proportion_coupled_agents, num_input_parameters
        )
        self.assertEqual(3, len(agent_infos_res))
        self.assertGreaterEqual(len(position_item_coupled), 3)
        self.assertEqual(0, len(variables_remaining_deque))
        num_coupled_agents, connections = get_stats_coupled_agents(agent_infos_res)
        self.assertEqual(3, num_coupled_agents)

    def test_get_agent_info_with_remaining_variables(self):
        agent_info: AgentInfo = {
            "actuator_signature": {
                "in_sig_full": [
                    {"name": "a", "mappable": False, "slot_fillable": False},
                    {"name": "b", "mappable": False, "slot_fillable": False},
                ],
                "out_sig_full": [
                    {"name": "c", "mappable": False, "slot_fillable": False},
                    {"name": "d", "mappable": False, "slot_fillable": False},
                ],
            }
        }
        agent_0 = deepcopy(agent_info)
        agent_0["agent_id"] = "A"
        agent_1 = deepcopy(agent_info)
        agent_1["agent_id"] = "B"
        agent_infos = [agent_0, agent_1]
        position_item_coupled = {(1, "in_sig_full", 0)}
        variables_remaining_deque_input = deque(
            [VariableInfo(variable_name="k", mappable=False, slot_fillable=False)]
        )
        (
            agent_infos_res,
            variables_remaining_deque,
        ) = get_agent_info_with_remaining_variables(
            agent_infos, position_item_coupled, variables_remaining_deque_input
        )
        self.assertEqual(
            "k", agent_infos_res[1]["actuator_signature"]["in_sig_full"][1]["name"]
        )
        self.assertEqual(
            "a", agent_infos_res[1]["actuator_signature"]["in_sig_full"][0]["name"]
        )

    def test_get_agents_with_variables_no_available_agents(self):
        agent_info: AgentInfo = {
            "actuator_signature": {
                "in_sig_full": [
                    {"name": "x", "mappable": False, "slot_fillable": False},
                    {"name": "x", "mappable": False, "slot_fillable": False},
                ],
                "out_sig_full": [
                    {"name": "x", "mappable": False, "slot_fillable": False},
                    {"name": "x", "mappable": False, "slot_fillable": False},
                ],
            }
        }
        agent_0 = deepcopy(agent_info)
        agent_0["agent_id"] = "A"
        agent_1 = deepcopy(agent_info)
        agent_1["agent_id"] = "B"
        agent_infos = [agent_0, agent_1]
        variable_infos_input = [
            VariableInfo(variable_name="a", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="b", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="c", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="d", mappable=False, slot_fillable=False),
        ]
        proportion_coupled_agents = 1.0
        res = get_agents_with_variables(
            agent_infos, variable_infos_input, proportion_coupled_agents
        )
        self.assertEqual(2, len(res[0]))
        self.assertEqual(0, len(res[1]))
        # check coupling
        num_coupled_agents, connections = get_stats_coupled_agents(res[0])
        self.assertEqual(2, num_coupled_agents)

    def test_get_agents_with_variables_two_available_agents(self):
        agent_info: AgentInfo = {
            "actuator_signature": {
                "in_sig_full": [
                    {"name": "x", "mappable": False, "slot_fillable": False},
                    {"name": "x", "mappable": False, "slot_fillable": False},
                ],
                "out_sig_full": [
                    {"name": "x", "mappable": False, "slot_fillable": False},
                    {"name": "x", "mappable": False, "slot_fillable": False},
                ],
            }
        }
        agent_0 = deepcopy(agent_info)
        agent_0["agent_id"] = "A"
        agent_1 = deepcopy(agent_info)
        agent_1["agent_id"] = "B"
        agent_infos = [agent_0, agent_1]
        variable_infos_input = [
            VariableInfo(variable_name="a", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="b", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="c", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="d", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="e", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="f", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="g", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="h", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="i", mappable=False, slot_fillable=False),
        ]
        proportion_coupled_agents = 1.0
        res = get_agents_with_variables(
            agent_infos, variable_infos_input, proportion_coupled_agents
        )
        self.assertEqual(2, len(res[0]))
        self.assertEqual(2, len(res[1]))
        assert "h" in res[1]
        assert "i" in res[1]
        # check coupling
        num_coupled_agents, connections = get_stats_coupled_agents(res[0])
        self.assertEqual(2, num_coupled_agents)

    def test_get_names_from_haikunator(self):
        num_names = 200
        names = get_names_from_haikunator(num_names)
        self.assertEqual(num_names, len(names))

    def test_get_agent_variable_names_with_haikunator(self):
        num_agents = 20
        num_vars = 50
        names_agents, names_vars = get_agent_variable_names_with_haikunator(
            num_agents, num_vars
        )
        self.assertEqual(num_agents, len(names_agents))
        self.assertEqual(num_vars, len(names_vars))

    def test_get_agent_variable_names_with_number(self):
        num_agents = 20
        num_vars = 50
        names_agents, names_vars = get_agent_variable_names_with_number(
            num_agents, num_vars
        )
        self.assertEqual(num_agents, len(names_agents))
        self.assertEqual(num_vars, len(names_vars))

    def test_get_names_dataset_agent(self):
        num = 100
        type = "agent"
        names = get_names_dataset(num, type)
        self.assertEqual(num, len(names))

    def test_get_names_dataset_aprameter(self):
        num = 100
        type = "parameter"
        names = get_names_dataset(num, type)
        self.assertEqual(num, len(names))
