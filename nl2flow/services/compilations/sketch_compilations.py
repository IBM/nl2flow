from nl2flow.compile.flow import Flow

# from nl2flow.compile.operators import ClassicalOperator as Operator
# from nl2flow.compile.schemas import SignatureItem, Parameter, GoalItems, GoalItem
from nl2flow.compile.schemas import GoalItems, GoalItem
from nl2flow.compile.options import GoalType
from nl2flow.services.schemas.sketch_schemas import Sketch, Catalog, Goal


def is_this_an_agent(item: str, catalog: Catalog) -> bool:
    return item in [agent.id for agent in catalog.agents]


def basic_sketch_compilation(flow: Flow, sketch: Sketch, catalog: Catalog) -> None:

    for component in sketch.components:

        if isinstance(component, Goal):
            if is_this_an_agent(component.item, catalog):
                flow.add(GoalItems(goals=GoalItem(goal_name=component.item, goal_type=GoalType.OPERATOR)))

            else:
                flow.add(GoalItems(goals=GoalItem(goal_name=component.item, goal_type=GoalType.OBJECT_KNOWN)))
