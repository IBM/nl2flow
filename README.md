# NL2Flow: A PDDL Interface to Flow Construction

![image](https://img.shields.io/badge/python-3.8-darkblue)
![image](https://img.shields.io/badge/tarski-0.8.2-blue)
![image](https://img.shields.io/badge/code%20style-black-black)
![image](https://img.shields.io/badge/linting-pylint-yellow)
![image](https://img.shields.io/badge/linting-flake8-yellow)
![image](https://img.shields.io/badge/typing-mypy-orange)
![image](https://img.shields.io/badge/tests-passing-brightgreen)

This package allows developers to easily integrate automated planning applications into their systems. Migrating research efforts to product creates knowledge gaps and blindspots, along with requirements for long-term support which often cannot be followed through. Particularly, the adoption of automated planners into products requires developers to get familiar with declarative modeling and understand the requirements of the [PDDL](https://en.wikipedia.org/wiki/Planning_Domain_Definition_Language) syntax. This package mitigates this need by creating an abstraction around the underlying formal representation so that anyone can use automated planners to create workflows through a Python API, with their desired specifications. 

&#129299; Read more about our work on natural language to workflow construction [here](https://link.springer.com/chapter/10.1007/978-3-031-16168-1_8).


### Development

Before starting development, please refer to the contribution 
guidelines [here](CONTRIBUTING.md).

If you are looking to contribute code, you need to install the developer requirements as well. 
We also strongly recommend using a virtual environment, such 
as [anaconda](https://www.anaconda.com/), for development.

```bash
$ conda create --name nl2flow
```

Python interpreter version should be `3.9.16`. Code formatter is `black`.
To install dependencies, execute `pip install -e .` at the project root.

To use a plan validator, install `VAL` (https://github.com/KCL-Planning/VAL).


### IDE
#### VSCODE
`.env` is located at the project root to set environmental variables.

#### Build a package locally

At the project root, execute the commands shown below.

```bash
python3 -m pip install --upgrade build
python3 -m build
```

to install the built package locally

```bash
pip install dist/nl2flow-<PACKAGE_VERSION_HERE>-py3-none-any.whl
```

### Usage

#### Flow generation

Get started with constructing a simple flow where you have two operators, one target operator and another one which provides required items for the target operator.

```python
from nl2flow.compile.flow import Flow
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.schemas import SignatureItem, GoalItem, GoalItems

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
```

Note that this package is only meant to produce the desired PDDL compilations; you still need to call a [planner](nl2flow/plan) after.
For the above specfication, the resultant plans looks like this. 

```
from nl2flow.plan.planners import Michael

planner = Michael(url="PLANNER_URL")
parsed_plans = new_flow.plan_it(planner)

print(planner.pretty_print(parsed_plans))
```

```commadline
---- Plan #0 ----
Cost: 501.0, Length: 2.0

Step 0: ask, Inputs: list of errors (generic), Outputs: None
Step 1: Fix Errors, Inputs: list of errors (generic), Outputs: None


---- Plan #1 ----
Cost: 502.0, Length: 3.0

Step 0: ask, Inputs: database link (generic), Outputs: None
Step 1: Find Errors, Inputs: database link (generic), Outputs: list of errors (generic)
Step 2: Fix Errors, Inputs: list of errors (generic), Outputs: None
```

Learn more about the NL2Flow API and use cases by clicking on the links below. 

[`NL2Flow API`](https://github.ibm.com/aicl/nl2flow/wiki/NL2Flow-API) &nbsp;
[`Watson Orchestrate`](https://github.ibm.com/aicl/nl2flow/wiki/Watson-Orchestrate) &nbsp;
[`AppConnect`](https://github.ibm.com/aicl/nl2flow/wiki/AppConnect) 


#### Randomly generate PDDL sources and plans

All input parameters to generate sources for PDDL compilation should be defined at `AgentInfoGeneratorInput`. Some combinations of input parameters are not valid for generating sources. For example, the combination of num_var=1 and num_input_parameters=2 is an invalid input because the minimum number of variables is (2 * the number of input parameters) (This source generator assumes that the number of input parameters (precondition) per action is equal to the number of output parameters (effect) per action). `generate_dataset_with_info_generator` returns a list of `PddlGeneratorOutput` if PDDL sources are generated successfully. Otherwise, `generate_dataset_with_info_generator` returns `None`. `PddlGeneratorOutput` contains 1) PDDL domain, 2) PDDL problem, 3) The description of the PDDL domain and problem, 4) a hash for the PDDL domain and problem, and 5) plans created by a planner. The following code block shows how to generate sources.

```python
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
    agent_info_generator_input, PLANNER
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


## Citation

If you end up using this code, you can cite us using the following BibTex entry. Our general focus on natural language processing pipelines for workflow construction applications is documented in that paper. For pointers to individual paper and implementations, please head over to our [Wiki](https://github.ibm.com/aicl/nl2flow/wiki). 

```latex
@inproceedings{chakraborti2022natural,
  title={From Natural Language to Workflows: Towards Emergent Intelligence in Robotic Process Automation},
  author={Tathagata Chakraborti and Yara Rizk and Vatche Isahagian and Burak Aksar and Francesco Fuggitti},
  booktitle={BPM RPA Forum},
  year={2022},
}
```

### Acknowledgements

This package depends **heavily** on `Tarski`, our favorite PDDL parser. Give them lots of &#9829; &#9829;. 

GitHub &#128073; https://github.com/aig-upf/tarski  
Docs &#128073; https://tarski.readthedocs.io
