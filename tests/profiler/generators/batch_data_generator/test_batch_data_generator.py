from nl2flow.plan.planners import Kstar
from profiler.data_types.generator_data_type import AgentInfoGeneratorInputBatch
from profiler.generators.batch_data_generator.batch_data_generator import (
    get_agent_info_generator_inputs,
    get_pddl_generator_output_batch,
)
import random


PLANNER = Kstar()


class TestBatchDataGenerator:
    def test_get_agent_info_generator_inputs(self) -> None:
        res = list(get_agent_info_generator_inputs(AgentInfoGeneratorInputBatch(proportion_coupled_agents=[0.5, 1.0])))
        assert len(res) == 2

    def test_get_pddl_generator_output_batch(self) -> None:
        AgentInfoGeneratorInputBatch()
        res = list(
            get_pddl_generator_output_batch(
                AgentInfoGeneratorInputBatch(proportion_coupled_agents=[0.5, 1.0]), planner=PLANNER, random=random
            )
        )
        assert len(res) == 2
