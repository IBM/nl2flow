#### Randomly generate PDDL sources and plans

All input parameters to generate sources for PDDL compilation should be defined at `AgentInfoGeneratorInput`. Some combinations of input parameters are not valid for generating sources. For example, the combination of num_var=1 and num_input_parameters=2 is an invalid input because the minimum number of variables is (2 * the number of input parameters) (This source generator assumes that the number of input parameters (precondition) per action is equal to the number of output parameters (effect) per action). `generate_dataset_with_info_generator` returns a list of `PddlGeneratorOutput` if PDDL sources are generated successfully. Otherwise, `generate_dataset_with_info_generator` returns `None`. `PddlGeneratorOutput` contains 1) PDDL domain, 2) PDDL problem, 3) The description of the PDDL domain and problem, 4) a hash for the PDDL domain and problem, and 5) plans created by a planner. The following code block shows how to generate sources.

```python
from nl2flow.plan.options import DEFAULT_PLANNER_URL
from profiler.data_types.generator_data_type import AgentInfoGeneratorInput
from profiler.generators.dataset_generator.dataset_generator import (
    generate_dataset_with_info_generator,
)
import random

PLANNER_URL = os.getenv("PLANNER_URL")
PLANNER = (
    Michael(url=PLANNER_URL)
    if PLANNER_URL is not None
    else Christian(url=DEFAULT_PLANNER_URL)
)

random.seed(123456)
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

pddl_generator_outputs = generate_dataset_with_info_generator(
    agent_info_generator_input, PLANNER, random
)

for output in pddl_generator_outputs:
    print(output.description) # print out the description of generated PDDL domain and problem
    print(output.pddl_domain) # print out a PDDL domain
    print(output.pddl_problem) # print out a PDDL problem
    print(output.sample_hash) # print out a hash for PDDL domain and problem
    print(output.planner_response.list_of_plans) # print out a list of plans
```


#### (Experimental) Create a quadruple of python code, code description, PDDL, and Plan

To create a quadruple of python code, code description, PDDL, and Plan, there should be a test in the `pytest` framework. The test should contain 1) a docstring describing the code, 2) PDDL, and 3) plans. `write_pddl_plan` function should be called to capture PDDL and plan information. The following code block shows a test, which can be used to generate a quadruple.

```python
import unittest
from nl2flow.compile.flow import Flow
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.plan.planners import Michael, Christian
from nl2flow.plan.options import DEFAULT_PLANNER_URL
from nl2flow.compile.schemas import SignatureItem, GoalItem, GoalItems
from profiler.test_helpers.profiler_test_helper import write_pddl_plan
import os

PLANNER_URL = os.getenv("PLANNER_URL")
PLANNER = (
    Michael(url=PLANNER_URL)
    if PLANNER_URL is not None
    else Christian(url=DEFAULT_PLANNER_URL)
)


class TestQuadrupleGenerator(unittest.TestCase):
    def test_basic_quadruple(self) -> None:
        """
        THIS IS A TEST DESCRIPTION line 1
        THIS IS A TEST DESCRIPTION line 2
        THIS IS A TEST DESCRIPTION line 3
        THIS IS A TEST DESCRIPTION line 4
        THIS IS A TEST DESCRIPTION line 5
        """
        new_flow = Flow("Basic Test")

        find_errors_api = Operator("Find Errors")
        find_errors_api.add_input(SignatureItem(parameters=["database link"]))
        find_errors_api.add_output(SignatureItem(parameters=["list of errors"]))

        fix_errors_api = Operator("Fix Errors")
        fix_errors_api.add_input(SignatureItem(parameters=["list of errors"]))

        new_flow.add([find_errors_api, fix_errors_api])

        goal = GoalItems(goals=GoalItem(goal_name="Fix Errors"))
        new_flow.add(goal)

        pddl, _ = new_flow.compile_to_pddl()
        plans = new_flow.plan_it(PLANNER)
        write_pddl_plan(pddl, plans, PLANNER)
        assert True
```

To generate a quadruple, which is made up of 1) python code, 2) the description of the code, 3) PDDL sources, and 4) plans created by a planner, execute `get_quadruple` with the path for a test file and the name of the test.

```python
from profiler.generator.quadruple_generator.quadruple_generator import get_quadruple


quadruple = get_quadruple(
    "./tests/profiler/generators/quadruple_generator/test_quadruple_generator.py",
    "test_basic_quadruple",
)
print(quadruple.get_hash()) # print out a hash of the quadruple
```

To generate a list of quadruples, execute `get_quadruples_from_folder` with the path for a directory containing test files.

```python
from profiler.generator.quadruple_generator.quadruple_generator import get_quadruples_from_folder

quadruples = get_quadruples_from_folder("./tests/test_basic")
```
