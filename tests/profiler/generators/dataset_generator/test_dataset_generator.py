import unittest
from nl2flow.plan.planners import Kstar
from profiler.data_types.generator_data_type import AgentInfoGeneratorInput
from profiler.generators.dataset_generator.dataset_generator import (
    generate_dataset_with_info_generator,
)
import random


PLANNER = Kstar()


class TestDatasetGenerator(unittest.TestCase):
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

        self.assertIsNotNone(pddl_generator_outputs)
        if pddl_generator_outputs is not None:
            self.assertEqual(num_samples, len(pddl_generator_outputs))
        # with open("description.txt", "w") as f:
        #     f.write(output.description)
        # with open("domain.pddl", "w") as f:
        #     f.write(output.pddl_domain)
        # with open("problem.pddl", "w") as f:
        #     f.write(output.pddl_problem)
        # with open("plan.txt", "w") as f:
        #     f.write(PLANNER.pretty_print(output.planner_response))
