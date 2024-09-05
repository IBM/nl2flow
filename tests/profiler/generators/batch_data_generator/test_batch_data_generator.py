from nl2flow.plan.planners.kstar import Kstar
from profiler.data_types.generator_data_type import AgentInfoGeneratorInputBatch, NameGenerator
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
        agent_info_generator_input_batch = AgentInfoGeneratorInputBatch(
            num_agents=[4],
            num_var=[5],
            num_input_parameters=[2],
            num_samples=[1],
            num_goal_agents=[1, 2],
            proportion_coupled_agents=[0.75],
            proportion_slot_fillable_variables=[0.1, 0.25],
            proportion_mappable_variables=[0.0],
            num_var_types=[0],
            slot_filler_option=[None],
            name_generator=[NameGenerator.NUMBER],
            error_message=[None],
        )
        res = list(get_pddl_generator_output_batch(agent_info_generator_input_batch, planner=PLANNER, random=random))
        assert len(res) == 4

    def test_get_pddl_generator_output_batch_random(self) -> None:
        agent_info_generator_input_batch = AgentInfoGeneratorInputBatch(
            num_agents=[4],
            num_var=[5],
            num_input_parameters=[2],
            num_samples=[1],
            num_goal_agents=[-1],  # random value generation request
            proportion_coupled_agents=[0.75],
            proportion_slot_fillable_variables=[-1.0],  # random value generation request
            proportion_mappable_variables=[-1.0],  # random value generation request
            num_var_types=[0],
            slot_filler_option=[None],
            name_generator=[NameGenerator.NUMBER],
            error_message=[None],
        )
        res = list(get_pddl_generator_output_batch(agent_info_generator_input_batch, planner=PLANNER, random=random))
        assert len(res) >= 0
