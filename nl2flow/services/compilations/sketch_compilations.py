from nl2flow.services.schemas.sketch_options import SketchOptions
from nl2flow.services.schemas.sketch_schemas import Sketch, Catalog, Goal, Ordering, Condition, Disjunction, Signature

from nl2flow.compile.flow import Flow
from nl2flow.compile.options import (
    GoalType,
    TypeOptions,
    LifeCycleOptions,
    MemoryState,
    MappingOptions,
    GoalOptions,
    ConstraintState,
)

from nl2flow.compile.schemas import (
    GoalItems,
    GoalItem,
    PartialOrder,
    SlotProperty,
    MappingItem,
    Step,
    MemoryItem,
    Constraint,
    SignatureItem,
    ManifestConstraint,
)

from typing import List, Union
from copy import deepcopy


def is_this_an_agent(item: str, catalog: Catalog) -> bool:
    return item in [agent.id for agent in catalog.agents]


def get_type_of_parameter(catalog: Catalog, agent_name: str, index: int) -> str:
    agent_spec = next(x for x in catalog.agents if x.id == agent_name)
    derived_type = agent_spec.inputs[index].type or TypeOptions.ROOT.value
    return derived_type


def get_all_agent_names_with_this_output(item: str, catalog: Catalog) -> List[str]:
    agent_names = []

    for agent in catalog.agents:
        for output in agent.outputs:
            if isinstance(output, Signature) and item == output.name:
                agent_names.append(agent.id)

    return agent_names


def set_condition_as_goal(
    flow: Flow,
    catalog: Catalog,
    new_constraint: Constraint,
    goal_items: List[Union[Goal, Condition]],
    truth_value: bool = True,
) -> None:
    for goal_item in goal_items:
        if isinstance(goal_item, Goal):
            if is_this_an_agent(goal_item.item, catalog):
                target_agents = [goal_item.item]
            else:
                target_agents = get_all_agent_names_with_this_output(goal_item.item, catalog)

            temp_c = deepcopy(new_constraint)
            temp_c.truth_value = truth_value

            or_goals = []
            for agent_name in target_agents:
                agent_spec = next(x for x in flow.flow_definition.operators if x.name == agent_name)
                agent_spec.inputs.append(SignatureItem(constraints=[temp_c]))
                or_goals.append(GoalItem(goal_name=agent_name, goal_type=GoalType.OPERATOR))

            temp_c = deepcopy(new_constraint)
            temp_c.truth_value = not truth_value

            or_goals.append(GoalItem(goal_name=temp_c, goal_type=GoalType.CONSTRAINT))
            flow.add(GoalItems(goals=or_goals))

        elif isinstance(goal_item, Condition):
            if goal_item.if_outcomes or goal_item.else_outcomes:
                raise ValueError("This should be an assignment.")

            temp_c = deepcopy(new_constraint)
            temp_c.truth_value = truth_value

            goal_c = Constraint(constraint=goal_item.condition, truth_value=ConstraintState.TRUE.value)
            flow.add(
                ManifestConstraint(
                    manifest=goal_c,
                    constraint=temp_c,
                )
            )

            temp_c = deepcopy(new_constraint)
            temp_c.truth_value = not truth_value

            flow.add(
                GoalItems(
                    goals=[
                        GoalItem(
                            goal_name=goal_c,
                            goal_type=GoalType.CONSTRAINT,
                        ),
                        GoalItem(goal_name=temp_c, goal_type=GoalType.CONSTRAINT),
                    ]
                )
            )

        else:
            raise ValueError(f"Unknown conditional outcome {goal_item}")


def sketch_options_compilation(flow: Flow, sketch: Sketch, catalog: Catalog) -> None:
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

    flow.goal_type = GoalOptions.AND_OR


def basic_sketch_compilation(flow: Flow, sketch: Sketch, catalog: Catalog) -> None:
    for component in sketch.components:
        if isinstance(component, Goal):
            if is_this_an_agent(component.item, catalog):
                if not component.parameters:
                    flow.add(GoalItems(goals=GoalItem(goal_name=component.item, goal_type=GoalType.OPERATOR)))
                else:
                    targets = []
                    for index, parameter in enumerate(component.parameters):
                        new_target = parameter.value or parameter.target
                        parameter_type = get_type_of_parameter(catalog, component.item, index)

                        if parameter.value:
                            flow.add(
                                MemoryItem(
                                    item_id=new_target,
                                    item_type=parameter_type,
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

        elif isinstance(component, Ordering):
            if ">" in component.order:
                split_order = component.order.split(">")
                split_order = [item.strip() for item in split_order]
                flow.add(PartialOrder(antecedent=split_order[0], consequent=split_order[1]))
            elif "<" in component.order:
                split_order = component.order.split("<")
                split_order = [item.strip() for item in split_order]
                flow.add(PartialOrder(antecedent=split_order[1], consequent=split_order[0]))
            else:
                raise ValueError(f"Unable to parse ordering in: {component.order}")

        elif isinstance(component, Condition):
            new_constraint = Constraint(constraint=component.condition)

            set_condition_as_goal(flow, catalog, new_constraint, component.if_outcomes)
            set_condition_as_goal(flow, catalog, new_constraint, component.else_outcomes, False)

        elif isinstance(component, Disjunction):
            or_goals = []

            for or_item in component.OR:
                if isinstance(or_item, Goal):
                    if is_this_an_agent(or_item.item, catalog):
                        or_goals.append(GoalItem(goal_name=or_item.item, goal_type=GoalType.OPERATOR))
                    else:
                        or_goals.append(GoalItem(goal_name=or_item.item, goal_type=GoalType.OBJECT_KNOWN))

                elif isinstance(or_item, Condition):
                    if or_item.if_outcomes or or_item.else_outcomes:
                        raise ValueError("This should be an assignment.")

                    goal_c = Constraint(constraint=or_item.condition, truth_value=ConstraintState.TRUE.value)
                    or_goals.append(GoalItem(goal_name=goal_c, goal_type=GoalType.CONSTRAINT))

                else:
                    raise ValueError(f"Unknown disjunction: {or_item}")

            flow.add(GoalItems(goals=or_goals))

    sketch_options_compilation(flow, sketch, catalog)
