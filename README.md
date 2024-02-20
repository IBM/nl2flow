# NL2Flow: A PDDL Interface to Flow Construction

[![IBM](https://img.shields.io/badge/IBM%20Research-AI-green)](https://research.ibm.com)
![image](https://img.shields.io/badge/python->=3.9-darkblue)
![image](https://img.shields.io/badge/tarski-0.8.2-blue)
[![AI](https://img.shields.io/badge/Planner-ForbidIterative-purple)](https://github.com/IBM/forbiditerative)

This package allows developers to easily integrate automated planning applications into their systems. Migrating research efforts to product creates knowledge gaps and blindspots, along with requirements for long-term support which often cannot be followed through. Particularly, the adoption of automated planners into products requires developers to get familiar with declarative modeling and understand the requirements of the [PDDL](https://en.wikipedia.org/wiki/Planning_Domain_Definition_Language) syntax. This package mitigates this need by creating an abstraction around the underlying formal representation so that anyone can use automated planners to create workflows through a Python API, with their desired specifications. 

&#129299; Read more about our work on natural language to workflow construction [here](https://link.springer.com/chapter/10.1007/978-3-031-16168-1_8).


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

pddl, _ = new_flow.compile_to_pddl() # if you want the PDDL only
parsed_plans = new_flow.plan_it(planner) # if you want the plans

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

## Citation

If you end up using this code, you can cite us using the following BibTex entry. Our general focus on natural language processing pipelines for workflow construction applications is documented in that paper. 

```latex
@inproceedings{chakraborti2022natural,
  title={From Natural Language to Workflows: Towards Emergent Intelligence in Robotic Process Automation},
  author={Tathagata Chakraborti and Yara Rizk and Vatche Isahagian and Burak Aksar and Francesco Fuggitti},
  booktitle={BPM RPA Forum},
  year={2022},
}
```

### Acknowledgements

This package depends **heavily** on `Tarski`, our favorite PDDL parser. Give them lots of :heart: :heart:. 

[![github](https://img.shields.io/badge/GitHub-Tarski-black)](https://github.com/aig-upf/tarski)
[![docs](https://img.shields.io/badge/Docs-Tarski-green)](https://tarski.readthedocs.io)
