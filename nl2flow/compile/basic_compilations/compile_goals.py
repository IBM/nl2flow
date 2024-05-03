import tarski.fstrips as fs
from tarski.io import fstrips as iofs
from tarski.syntax import land
from typing import List, Set, Any, Optional
from nl2flow.compile.basic_compilations.utils import get_type_of_constant, add_memory_item_to_constant_map
from nl2flow.compile.basic_compilations.utils import unpack_list_of_signature_items
from nl2flow.compile.basic_compilations.compile_constraints import compile_constraints
from nl2flow.debug.schemas import SolutionQuality
from nl2flow.compile.schemas import GoalItem, GoalItems, MemoryItem, Constraint, Step, Parameter
from nl2flow.compile.options import (
    TypeOptions,
    GoalType,
    GoalOptions,
    RestrictedOperations,
    CostOptions,
    MemoryState,
    HasDoneState,
    NL2FlowOptions,
)


def get_orphaned_items(compilation: Any, goal_items: List[str]) -> List[str]:
    list_of_neighs = list()
    list_of_orphans = list()

    for item in compilation.flow_definition.memory_items:
        list_of_neighs.append(item.item_id)

    for operator in compilation.flow_definition.operators:
        input_names = unpack_list_of_signature_items(operator.inputs)
        list_of_neighs.extend(input_names)

        output = operator.outputs
        if isinstance(output, List):
            output = output[0]

        output_names = unpack_list_of_signature_items(output.outcomes)
        list_of_neighs.extend(output_names)

    for item in goal_items:
        if item not in list_of_neighs:
            list_of_orphans.append(item)

    return list_of_orphans


def compile_goal_item(compilation: Any, goal_item: GoalItem, goal_predicates: Set[Any], **kwargs: Any) -> None:
    optimization_options: Set[NL2FlowOptions] = set(kwargs["optimization_options"])

    if goal_item.goal_type == GoalType.OPERATOR:
        goal = goal_item.goal_name

        if isinstance(goal, Step):
            new_goal_predicate = f"has_done_{goal.name}"
            new_goal_parameters = (
                []
                if NL2FlowOptions.multi_instance not in optimization_options
                else [
                    compilation.constant_map[p.item_id] if isinstance(p, Parameter) else compilation.constant_map[p]
                    for p in goal.parameters
                ]
            )

            if NL2FlowOptions.allow_retries in optimization_options:
                try_level = 1
                for historical_step in compilation.flow_definition.history:
                    try_level += int(goal == historical_step)

                try_level_parameter = compilation.constant_map[f"try_level_{try_level}"]
                new_goal_parameters.append(try_level_parameter)

            if new_goal_parameters:
                goal_predicates.add(getattr(compilation, new_goal_predicate)(*new_goal_parameters))
            else:
                goal_predicates.add(
                    compilation.has_done(
                        compilation.constant_map[goal.name],
                        compilation.constant_map[HasDoneState.present.value],
                    )
                )

        elif isinstance(goal, str):
            goal_predicates.add(
                compilation.has_done(
                    compilation.constant_map[goal],
                    compilation.constant_map[HasDoneState.present.value],
                )
            )

        else:
            TypeError("Unrecognized goal type.")

    elif goal_item.goal_type == GoalType.CONSTRAINT and isinstance(goal_item.goal_name, Constraint):
        temp = compile_constraints(compilation, goal_item.goal_name, **kwargs)
        goal_predicates.add(temp)

    else:
        list_of_constants = list()
        if goal_item.goal_name in compilation.type_map:
            for item in compilation.constant_map:
                type_of_item = get_type_of_constant(compilation, item)

                if type_of_item == goal_item.goal_name and "new_object" not in item:
                    list_of_constants.append(item)
        else:
            list_of_constants = [goal_item.goal_name]

        for item in list_of_constants:
            if item not in compilation.constant_map:
                add_memory_item_to_constant_map(
                    compilation,
                    memory_item=MemoryItem(
                        item_id=item, item_type=TypeOptions.ROOT.value, item_state=MemoryState.UNKNOWN.value
                    ),
                )

        for item in list_of_constants:
            if goal_item.goal_type == GoalType.OBJECT_USED:
                goal_predicates.add(compilation.been_used(compilation.constant_map[item]))

            elif goal_item.goal_type == GoalType.OBJECT_KNOWN:
                goal_predicates.add(
                    compilation.known(
                        compilation.constant_map[item],
                        compilation.constant_map[MemoryState.KNOWN.value],
                    )
                )

                orphaned_items = get_orphaned_items(compilation, list_of_constants)
                for orphan in orphaned_items:
                    compilation.init.add(compilation.been_used(compilation.constant_map[orphan]))

            else:
                raise TypeError("Unrecognized goal type.")


def compile_goals(compilation: Any, **kwargs: Any) -> None:
    goal_type: GoalOptions = kwargs["goal_type"]
    debug_flag: Optional[SolutionQuality] = kwargs.get("debug_flag", None)

    list_of_goal_items: List[GoalItems] = compilation.flow_definition.goal_items
    goal_predicates: Set[Any]

    if goal_type == GoalOptions.AND_AND:
        goal_predicates = set()

        for goal_items in list_of_goal_items:
            for goal_item in goal_items.goals:
                compile_goal_item(compilation, goal_item, goal_predicates, **kwargs)

        if debug_flag is None or debug_flag != SolutionQuality.SOUND:
            compilation.problem.goal = land(*goal_predicates, flat=True)

    elif goal_type == GoalOptions.OR_AND:
        for goal_index, goal_items in enumerate(list_of_goal_items):
            goal_predicates = set()
            for goal_item in goal_items.goals:
                compile_goal_item(compilation, goal_item, goal_predicates, **kwargs)

            compilation.problem.action(
                f"{RestrictedOperations.GOAL.value}-{goal_index}",
                parameters=[],
                precondition=land(*goal_predicates, flat=True),
                effects=[fs.AddEffect(compilation.done_goal_pre())],
                cost=iofs.AdditiveActionCost(
                    compilation.problem.language.constant(
                        CostOptions.VERY_HIGH.value,
                        compilation.problem.language.get_sort("Integer"),
                    )
                ),
            )

        if debug_flag is None or debug_flag != SolutionQuality.SOUND:
            compilation.problem.goal = compilation.done_goal_post()
            compilation.problem.action(
                f"{RestrictedOperations.GOAL.value}",
                parameters=[],
                precondition=compilation.done_goal_pre(),
                effects=[fs.AddEffect(compilation.done_goal_post())],
                cost=iofs.AdditiveActionCost(
                    compilation.problem.language.constant(
                        CostOptions.VERY_HIGH.value,
                        compilation.problem.language.get_sort("Integer"),
                    )
                ),
            )

    elif goal_type == GoalOptions.AND_OR:
        goal_predicates = set()

        for goal_index, goal_items in enumerate(list_of_goal_items):
            new_goal_predicate_name = f"has_done_pre_{goal_index}"
            new_goal_predicate = compilation.lang.predicate(new_goal_predicate_name)

            setattr(compilation, new_goal_predicate_name, new_goal_predicate)

            new_goal = getattr(compilation, new_goal_predicate_name)()
            goal_predicates.add(new_goal)

            goals = goal_items.goals if isinstance(goal_items.goals, List) else [goal_items.goals]
            for goal_item_index, goal_item in enumerate(goals):
                precondition_set: Set[Any] = set()

                compile_goal_item(compilation, goal_item, precondition_set, **kwargs)
                compilation.problem.action(
                    f"{RestrictedOperations.GOAL.value}-{goal_index}-{goal_item_index}",
                    parameters=[],
                    precondition=land(*precondition_set, flat=True),
                    effects=[fs.AddEffect(new_goal)],
                    cost=iofs.AdditiveActionCost(
                        compilation.problem.language.constant(
                            CostOptions.VERY_HIGH.value,
                            compilation.problem.language.get_sort("Integer"),
                        )
                    ),
                )

        if debug_flag is None or debug_flag != SolutionQuality.SOUND:
            compilation.problem.goal = land(*goal_predicates, flat=True)

    else:
        raise TypeError("Unrecognized goal option.")
