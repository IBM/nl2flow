from typing import List, Optional, Tuple
from profiler.generators.description_generator.description_generator_helper import (
    get_variables_description,
    get_description_available_data,
    get_names,
    get_available_agents_description,
    get_agent_info_description,
    get_mapping_description,
    get_mappings_description,
    get_goal_description,
    get_available_action_names,
    get_names_from_signature_items,
    get_signature_item_names,
    get_variable_name_from_sig_item,
    get_variable_type_from_sig_item,
)
from profiler.data_types.agent_info_data_types import (
    AgentInfo,
    AgentInfoSignatureItem,
)
from profiler.common_helpers.hash_helper import get_hash_str


class TestDescriptionGeneratorHelper:
    def test_get_variable_name_from_sig_item(self) -> None:
        sig_items = [
            AgentInfoSignatureItem(name="abc", data_type="integer"),
            AgentInfoSignatureItem(name="def", data_type="string"),
            AgentInfoSignatureItem(name="ghi", data_type="date"),
        ]
        variable_strs = get_variable_name_from_sig_item(sig_items)
        assert variable_strs == ["Variable abc", "Variable def", "Variable ghi"]

    def test_get_variable_type_from_sig_item(self) -> None:
        sig_items = [
            AgentInfoSignatureItem(name="abc", data_type="integer"),
            AgentInfoSignatureItem(name="def", data_type="string"),
            AgentInfoSignatureItem(name="ghi", data_type="date"),
        ]
        variable_type_strs = get_variable_type_from_sig_item(sig_items)
        assert variable_type_strs == [
            "The type of Variable abc is integer.",
            "The type of Variable def is string.",
            "The type of Variable ghi is date.",
        ]

    def test_get_signature_item_names(self) -> None:
        sig_items = [
            AgentInfoSignatureItem(name="abc"),
            AgentInfoSignatureItem(name="def"),
            AgentInfoSignatureItem(name="ghi"),
        ]
        names_str = get_signature_item_names(sig_items)
        assert names_str == "Variable abc, Variable def, and Variable ghi"

    def test_get_names_from_signature_items(self) -> None:
        sig_items = [AgentInfoSignatureItem(name="abc"), AgentInfoSignatureItem(name="def")]
        strs = get_names_from_signature_items(sig_items)
        assert strs == ["Variable abc", "Variable def"]

    # def test_get_variable_type_str_none(self):
    #     type_str = None
    #     res = get_variable_type_str(type_str)
    #     self.assertEqual(len(res), 0)

    # def test_get_variable_type_str_none(self):
    #     variable_name = "kjh"
    #     type_str = "abc"
    #     res = get_variable_type_str(variable_name, type_str)
    #     self.assertEqual(res, "The type of Variable kjh is abc.")

    def test_get_names_single(self) -> None:
        names = ["a"]
        names_str = get_names(names)
        assert names[0] == names_str

    def test_get_names_double(self) -> None:
        names = ["a", "b"]
        names_str = get_names(names)
        assert names_str == "a and b"

    def test_get_names_triple(self) -> None:
        names = ["a", "b", "c"]
        names_str = get_names(names)
        assert names_str == "a, b, and c"

    def test_get_available_action_names(self) -> None:
        available_agents: List[AgentInfo] = list()
        available_agents.extend([{"agent_id": "a"}, {"agent_id": "c"}, {"agent_id": "c"}])
        name_str = get_available_action_names(available_agents)
        assert name_str == "Action a, Action c, and Action c"

    def test_get_available_agents_description_single(self) -> None:
        available_agents: List[AgentInfo] = list()
        available_agents.append({"agent_id": "a"})
        res = get_available_agents_description(available_agents)
        assert res == "The system has Action a."

    def test_get_available_agents_description_double(self) -> None:
        available_agents: List[AgentInfo] = list()
        available_agents.append({"agent_id": "a"})
        available_agents.append({"agent_id": "b"})
        res = get_available_agents_description(available_agents)
        assert res == "The system has Action a and Action b."

    def test_get_available_agents_description_triple(self) -> None:
        available_agents: List[AgentInfo] = list()
        available_agents.append({"agent_id": "a"})
        available_agents.append({"agent_id": "b"})
        available_agents.append({"agent_id": "c"})
        res = get_available_agents_description(available_agents)
        assert res == "The system has Action a, Action b, and Action c."

    def test_get_signature_item_names_single(self) -> None:
        items: List[AgentInfoSignatureItem] = list()
        items.append({"name": "a"})
        res = get_signature_item_names(items)
        assert res == "Variable a"

    def test_get_signature_item_names_double(self) -> None:
        items: List[AgentInfoSignatureItem] = list()
        items.append({"name": "a"})
        items.append({"name": "b"})
        res = get_signature_item_names(items)
        assert res == "Variable a and Variable b"

    def test_get_signature_item_names_triple(self) -> None:
        items: List[AgentInfoSignatureItem] = list()
        items.append({"name": "a"})
        items.append({"name": "b"})
        items.append({"name": "c"})
        res = get_signature_item_names(items)
        assert res == "Variable a, Variable b, and Variable c"

    def test_get_agent_info_description(self) -> None:
        agent_info: AgentInfo = {
            "agent_id": "a",
            "actuator_signature": {
                "in_sig_full": [{"name": "b", "required": True, "slot_fillable": True}],
                "out_sig_full": [{"name": "c", "required": False, "slot_fillable": False}],
            },
        }
        pre_cond, effects = get_agent_info_description(agent_info)
        assert pre_cond == "To execute Action a, Variable b should be known."
        assert effects == "After executing Action a, Variable c is known."

    def test_get_mapping_description(self) -> None:
        mapping = ("a", "b", 1.0)
        res = get_mapping_description(mapping)
        assert res == "Values for Variable a can be used for Variable b."

    def test_get_mappings_description(self) -> None:
        mapping_0 = ("a", "b", 1.0)
        mapping_1 = ("c", "d", 1.0)
        res = get_mappings_description([mapping_0, mapping_1])
        assert (
            res == "Values for Variable a can be used for Variable b. Values for Variable c can be used for Variable d."
        )

    def test_get_goal_description(self) -> None:
        goals = {"a", "b"}
        res = get_goal_description(goals)
        assert res == "The goal of the system is to execute Action a and Action b."

    def test_get_description_available_data(self) -> None:
        values: List[Tuple[str, Optional[str]]] = [("a", ""), ("b", "")]
        res = get_description_available_data(values)
        assert res == "Values are available already for Variable a and Variable b."

    def test_get_variables_description_single_variable(self) -> None:
        agent_info: AgentInfo = {
            "agent_id": "a",
            "actuator_signature": {
                "in_sig_full": [
                    {
                        "name": "b",
                        "required": True,
                        "slot_fillable": True,
                        "data_type": None,
                    }
                ],
                "out_sig_full": [
                    {
                        "name": "c",
                        "required": False,
                        "slot_fillable": False,
                        "data_type": "sample_type",
                    }
                ],
            },
        }

        res = get_variables_description([agent_info], [("r", "type_a"), ("s", None)])
        assert get_hash_str(res) == get_hash_str(
            "Variable b can be acquired by asking the user.\n"
            + "Variable c cannot be acquired by asking the user.\n"
            + "The type of Variable c is sample_type. The type of Variable r is type_a."
        )

    def test_get_variables_description_multiple_variables(self) -> None:
        agent_info: AgentInfo = {
            "agent_id": "a",
            "actuator_signature": {
                "in_sig_full": [
                    {
                        "name": "b",
                        "required": True,
                        "slot_fillable": True,
                        "data_type": None,
                    },
                    {
                        "name": "x",
                        "required": True,
                        "slot_fillable": False,
                        "data_type": None,
                    },
                ],
                "out_sig_full": [
                    {
                        "name": "c",
                        "required": False,
                        "slot_fillable": False,
                        "data_type": "sample_type",
                    },
                    {
                        "name": "k",
                        "required": False,
                        "slot_fillable": True,
                        "data_type": None,
                    },
                ],
            },
        }

        res = get_variables_description([agent_info], [("r", "type_a"), ("s", None)])
        assert get_hash_str(res) == get_hash_str(
            "Variables b and k can be acquired by asking the user.\n"
            + "Variables c and x cannot be acquired by asking the user.\n"
            + "The type of Variable c is sample_type. The type of Variable r is type_a."
        )
