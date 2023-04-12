# Getting Started

NL2Flow is a Python API for writing PDDL compilations.
Get started with constructing a simple flow where you have two operators, 
one target operator and another one which provides required items for the target operator.

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

You can use this PDDL to generate plans using any domain-independent planner.
If you don't have a planner handy, try it out [here](http://editor.planning.domains/).
The top-2 plans for the above specfication looks like this. 

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

## Developer

If you are a developer, head over to the instructions for contributing 
code [here](CONTRIBUTING.md).

