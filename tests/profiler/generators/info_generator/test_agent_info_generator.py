import pytest
from profiler.generators.info_generator.agent_info_generator import generate_agent_infos
from profiler.data_types.generator_data_type import (
    AgentInfoGeneratorInput,
    NameGenerator,
)
import random


class TestAgentInfoGenerator:
    def test_generate_agent_infos(self) -> None:
        agent_info_generator_input: AgentInfoGeneratorInput = AgentInfoGeneratorInput(
            num_agents=21,
            num_var=7,
            num_input_parameters=2,
            num_samples=2,
            num_goal_agents=5,
            proportion_coupled_agents=0.5,
            proportion_slot_fillable_variables=0.2,
            proportion_mappable_variables=0.5,
        )

        samples, _ = generate_agent_infos(agent_info_generator_input, random)
        assert len(samples) > 0

    @pytest.mark.skip("hakunator package has an issue")
    def test_generate_agent_infos_name_generator_haikunator(self) -> None:
        agent_info_generator_input: AgentInfoGeneratorInput = AgentInfoGeneratorInput(
            num_agents=21,
            num_var=7,
            num_input_parameters=2,
            num_samples=2,
            num_goal_agents=5,
            proportion_coupled_agents=0.5,
            proportion_slot_fillable_variables=0.2,
            proportion_mappable_variables=0.5,
            name_generator=NameGenerator.HAIKUNATOR,
        )

        samples, _ = generate_agent_infos(agent_info_generator_input, random)
        assert len(samples) > 0

    def test_generate_agent_infos_name_generator_dataset(self) -> None:
        agent_info_generator_input: AgentInfoGeneratorInput = AgentInfoGeneratorInput(
            num_agents=21,
            num_var=7,
            num_input_parameters=2,
            num_samples=2,
            num_goal_agents=5,
            proportion_coupled_agents=0.5,
            proportion_slot_fillable_variables=0.2,
            proportion_mappable_variables=0.5,
            name_generator=NameGenerator.DATASET,
        )

        samples, _ = generate_agent_infos(agent_info_generator_input, random)
        assert len(samples) > 0
