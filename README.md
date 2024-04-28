# NL2Flow: A PDDL Interface to Flow Construction

[![IBM](https://img.shields.io/badge/IBM%20Research-AI-green)](https://research.ibm.com)
![image](https://img.shields.io/badge/python->=3.9-darkblue)
![image](https://img.shields.io/badge/tarski-0.8.2-blue)
[![AI](https://img.shields.io/badge/Planner-KStar-purple)](https://github.com/IBM/kstar)

This package allows developers to easily integrate automated planning applications into their systems. Migrating research efforts to product creates knowledge gaps and blindspots, along with requirements for long-term support which often cannot be followed through. Particularly, the adoption of automated planners into products requires developers to get familiar with declarative modeling and understand the requirements of the [PDDL](https://en.wikipedia.org/wiki/Planning_Domain_Definition_Language) syntax. This package mitigates this need by creating an abstraction around the underlying formal representation so that anyone can use automated planners to create workflows through a Python API, with their desired specifications. 

🤓 Read more about our work on natural language to workflow construction [here](https://link.springer.com/chapter/10.1007/978-3-031-16168-1_8).

# Getting Started

#### Clone the repository

```commandline
user:~$ git clone git@github.com:IBM/nl2flow.git
user:~$ cd nl2flow
```

#### Change to a virtual environment

We also strongly recommend using a virtual environment, such
as [anaconda](https://www.anaconda.com/), for development.

```commandline
user:~$ conda create --name nl2flow
user:~$ conda activate nl2flow
```

#### Install Dependencies

```commandline
(nl2flow) user:~$ pip install -e .
```

If you want to contribute code, check [here](docs/CONTRIBUTING.md)

## Example of an NL2Flow Domain

An NL2Flow domain is a mixture of service compostiion and goal-oriented conversation. A typical plan includes elements of API calls, systems calls, and interactions with the user, in pursuit of 
a higher level goal. The following is an example of a plan helping an user with a [trip approval process](https://github.com/IBM/nl2flow/blob/main/tests/sketch/sample_sketches/06-sketch_with_instantiated_goals.yaml)
involving flight and hotel bookings, taxi services to and from airports and location of the event, and subprocesses involving conference registration, visa approval, etc. handed off to the corresponding agents.
Notice the information gathering actions, either directly from the user or from other services, performed by the system to facilitate the above requirements of the goal.

```
[0] ask(conference name)
[1] ask(w3)
[2] list of papers = Author Workbench(w3, conference name)
[3] ask(username)
[4] invoice = Registration Bot(conference name, list of papers, username)
[5] map(invoice, conference registration)
[6] name, address, Employee ID, Passport = W3 Agent(w3)
[7] name, address, Employer Letter = Workday(Employee ID)
[8] visa = Visa Application(Passport, address, Employer Letter)
[9] ask(start date)
[10] ask(end date)
[11] map(home, address)
[12] map(BOS, destination)
[13] booking = Taxi(date, address, destination)
[14] map(LAX, address)
[15] map(JW Marriott Los Angeles LA 900 W Olympic Blvd, destination)
[16] booking = Taxi(date, address, destination)
[17] map(end date, date)
[18] map(JW Marriott Los Angeles LA 900 W Olympic Blvd, address)
[19] map(LAX, destination)
[20] booking = Taxi(date, address, destination)
[21] map(BOS, address)
[22] map(destination, home)
[23] booking = Taxi(date, address, destination)
[24] assert eval(is a business trip)
[25] flight_ticket, hotel_booking = Concur(start date, end date, home, destination)
[26] map(flight_ticket, ticket to conference)
[27] assert $hotel_booking.price + $flight_ticket.price < 1500
[28] approval = Trip Approval(ticket to conference, conference registration)
``` 

## Usage

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
