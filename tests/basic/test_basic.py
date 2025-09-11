from nl2flow.compile.flow import Flow
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.plan.planners.kstar import Kstar
from nl2flow.compile.schemas import SignatureItem, GoalItem, GoalItems
from nl2flow.printers.codelike import CodeLikePrint

PLANNER = Kstar()


def test_basic() -> None:
    new_flow = Flow("Basic Test")

    find_errors_api = Operator("Find Errors")
    find_errors_api.add_input(SignatureItem(parameters=["database link"]))
    find_errors_api.add_output(SignatureItem(parameters=["list of errors"]))

    fix_errors_api = Operator("Fix Errors")
    fix_errors_api.add_input(SignatureItem(parameters=["list of errors"]))

    new_flow.add([find_errors_api, fix_errors_api])

    goal = GoalItems(goals=GoalItem(goal_name="Fix Errors"))
    new_flow.add(goal)

    planner_response = new_flow.plan_it(PLANNER)
    print(CodeLikePrint.pretty_print(planner_response))

    assert planner_response.list_of_plans, "There should be plans."
