# NL2Flow: A PDDL Interface to Flow Construction

![image](https://img.shields.io/badge/python-3.8-darkblue)
![image](https://img.shields.io/badge/tarski-0.8.2-blue)
![image](https://img.shields.io/badge/code%20style-black-black)
![image](https://img.shields.io/badge/linting-pylint-yellow)
![image](https://img.shields.io/badge/linting-flake8-yellow)
![image](https://img.shields.io/badge/typing-mypy-orange)
![image](https://img.shields.io/badge/tests-passing-brightgreen)

This package allows developers to easily integrate automated planning applications into their systems. Migrating research efforts to product creates knowledge gaps and blindspots, along with requirements for long-term support which often cannot be followed through. Particularly, the adoption of automated planners into products requires developers to get familiar with declarative modeling and understand the requirements of the [PDDL](https://en.wikipedia.org/wiki/Planning_Domain_Definition_Language) syntax. 

This package mitigates this need by creating an abstraction around the underlying formal representation so that anyone can use automated planners to create workflows through a Python API, with their desired specifications. The package contains use cases and compilations that have featured in two IBM products till date: [Watson Orchestrate](https://www.ibm.com/products/watson-orchestrate) and [App Connect](https://www.ibm.com/cloud/app-connect). 

&#129299; Read more about our work on natural language to workflow construction [here](https://link.springer.com/chapter/10.1007/978-3-031-16168-1_8).

### Installation

```bash
$ pip install -r requirements.txt
```

### Development

If you are looking to contribute code, you need to install the developer requirements as well. 
We also strongly recommend using a virtual environment, such 
as [anaconda](https://www.anaconda.com/), for development.

```bash
$ conda create --name nl2flow
(nl2flow) $ pip install -r requirements_dev.txt
```

Before starting development, please refer to the contribution 
guidelines [here](CONTRIBUTING.md).


### Usage

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



