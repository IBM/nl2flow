from nl2flow.compile.flow import Flow
from nl2flow.compile.schemas import (
    PDDL,
    MemoryItem,
    SignatureItem,
    GoalItem,
    GoalItems,
    TypeItem,
)
from nl2flow.compile.options import GoalType, TypeOptions, MemoryState
from nl2flow.compile.operators import ClassicalOperator
from nl2flow.plan.planners import Michael


def test_basic() -> None:
    new_flow = Flow("Basic Test")

    new_flow.add(TypeItem(name="test", parent=TypeOptions.ROOT.value))
    new_flow.add(MemoryItem(item_id="id123", item_state=MemoryState.KNOWN))

    find_errors_api = ClassicalOperator("find errors")
    find_errors_api.add_input(SignatureItem(parameters=["database link"]))
    find_errors_api.add_output(SignatureItem(parameters=["list of errors"]))

    fix_errors_api = ClassicalOperator("fix errors")
    fix_errors_api.add_input(SignatureItem(parameters=["list of errors"]))

    goal = GoalItems(
        goals=GoalItem(goal_name="fix errors", goal_type=GoalType.OPERATOR)
    )

    new_flow.add([find_errors_api, fix_errors_api, goal])

    pddl: PDDL = new_flow.compile_to_pddl()
    planner = Michael(url="http://localhost:4501/planners/topq")

    raw_plans = planner.plan(pddl=pddl)
    parsed_plans = planner.parse(response=raw_plans)
    planner.pretty_print(parsed_plans)
