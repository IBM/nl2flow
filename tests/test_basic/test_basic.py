from nl2flow.compile.flow import Flow
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.plan.planners import Michael, Christian
from nl2flow.plan.options import DEFAULT_PLANNER_URL
from nl2flow.compile.schemas import (
    PDDL,
    SignatureItem,
    GoalItem,
    GoalItems,
)

import os

PLANNER_URL = os.getenv("PLANNER_URL")
PLANNER = (
    Michael(url=PLANNER_URL)
    if PLANNER_URL is not None
    else Christian(url=DEFAULT_PLANNER_URL)
)


def test_basic() -> None:
    new_flow = Flow("Basic")

    find_errors_api = Operator("find_errors")
    find_errors_api.add_input(SignatureItem(parameters=["database_link"]))
    find_errors_api.add_output(SignatureItem(parameters=["list_of_errors"]))

    fix_errors_api = Operator("fix_errors")
    fix_errors_api.add_input(SignatureItem(parameters=["list_of_errors"]))

    new_flow.add([find_errors_api, fix_errors_api])

    goal = GoalItems(goals=GoalItem(goal_name="fix_errors"))
    new_flow.add(goal)

    pddl: PDDL = new_flow.compile_to_pddl()

    raw_plans = PLANNER.plan(pddl=pddl)
    parsed_plans = PLANNER.parse(response=raw_plans)
    print(PLANNER.pretty_print(parsed_plans))
