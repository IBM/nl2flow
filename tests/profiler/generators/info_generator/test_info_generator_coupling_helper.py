import unittest
from unittest.mock import patch
from profiler.data_types.generator_data_type import VariableInfo
from profiler.generators.info_generator.agent_info_generator_coupling_helper import (
    get_out_item_position_to_couple_agents,
    exist_variable_name_in_signature,
)
from profiler.data_types.agent_info_data_types import (
    AgentInfoSignatureItem,
    AgentInfo,
)


class TestInfoGeneratorCouplingHelper(unittest.TestCase):
    def test_exist_variable_name_in_signature_not_exist(self):
        item: AgentInfoSignatureItem = {"name": "b"}
        agent_info: AgentInfo = {"actuator_signature": {"out_full_sig": [item]}}
        variable_info = VariableInfo(
            variable_name="a", mappable=False, slot_fillable=False
        )
        agent_infos = [agent_info]
        self.assertFalse(
            exist_variable_name_in_signature(
                agent_infos, variable_info, 0, "out_full_sig"
            )
        )

    def test_exist_variable_name_in_signature_exist(self):
        item: AgentInfoSignatureItem = {"name": "a"}
        agent_info: AgentInfo = {"actuator_signature": {"out_full_sig": [item]}}
        variable_info = VariableInfo(
            variable_name="a", mappable=False, slot_fillable=False
        )
        agent_infos = [agent_info]
        self.assertTrue(
            exist_variable_name_in_signature(
                agent_infos, variable_info, 0, "out_full_sig"
            )
        )

    def test_exist_variable_name_in_signature_exist_none(self):
        item: AgentInfoSignatureItem = {"name": "a"}
        agent_info: AgentInfo = {"actuator_signature": {"out_full_sig": [item]}}
        variable_info = None
        agent_infos = [agent_info]
        self.assertFalse(
            exist_variable_name_in_signature(
                agent_infos, variable_info, 0, "out_full_sig"
            )
        )

    @patch(
        "profiler.generators.info_generator.agent_info_generator_coupling_helper.exist_variable_name_in_signature",
        return_value=True,
    )
    def test_get_out_item_position_to_couple_agents_fallback(
        self, mock_exist_variable_name_in_signature
    ):
        position_coupled = {}
        variable_info = VariableInfo(
            variable_name="a", mappable=False, slot_fillable=False
        )
        signature_type = "out_sig_full"
        (
            agent_index,
            signature_type_out,
            item_index,
        ), is_already_coupled = get_out_item_position_to_couple_agents(
            0, 1, position_coupled, variable_info, [], signature_type
        )
        self.assertFalse(is_already_coupled)
        self.assertEqual(0, agent_index)
        self.assertEqual(signature_type, signature_type_out)
        self.assertEqual(0, item_index)
        assert mock_exist_variable_name_in_signature.called

    @patch(
        "profiler.generators.info_generator.agent_info_generator_coupling_helper.exist_variable_name_in_signature",
        return_value=True,
    )
    def test_get_out_item_position_to_couple_agents_coupled_position(
        self, mock_exist_variable_name_in_signature
    ):
        variable_info = VariableInfo(
            variable_name="a", mappable=False, slot_fillable=False
        )
        signature_type = "out_sig_full"
        position_coupled = {(0, signature_type, 0)}
        (
            agent_index,
            signature_type_out,
            item_index,
        ), is_already_coupled = get_out_item_position_to_couple_agents(
            0, 1, position_coupled, variable_info, [], signature_type
        )
        self.assertTrue(is_already_coupled)
        self.assertEqual(0, agent_index)
        self.assertEqual(signature_type, signature_type_out)
        self.assertEqual(0, item_index)
        assert not mock_exist_variable_name_in_signature.called

    @patch(
        "profiler.generators.info_generator.agent_info_generator_coupling_helper.exist_variable_name_in_signature",
        return_value=False,
    )
    def test_get_out_item_position_to_couple_agents_not_conflicting_signature(
        self, mock_exist_variable_name_in_signature
    ):
        variable_info = VariableInfo(
            variable_name="a", mappable=False, slot_fillable=False
        )
        signature_type = "out_sig_full"
        position_coupled = {}
        (
            agent_index,
            signature_type_out,
            item_index,
        ), is_already_coupled = get_out_item_position_to_couple_agents(
            0, 1, position_coupled, variable_info, [], signature_type
        )
        self.assertFalse(is_already_coupled)
        self.assertEqual(0, agent_index)
        self.assertEqual(signature_type, signature_type_out)
        self.assertEqual(0, item_index)
        self.assertEqual(1, mock_exist_variable_name_in_signature.call_count)
