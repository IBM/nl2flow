import os
import unittest
from nl2flow.plan.planners import Michael, Christian
from nl2flow.plan.options import DEFAULT_PLANNER_URL
from profiler.data_types.generator_data_type import AgentInfoGeneratorInput
from profiler.generators.dataset_generator.dataset_generator import (
    generate_dataset_with_info_generator,
)

PLANNER_URL = os.getenv("PLANNER_URL")
PLANNER = (
    Michael(url=PLANNER_URL)
    if PLANNER_URL is not None
    else Christian(url=DEFAULT_PLANNER_URL)
)


class TestDatasetGenerator(unittest.TestCase):
    def test_generate_dataset_with_info_generator(self):
        num_samples = 2
        agent_info_generator_input: AgentInfoGeneratorInput = AgentInfoGeneratorInput(
            num_agents=21,
            num_var=7,
            num_input_parameters=2,
            num_samples=num_samples,
            num_goal_agents=5,
            proportion_coupled_agents=0.5,
            proportion_slot_fillable_variables=0.2,
            proportion_mappable_variables=0.5,
        )

        pddl_generator_outputs = generate_dataset_with_info_generator(
            agent_info_generator_input, PLANNER
        )

        pretty = PLANNER.pretty_print(pddl_generator_outputs[0].planner_response)
        self.assertEqual(num_samples, len(pddl_generator_outputs))
        for output in pddl_generator_outputs:
            self.assertGreater(len(output.description), 10)
            self.assertGreater(len(output.pddl_domain), 10)
            self.assertGreater(len(output.pddl_problem), 10)
            self.assertIsNotNone(output.planner_response)
            self.assertIsNotNone(output.sample_hash)
            # with open("description.txt", "w") as f:
            #     f.write(output.description)
            # with open("domain.pddl", "w") as f:
            #     f.write(output.pddl_domain)
            # with open("problem.pddl", "w") as f:
            #     f.write(output.pddl_problem)
            # with open("plan.txt", "w") as f:
            #     f.write(PLANNER.pretty_print(output.planner_response))

            print(output)
