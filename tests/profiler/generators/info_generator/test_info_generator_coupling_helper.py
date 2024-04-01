from typing import Set
from click import Tuple
from pytest_mock import MockerFixture
from profiler.data_types.generator_data_type import VariableInfo
from profiler.generators.info_generator.agent_info_generator_coupling_helper import (
    get_out_item_position_to_couple_agents,
    exist_variable_name_in_signature,
)
from profiler.data_types.agent_info_data_types import (
    AgentInfoSignature,
    AgentInfoSignatureItem,
    AgentInfo,
    AgentInfoSignatureType,
)


def test_exist_variable_name_in_signature_not_exist() -> None:
    item = AgentInfoSignatureItem(name="b")
    agent_info: AgentInfo = {"actuator_signature": AgentInfoSignature(out_sig_full=[item])}
    variable_info = VariableInfo(variable_name="a", mappable=False, slot_fillable=False)
    agent_infos = [agent_info]
    assert not exist_variable_name_in_signature(agent_infos, variable_info, 0, AgentInfoSignatureType.OUT_SIG_FULL)


def test_exist_variable_name_in_signature_exist() -> None:
    item = AgentInfoSignatureItem(name="a")
    agent_info: AgentInfo = {"actuator_signature": AgentInfoSignature(out_sig_full=[item])}
    variable_info = VariableInfo(variable_name="a", mappable=False, slot_fillable=False)
    agent_infos = [agent_info]
    assert exist_variable_name_in_signature(agent_infos, variable_info, 0, AgentInfoSignatureType.OUT_SIG_FULL)


def test_exist_variable_name_in_signature_exist_none() -> None:
    item = AgentInfoSignatureItem(name="a")
    agent_info: AgentInfo = {"actuator_signature": AgentInfoSignature(out_sig_full=[item])}
    variable_info = None
    agent_infos = [agent_info]
    assert not exist_variable_name_in_signature(agent_infos, variable_info, 0, AgentInfoSignatureType.OUT_SIG_FULL)


def test_get_out_item_position_to_couple_agents_fallback(mocker: MockerFixture) -> None:
    mocker.patch(
        "profiler.generators.info_generator.agent_info_generator_coupling_helper.exist_variable_name_in_signature",
        return_value=True,
    )
    position_coupled: Set[Tuple[int, str, int]] = set()
    variable_info = VariableInfo(variable_name="a", mappable=False, slot_fillable=False)
    signature_type = AgentInfoSignatureType.OUT_SIG_FULL
    (
        agent_index,
        signature_type_out,
        item_index,
    ), is_already_coupled = get_out_item_position_to_couple_agents(
        0, 1, position_coupled, variable_info, [], signature_type
    )
    assert not is_already_coupled
    assert agent_index == 0
    assert signature_type == signature_type_out
    assert item_index == 0


def test_get_out_item_position_to_couple_agents_coupled_position(mocker: MockerFixture) -> None:
    mocker.patch(
        "profiler.generators.info_generator.agent_info_generator_coupling_helper.exist_variable_name_in_signature",
        return_value=True,
    )
    variable_info = VariableInfo(variable_name="a", mappable=False, slot_fillable=False)
    signature_type = AgentInfoSignatureType.OUT_SIG_FULL
    position_coupled = {(0, signature_type, 0)}
    (
        agent_index,
        signature_type_out,
        item_index,
    ), is_already_coupled = get_out_item_position_to_couple_agents(
        0, 1, position_coupled, variable_info, [], signature_type
    )
    assert is_already_coupled
    assert agent_index == 0
    assert signature_type == signature_type_out
    assert item_index == 0


def test_get_out_item_position_to_couple_agents_not_conflicting_signature(mocker: MockerFixture) -> None:
    mocker.patch(
        "profiler.generators.info_generator.agent_info_generator_coupling_helper.exist_variable_name_in_signature",
        return_value=False,
    )
    variable_info = VariableInfo(variable_name="a", mappable=False, slot_fillable=False)
    signature_type = AgentInfoSignatureType.OUT_SIG_FULL
    position_coupled: Set[Tuple[int, str, int]] = set()
    (
        agent_index,
        signature_type_out,
        item_index,
    ), is_already_coupled = get_out_item_position_to_couple_agents(
        0, 1, position_coupled, variable_info, [], signature_type
    )
    assert not is_already_coupled
    assert agent_index == 0
    assert signature_type == signature_type_out
    assert item_index == 0
