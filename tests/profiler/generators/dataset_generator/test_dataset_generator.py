from nl2flow.plan.planners.kstar import Kstar
from profiler.data_types.generator_data_type import AgentInfoGeneratorInput
from profiler.generators.dataset_generator.dataset_generator import (
    generate_dataset_with_info_generator,
)
import random


PLANNER = Kstar()


class TestDatasetGenerator:
    def test_generate_dataset_with_info_generator_medium(self) -> None:
        num_samples = 10
        agent_info_generator_input: AgentInfoGeneratorInput = AgentInfoGeneratorInput(
            num_agents=5,
            num_var=40,
            num_input_parameters=5,
            num_samples=num_samples,
            num_goal_agents=1,
            proportion_coupled_agents=0.5,
            proportion_slot_fillable_variables=1.0,
            proportion_mappable_variables=1.0,
            num_var_types=0,
        )

        pddl_generator_outputs = generate_dataset_with_info_generator(agent_info_generator_input, PLANNER, random)

        assert pddl_generator_outputs is not None
        if pddl_generator_outputs is not None:
            assert num_samples == len(pddl_generator_outputs)
        # with open("description.txt", "w") as f:
        #     f.write(output.description)
        # with open("domain.pddl", "w") as f:
        #     f.write(output.pddl_domain)
        # with open("problem.pddl", "w") as f:
        #     f.write(output.pddl_problem)
        # with open("plan.txt", "w") as f:
        #     f.write(PLANNER.pretty_print(output.planner_response))

    def test_generate_dataset_with_info_generator_small(self) -> None:
        num_samples = 1
        agent_info_generator_input: AgentInfoGeneratorInput = AgentInfoGeneratorInput(
            num_agents=2,
            num_var=9,
            num_input_parameters=2,
            num_samples=num_samples,
            num_goal_agents=1,
            proportion_coupled_agents=0.0,
            proportion_slot_fillable_variables=0.1,
            proportion_mappable_variables=0.0,
            num_var_types=3,
        )

        pddl_generator_outputs = generate_dataset_with_info_generator(agent_info_generator_input, PLANNER, random)

        assert pddl_generator_outputs is not None
        if pddl_generator_outputs is not None:
            assert num_samples == len(pddl_generator_outputs)
        # with open("description.txt", "w") as f:
        #     f.write(output.description)
        # with open("domain.pddl", "w") as f:
        #     f.write(output.pddl_domain)
        # with open("problem.pddl", "w") as f:
        #     f.write(output.pddl_problem)
        # with open("plan.txt", "w") as f:
        #     f.write(PLANNER.pretty_print(output.planner_response))

    def test_generate_dataset_with_info_generator_one_action(self) -> None:
        num_samples = 1
        agent_info_generator_input: AgentInfoGeneratorInput = AgentInfoGeneratorInput(
            num_agents=1,
            num_var=9,
            num_input_parameters=2,
            num_samples=num_samples,
            num_goal_agents=1,
            proportion_coupled_agents=1.0,
            proportion_slot_fillable_variables=0.1,
            proportion_mappable_variables=0.0,
            num_var_types=1,
        )

        assert agent_info_generator_input is not None

        pddl_generator_outputs = generate_dataset_with_info_generator(agent_info_generator_input, PLANNER, random)

        assert pddl_generator_outputs is not None
        if pddl_generator_outputs is not None:
            assert num_samples == len(pddl_generator_outputs)
