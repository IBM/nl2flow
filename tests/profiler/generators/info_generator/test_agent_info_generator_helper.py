from collections import deque
from copy import deepcopy
from typing import List

import pytest
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
    get_variable_types,
)
from profiler.data_types.agent_info_data_types import (
    AgentInfo,
    AgentInfoSignature,
    AgentInfoSignatureItem,
    AgentInfoSignatureType,
)
from profiler.data_types.generator_data_type import VariableInfo
from profiler.validators.agent_info_generator_test_utils import get_stats_coupled_agents
import random


class TestAgentInfoGeneratorHelper:
    def test_get_agents(self) -> None:
        agent_names = ["a", "b", "c"]
        num_input_sig = 3
        agent_infos = get_agents(agent_names, num_input_sig)
        assert len(agent_names) == len(agent_infos)
        for agent_info in agent_infos:
            assert len(agent_info["evaluator_signature"].in_sig_full) == 0
            assert len(agent_info["evaluator_signature"].out_sig_full) == 0
            assert num_input_sig == len(agent_info["actuator_signature"].in_sig_full)
            assert num_input_sig == len(agent_info["actuator_signature"].out_sig_full)

    def test_get_variable_types_many_types(self) -> None:
        num_variables = 100
        num_var_types = 14
        sample_types = get_variable_types(num_variables, num_var_types, random)
        assert num_variables == len(sample_types)
        types = set(filter(lambda t: t is not None, sample_types))
        assert num_var_types == len(types)

    def test_get_variable_types_no_type(self) -> None:
        num_variables = 100
        num_var_types = 0
        sample_types = get_variable_types(num_variables, num_var_types, random)
        assert num_variables == len(sample_types)
        types = set(filter(lambda t: t is not None, sample_types))
        assert num_var_types == len(types)

    def test_get_variables(self) -> None:
        variable_names = ["a", "b", "c", "d"]
        proportion_mappable_variable = 0.5
        proportion_slot_fillable_variable = 0.5
        num_variable_types = 2
        variables: List[VariableInfo] = get_variables(
            variable_names,
            proportion_slot_fillable_variable,
            proportion_mappable_variable,
            num_variable_types,
            random,
        )
        assert len(variable_names) == len(variables)
        cnt_mappable = 0
        cnt_slot_fillable = 0
        variable_types = set()
        for variable in variables:
            if variable.mappable:
                cnt_mappable += 1
            if variable.slot_fillable:
                cnt_slot_fillable += 1
            if variable.variable_type is not None:
                variable_types.add(variable.variable_type[:])
        assert len(variable_names) // 2 == cnt_mappable
        assert len(variable_names) // 2 == cnt_slot_fillable
        assert len(variable_types) == num_variable_types

    def test_get_goals(self) -> None:
        num_agents = 10
        num_goals = 5
        agent_infos: List[AgentInfo] = list()
        for i in range(num_agents):
            agent_info: AgentInfo = AgentInfo()
            agent_info["agent_id"] = str(i)
            agent_infos.append(agent_info)
        agent_ids = set(map(lambda info: info["agent_id"][:], agent_infos))
        goals = get_goals(num_goals, agent_infos, random)
        assert num_goals == len(goals)
        for goal in goals:
            assert goal in agent_ids

    def test_get_mappings(self) -> None:
        variable_0 = VariableInfo(variable_name="a", slot_fillable=False, mappable=True)
        variable_1 = VariableInfo(variable_name="b", slot_fillable=False, mappable=False)
        variable_2 = VariableInfo(variable_name="c", slot_fillable=False, mappable=True)
        mappings = get_mappings([variable_0, variable_1, variable_2], random)
        assert len(mappings) == 2

    def test_get_new_signature_from_variable_info(self) -> None:
        signature_item_input = AgentInfoSignatureItem(name="a", slot_fillable=False)
        name = "k"
        variable_info = VariableInfo(variable_name=name, mappable=True, slot_fillable=True)
        res = get_new_signature_from_variable_info(signature_item_input, variable_info)
        assert name == res.name
        assert res.slot_fillable

    def test_get_uncoupled_agents(self) -> None:
        item = AgentInfoSignatureItem(name="k")
        agent_info: AgentInfo = {"actuator_signature": AgentInfoSignature(in_sig_full=[item], out_sig_full=[item])}
        agent_infos = [deepcopy(agent_info), deepcopy(agent_info)]
        variable_infos = [
            VariableInfo(variable_name="a", mappable=False, slot_fillable=False),
            VariableInfo(variable_name="b", mappable=False, slot_fillable=False),
        ]
        res = get_uncoupled_agents(agent_infos, variable_infos)
        assert len(agent_infos) == len(res)
        for agent_info in res:
            assert len(agent_info["actuator_signature"].in_sig_full) == 1
            assert agent_info["actuator_signature"].in_sig_full[0].name == "a"
            assert len(agent_info["actuator_signature"].out_sig_full) == 1
            assert agent_info["actuator_signature"].out_sig_full[0].name == "b"

    def test_get_agent_infos_with_coupled_agents_two_agents_no_extra_variable_all_coupling_agents(
        self,
    ) -> None:
        agent_info: AgentInfo = {
            "actuator_signature": AgentInfoSignature(
                in_sig_full=[
                    AgentInfoSignatureItem(name="a", mappable=False, slot_fillable=False),
                    AgentInfoSignatureItem(name="b", mappable=False, slot_fillable=False),
                ],
                out_sig_full=[
                    AgentInfoSignatureItem(name="c", mappable=False, slot_fillable=False),
                    AgentInfoSignatureItem(name="d", mappable=False, slot_fillable=False),
                ],
            )
        }
        agent_0 = deepcopy(agent_info)
        agent_0["agent_id"] = "A"
        agent_1 = deepcopy(agent_info)
        agent_1["agent_id"] = "B"
        agent_infos = [agent_0, agent_1]
        variable_infos = [
            VariableInfo(
                variable_name="a",
                mappable=False,
                slot_fillable=False,
                variable_type=None,
            ),
            VariableInfo(
                variable_name="b",
                mappable=False,
                slot_fillable=False,
                variable_type=None,
            ),
            VariableInfo(
                variable_name="c",
                mappable=False,
                slot_fillable=False,
                variable_type=None,
            ),
            VariableInfo(
                variable_name="d",
                mappable=False,
                slot_fillable=False,
                variable_type=None,
            ),
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
        assert len(agent_infos_res) == 2
        assert len(position_item_coupled) == 2
        assert len(variables_remaining_deque) == 0
        num_coupled_agents, _ = get_stats_coupled_agents(agent_infos_res)
        assert num_coupled_agents == 2

    def test_get_agent_infos_with_coupled_agents_two_agents_extra_variable_all_coupling_agents(
        self,
    ) -> None:
        agent_info: AgentInfo = {
            "actuator_signature": AgentInfoSignature(
                in_sig_full=[
                    AgentInfoSignatureItem(name="a", mappable=False, slot_fillable=False),
                    AgentInfoSignatureItem(name="b", mappable=False, slot_fillable=False),
                ],
                out_sig_full=[
                    AgentInfoSignatureItem(name="c", mappable=False, slot_fillable=False),
                    AgentInfoSignatureItem(name="d", mappable=False, slot_fillable=False),
                ],
            )
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
        assert len(agent_infos_res) == 2
        assert len(position_item_coupled) == 2
        assert len(variables_remaining_deque) == 0
        num_coupled_agents, _ = get_stats_coupled_agents(agent_infos_res)
        assert num_coupled_agents == 2

    def test_get_agent_infos_with_coupled_agents_three_agents_extra_variable_all_coupling_agents(
        self,
    ) -> None:
        agent_info: AgentInfo = {
            "actuator_signature": AgentInfoSignature(
                in_sig_full=[
                    AgentInfoSignatureItem(name="a", mappable=False, slot_fillable=False),
                    AgentInfoSignatureItem(name="b", mappable=False, slot_fillable=False),
                ],
                out_sig_full=[
                    AgentInfoSignatureItem(name="c", mappable=False, slot_fillable=False),
                    AgentInfoSignatureItem(name="d", mappable=False, slot_fillable=False),
                ],
            )
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
        assert len(agent_infos_res) == 3
        assert len(position_item_coupled) >= 3
        assert len(variables_remaining_deque) == 0
        num_coupled_agents, _ = get_stats_coupled_agents(agent_infos_res)
        assert num_coupled_agents == 3

    def test_get_agent_info_with_remaining_variables(self) -> None:
        agent_info: AgentInfo = {
            "actuator_signature": AgentInfoSignature(
                in_sig_full=[
                    AgentInfoSignatureItem(name="a", mappable=False, slot_fillable=False),
                    AgentInfoSignatureItem(name="b", mappable=False, slot_fillable=False),
                ],
                out_sig_full=[
                    AgentInfoSignatureItem(name="c", mappable=False, slot_fillable=False),
                    AgentInfoSignatureItem(name="d", mappable=False, slot_fillable=False),
                ],
            )
        }
        agent_0 = deepcopy(agent_info)
        agent_0["agent_id"] = "A"
        agent_1 = deepcopy(agent_info)
        agent_1["agent_id"] = "B"
        agent_infos = [agent_0, agent_1]
        position_item_coupled = {(1, AgentInfoSignatureType.IN_SIG_FULL, 0)}
        variables_remaining_deque_input = deque([VariableInfo(variable_name="k", mappable=False, slot_fillable=False)])
        (
            agent_infos_res,
            _,
        ) = get_agent_info_with_remaining_variables(agent_infos, position_item_coupled, variables_remaining_deque_input)
        assert agent_infos_res[1]["actuator_signature"].in_sig_full[1].name == "k"
        assert agent_infos_res[1]["actuator_signature"].in_sig_full[0].name == "a"

    def test_get_agents_with_variables_no_available_agents(self) -> None:
        agent_info: AgentInfo = {
            "actuator_signature": AgentInfoSignature(
                in_sig_full=[
                    AgentInfoSignatureItem(name="x", mappable=False, slot_fillable=False),
                    AgentInfoSignatureItem(name="x", mappable=False, slot_fillable=False),
                ],
                out_sig_full=[
                    AgentInfoSignatureItem(name="x", mappable=False, slot_fillable=False),
                    AgentInfoSignatureItem(name="x", mappable=False, slot_fillable=False),
                ],
            )
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
        res = get_agents_with_variables(agent_infos, variable_infos_input, proportion_coupled_agents, random)
        assert len(res[0]) == 2
        assert len(res[1]) == 0
        # check coupling
        num_coupled_agents, _ = get_stats_coupled_agents(res[0])
        assert num_coupled_agents == 2

    def test_get_agents_with_variables_two_available_agents(self) -> None:
        agent_info: AgentInfo = {
            "actuator_signature": AgentInfoSignature(
                in_sig_full=[
                    AgentInfoSignatureItem(name="x", mappable=False, slot_fillable=False),
                    AgentInfoSignatureItem(name="x", mappable=False, slot_fillable=False),
                ],
                out_sig_full=[
                    AgentInfoSignatureItem(name="x", mappable=False, slot_fillable=False),
                    AgentInfoSignatureItem(name="x", mappable=False, slot_fillable=False),
                ],
            )
        }
        agent_0 = deepcopy(agent_info)
        agent_0["agent_id"] = "A"
        agent_1 = deepcopy(agent_info)
        agent_1["agent_id"] = "B"
        agent_infos = [agent_0, agent_1]
        variable_infos_input = [
            VariableInfo(
                variable_name="a",
                mappable=False,
                slot_fillable=False,
                variable_type=None,
            ),
            VariableInfo(
                variable_name="b",
                mappable=False,
                slot_fillable=False,
                variable_type=None,
            ),
            VariableInfo(
                variable_name="c",
                mappable=False,
                slot_fillable=False,
                variable_type=None,
            ),
            VariableInfo(
                variable_name="d",
                mappable=False,
                slot_fillable=False,
                variable_type=None,
            ),
            VariableInfo(
                variable_name="e",
                mappable=False,
                slot_fillable=False,
                variable_type=None,
            ),
            VariableInfo(
                variable_name="f",
                mappable=False,
                slot_fillable=False,
                variable_type=None,
            ),
            VariableInfo(
                variable_name="g",
                mappable=False,
                slot_fillable=False,
                variable_type=None,
            ),
            VariableInfo(
                variable_name="h",
                mappable=False,
                slot_fillable=False,
                variable_type=None,
            ),
            VariableInfo(
                variable_name="i",
                mappable=False,
                slot_fillable=False,
                variable_type=None,
            ),
        ]
        proportion_coupled_agents = 1.0
        res = get_agents_with_variables(agent_infos, variable_infos_input, proportion_coupled_agents, random)
        assert len(res[0]) == 2
        assert len(res[1]) == 2
        assert ("h", None) in res[1]
        assert ("i", None) in res[1]
        # check coupling
        num_coupled_agents, _ = get_stats_coupled_agents(res[0])
        assert num_coupled_agents == 2

    @pytest.mark.skip(reason="hakunator package has an issue")
    def test_get_names_from_haikunator(self) -> None:
        num_names = 200
        names = get_names_from_haikunator(num_names)
        assert num_names == len(names)

    @pytest.mark.skip(reason="hakunator package has an issue")
    def test_get_agent_variable_names_with_haikunator(self) -> None:
        num_agents = 20
        num_vars = 50
        names_agents, names_vars = get_agent_variable_names_with_haikunator(num_agents, num_vars)
        assert num_agents == len(names_agents)
        assert num_vars == len(names_vars)

    def test_get_agent_variable_names_with_number(self) -> None:
        num_agents = 20
        num_vars = 50
        names_agents, names_vars = get_agent_variable_names_with_number(num_agents, num_vars)
        assert num_agents == len(names_agents)
        assert num_vars == len(names_vars)

    def test_get_names_dataset_agent(self) -> None:
        num = 100
        type = "agent"
        names = get_names_dataset(num, type, random)
        assert num == len(names)

    def test_get_names_dataset_aprameter(self) -> None:
        num = 100
        type = "parameter"
        names = get_names_dataset(num, type, random)
        assert num == len(names)
