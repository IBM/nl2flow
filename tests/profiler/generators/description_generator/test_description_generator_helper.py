from typing import List
import unittest
from profiler.generators.description_generator.description_generator_helper import (
    get_variables_description,
    get_description_available_data,
    get_names,
    get_available_agents_description,
    get_signature_item_names,
    get_agent_info_description,
    get_mapping_description,
    get_mappings_description,
    get_goal_description,
)
from profiler.data_types.agent_info_data_types import (
    AgentInfo,
    AgentInfoSignatureItem,
)


class TestDescriptionGeneratorHelper(unittest.TestCase):
    def test_get_names_single(self):
        names = ["a"]
        names_str = get_names(names)
        self.assertEqual(names[0], names_str)

    def test_get_names_double(self):
        names = ["a", "b"]
        names_str = get_names(names)
        self.assertEqual("a and b", names_str)

    def test_get_names_triple(self):
        names = ["a", "b", "c"]
        names_str = get_names(names)
        self.assertEqual("a, b, and c", names_str)

    def test_get_available_agents_description_single(self):
        available_agents: List[AgentInfo] = list()
        available_agents.append({"agent_id": "a"})
        res = get_available_agents_description(available_agents)
        self.assertEqual("The system has Action a.", res)

    def test_get_available_agents_description_double(self):
        available_agents: List[AgentInfo] = list()
        available_agents.append({"agent_id": "a"})
        available_agents.append({"agent_id": "b"})
        res = get_available_agents_description(available_agents)
        self.assertEqual("The system has Action a and Action b.", res)

    def test_get_available_agents_description_triple(self):
        available_agents: List[AgentInfo] = list()
        available_agents.append({"agent_id": "a"})
        available_agents.append({"agent_id": "b"})
        available_agents.append({"agent_id": "c"})
        res = get_available_agents_description(available_agents)
        self.assertEqual("The system has Action a, Action b, and Action c.", res)

    def test_get_signature_item_names_single(self):
        items: List[AgentInfoSignatureItem] = list()
        items.append({"name": "a"})
        res = get_signature_item_names(items)
        self.assertEqual("Variable a", res)

    def test_get_signature_item_names_double(self):
        items: List[AgentInfoSignatureItem] = list()
        items.append({"name": "a"})
        items.append({"name": "b"})
        res = get_signature_item_names(items)
        self.assertEqual("Variable a and Variable b", res)

    def test_get_signature_item_names_triple(self):
        items: List[AgentInfoSignatureItem] = list()
        items.append({"name": "a"})
        items.append({"name": "b"})
        items.append({"name": "c"})
        res = get_signature_item_names(items)
        self.assertEqual("Variable a, Variable b, and Variable c", res)

    def test_get_agent_info_description(self):
        agent_info: AgentInfo = {
            "agent_id": "a",
            "actuator_signature": {
                "in_sig_full": [{"name": "b", "required": True, "slot_fillable": True}],
                "out_sig_full": [
                    {"name": "c", "required": False, "slot_fillable": False}
                ],
            },
        }
        pre_cond, in_sig, effects = get_agent_info_description(agent_info)
        self.assertEqual("To execute Action a, Variable b should be known.", pre_cond)
        self.assertEqual(
            "Variable b is required and can be acquired by asking the user.", in_sig
        )
        self.assertEqual("After executing Action a, Variable c is known.", effects)

    def test_get_mapping_description(self):
        mapping = ("a", "b", 1.0)
        res = get_mapping_description(mapping)
        self.assertEqual(
            "Values for Variable a can be used for Variable b.",
            res,
        )

    def test_get_mappings_description(self):
        mapping_0 = ("a", "b", 1.0)
        mapping_1 = ("c", "d", 1.0)
        res = get_mappings_description([mapping_0, mapping_1])
        self.assertEqual(
            "Values for Variable a can be used for Variable b. Values for Variable c can be used for Variable d.",
            res,
        )

    def test_get_goal_description(self):
        goals = {"a", "b"}
        res = get_goal_description(goals)
        self.assertEqual(
            "The goal of the system is to execute Action a and Action b.", res
        )

    def test_get_description_available_data(self):
        values = ["a", "b"]
        res = get_description_available_data(values)
        self.assertEqual(
            "Values are available already for Variable a and Variable b.", res
        )

    def test_get_variables_description(self):
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
        self.assertEqual(
            "The system has Variable b, Variable c (type: sample_type), Variable r (type: type_a), and Variable s.",
            res,
        )
