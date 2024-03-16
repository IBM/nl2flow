from nl2flow.compile.flow import Flow

from nl2flow.compile.schemas import PartialOrder
from nl2flow.compile.schemas import GoalItems, GoalItem
from nl2flow.compile.options import GoalType
from nl2flow.services.schemas.sketch_schemas import Sketch, Catalog, Goal
from nl2flow.services.schemas.sketch_options import SketchOptions


def is_this_an_agent(item: str, catalog: Catalog) -> bool:
    return item in [agent.id for agent in catalog.agents]


def basic_sketch_compilation(flow: Flow, sketch: Sketch, catalog: Catalog) -> None:
    for component in sketch.components:
        if isinstance(component, Goal):
            if is_this_an_agent(component.item, catalog):
                flow.add(GoalItems(goals=GoalItem(goal_name=component.item, goal_type=GoalType.OPERATOR)))
            else:
                flow.add(GoalItems(goals=GoalItem(goal_name=component.item, goal_type=GoalType.OBJECT_KNOWN)))

    if SketchOptions.INORDER.value in sketch.options:
        goal_agents = [
            component.item
            for component in sketch.components
            if isinstance(component, Goal) and is_this_an_agent(component.item, catalog)
        ]

        for index in range(1, len(goal_agents)):
            flow.add(PartialOrder(antecedent=goal_agents[index - 1], consequent=goal_agents[index]))
