from nl2flow.services.schemas.sketch_schemas import Sketch, Catalog, Goal
from nl2flow.services.schemas.sketch_options import SketchOptions

from nl2flow.compile.flow import Flow
from nl2flow.compile.options import GoalType, TypeOptions, LifeCycleOptions, MemoryState, MappingOptions
from nl2flow.compile.schemas import GoalItems, GoalItem, PartialOrder, SlotProperty, MappingItem, Step, MemoryItem


def is_this_an_agent(item: str, catalog: Catalog) -> bool:
    return item in [agent.id for agent in catalog.agents]


def basic_sketch_compilation(flow: Flow, sketch: Sketch, catalog: Catalog) -> None:
    for component in sketch.components:
        if isinstance(component, Goal):
            if is_this_an_agent(component.item, catalog):
                if not component.parameters:
                    flow.add(GoalItems(goals=GoalItem(goal_name=component.item, goal_type=GoalType.OPERATOR)))
                else:
                    targets = []
                    for parameter in component.parameters:
                        new_target = parameter.value or parameter.target

                        if parameter.value:
                            flow.add(
                                MemoryItem(
                                    item_id=new_target,
                                    item_type=parameter.type or TypeOptions.ROOT.value,
                                    item_state=MemoryState.KNOWN.value,
                                )
                            )
                            flow.add(SlotProperty(slot_name=new_target, slot_desirability=0.0))

                        flow.add(MappingItem(source_name=new_target, target_name=parameter.name, probability=1.0))
                        targets.append(new_target)

                    flow.add(
                        GoalItems(
                            goals=GoalItem(
                                goal_name=Step(
                                    name=component.item,
                                    parameters=targets,
                                ),
                                goal_type=GoalType.OPERATOR,
                            )
                        )
                    )
            else:
                flow.add(GoalItems(goals=GoalItem(goal_name=component.item, goal_type=GoalType.OBJECT_KNOWN)))

    for slot_info in sketch.slots:
        flow.add(
            SlotProperty(
                slot_name=slot_info.name,
                slot_desirability=slot_info.goodness,
            )
        )

    for map_info in sketch.mappings:
        flow.add(
            MappingItem(
                source_name=map_info.source,
                target_name=map_info.target,
                probability=map_info.goodness,
            )
        )

    if SketchOptions.INORDER.value in sketch.options:
        goal_agents = [
            component.item
            for component in sketch.components
            if isinstance(component, Goal) and is_this_an_agent(component.item, catalog)
        ]

        for index in range(1, len(goal_agents)):
            flow.add(PartialOrder(antecedent=goal_agents[index - 1], consequent=goal_agents[index]))

    if SketchOptions.NO_TYPING.value in sketch.options:
        flow.mapping_options.add(MappingOptions.ignore_types)

    if SketchOptions.CAREFUL.value in sketch.options:
        flow.variable_life_cycle.add(LifeCycleOptions.uncertain_on_use)
        flow.variable_life_cycle.add(LifeCycleOptions.confirm_on_mapping)
