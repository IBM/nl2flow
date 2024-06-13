from profiler.data_types.generator_data_type import (
    AgentInfoGeneratorInput,
    PlanningInputDescriptionMode,
)
from profiler.generators.info_generator.agent_info_generator import generate_agent_infos
import random


class TestDescriptionGenerator:
    def test_get_sample_description(self) -> None:
        agent_info_generator_input: AgentInfoGeneratorInput = AgentInfoGeneratorInput(
            num_agents=21,
            num_var=7,
            num_input_parameters=2,
            num_samples=1,
            num_goal_agents=5,
            proportion_coupled_agents=0.5,
            proportion_slot_fillable_variables=0.2,
            proportion_mappable_variables=0.5,
        )

        samples, _ = generate_agent_infos(agent_info_generator_input, random)
        assert samples[0].describe() is not None

    def test_get_sample_description_small(self) -> None:
        agent_info_generator_input: AgentInfoGeneratorInput = AgentInfoGeneratorInput(
            num_agents=3,
            num_var=6,
            num_input_parameters=2,
            num_samples=1,
            num_goal_agents=1,
            proportion_coupled_agents=0.5,
            proportion_slot_fillable_variables=1.0,
            proportion_mappable_variables=0.5,
        )

        samples, _ = generate_agent_infos(agent_info_generator_input, random)

        assert samples[0].describe() is not None
        print(samples[0].describe())

    def test_get_sample_description_json(self) -> None:
        agent_info_generator_input: AgentInfoGeneratorInput = AgentInfoGeneratorInput(
            num_agents=3,
            num_var=6,
            num_input_parameters=2,
            num_samples=1,
            num_goal_agents=1,
            proportion_coupled_agents=0.5,
            proportion_slot_fillable_variables=1.0,
            proportion_mappable_variables=0.5,
        )

        samples, _ = generate_agent_infos(agent_info_generator_input, random)

        assert samples[0].describe(planning_input_description_mode=PlanningInputDescriptionMode.JSON) is not None

    def test_get_sample_description_concise(self) -> None:
        agent_info_generator_input: AgentInfoGeneratorInput = AgentInfoGeneratorInput(
            num_agents=3,
            num_var=6,
            num_input_parameters=2,
            num_samples=1,
            num_goal_agents=1,
            proportion_coupled_agents=0.5,
            proportion_slot_fillable_variables=1.0,
            proportion_mappable_variables=0.5,
        )

        samples, _ = generate_agent_infos(agent_info_generator_input, random)

        assert samples[0].describe(planning_input_description_mode=PlanningInputDescriptionMode.CONCISE) is not None
