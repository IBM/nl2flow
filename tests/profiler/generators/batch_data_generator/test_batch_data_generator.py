import unittest
from profiler.data_types.generator_data_type import AgentInfoGeneratorInputBatch
from profiler.generators.batch_data_generator.batch_data_generator import get_agent_info_generator_inputs


class TestBatchDataGenerator(unittest.TestCase):
    def test_get_agent_info_generator_inputs(self) -> None:
        AgentInfoGeneratorInputBatch()
        res = list(get_agent_info_generator_inputs(AgentInfoGeneratorInputBatch(proportion_coupled_agents=[0.5, 0.3])))
        self.assertEqual(len(res), 2)
