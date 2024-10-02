import tarski.fstrips as fs
from tarski.io import fstrips as iofs
from tarski.syntax import land, neg, Atom, Tautology
from typing import Any, Optional, Set, List
from nl2flow.compile.schemas import Step, Constraint, Parameter, MemoryItem, OperatorDefinition
from nl2flow.compile.basic_compilations.utils import add_to_condition_list_pre_check
from nl2flow.debug.schemas import SolutionQuality
from nl2flow.compile.options import (
    PARAMETER_DELIMITER,
    BasicOperations,
    MemoryState,
    LifeCycleOptions,
    RestrictedOperations,
    CostOptions,
    NL2FlowOptions,
    TypeOptions,
)
from nl2flow.compile.basic_compilations.compile_references.utils import get_token_predicate
from nl2flow.compile.basic_compilations.compile_history import (
    get_predicate_from_step,
    get_index_of_interest,
)


def add_surrogate_goal(
    compilation: Any,
    goal_predicates: Set[Any],
    post_token_predicate: Any,
    target: Any,
    index: int,
) -> None:
    add_to_condition_list_pre_check(compilation, target.name)

    new_index = 100 * (index + 1)
    token_predicate = get_token_predicate(compilation, index=new_index)
    goal_predicates.add(token_predicate)

    precondition_list = [post_token_predicate, compilation.been_used(target)]
    add_effect_list = [token_predicate]

    compilation.problem.action(
        f"{RestrictedOperations.TOKENIZE.value}_{new_index}",
        parameters=[],
        precondition=land(*precondition_list, flat=True),
        effects=[fs.AddEffect(add) for add in add_effect_list],
        cost=iofs.AdditiveActionCost(
            compilation.problem.language.constant(
                CostOptions.ZERO.value,
                compilation.problem.language.get_sort("Integer"),
            )
        ),
    )

    precondition_list = [post_token_predicate]
    add_effect_list = [token_predicate]

    compilation.problem.action(
        f"{RestrictedOperations.UNTOKENIZE.value}_{new_index}",
        parameters=[],
        precondition=land(*precondition_list, flat=True),
        effects=[fs.AddEffect(add) for add in add_effect_list],
        cost=iofs.AdditiveActionCost(
            compilation.problem.language.constant(
                CostOptions.HIGH.value,
                compilation.problem.language.get_sort("Integer"),
            )
        ),
    )


def add_instantiated_map(
    compilation: Any,
    step: Step,
    index: int,
    goal_predicates: Set[Any],
    precondition_list: List[Any],
    add_effect_list: List[Any],
    del_effect_list: List[Any],
    post_token_predicate: Any,
    **kwargs: Any,
) -> Optional[Any]:
    variable_life_cycle: Set[LifeCycleOptions] = set(kwargs["variable_life_cycle"])

    for item in step.parameters[:2]:
        add_to_condition_list_pre_check(compilation, item)

    step_predicate = get_predicate_from_step(compilation, step, **kwargs)

    if step_predicate:
        goal_predicates.add(step_predicate)

    source = compilation.constant_map[step.parameter(0)]
    target = compilation.constant_map[step.parameter(1)]

    if step.label:
        precondition_list.append(
            compilation.label_tag(source, compilation.constant_map[step.label]),
        )

        add_effect_list.append(compilation.label_tag(target, compilation.constant_map[step.label]))

    add_surrogate_goal(compilation, goal_predicates, post_token_predicate, target, index)

    precondition_list.extend(
        [
            compilation.known(source, compilation.constant_map[MemoryState.KNOWN.value]),
            compilation.is_mappable(source, target),
            compilation.been_used(target),
            neg(compilation.not_mappable(source, target)),
            neg(compilation.new_item(source)),
        ]
    )

    add_effect_list.extend(
        [
            compilation.known(
                target,
                compilation.constant_map[MemoryState.UNCERTAIN.value]
                if LifeCycleOptions.confirm_on_mapping in variable_life_cycle
                else compilation.constant_map[MemoryState.KNOWN.value],
            ),
            compilation.mapped_to(source, target),
            compilation.mapped(source),
        ]
    )

    del_effect_list.extend(
        [
            compilation.been_used(target),
            compilation.not_usable(target),
        ]
    )

    return step_predicate


def add_instantiated_operation(
    compilation: Any,
    step: Step,
    index: int,
    goal_predicates: Set[Any],
    precondition_list: List[Any],
    add_effect_list: List[Any],
    del_effect_list: List[Any],
    **kwargs: Any,
) -> Optional[Any]:
    variable_life_cycle: Set[LifeCycleOptions] = set(kwargs["variable_life_cycle"])
    repeat_index = get_index_of_interest(compilation, step, index)
    step_predicate = get_predicate_from_step(compilation, step, repeat_index, **kwargs)

    if step_predicate:
        goal_predicates.add(step_predicate)

        precondition_list.append(neg(step_predicate))
        add_effect_list.append(step_predicate)

        operator: OperatorDefinition = next(
            filter(lambda x: x.name == step.name, compilation.flow_definition.operators)
        )

        for i, param in enumerate(step.parameters):
            add_to_condition_list_pre_check(compilation, step.parameter(i))
            add_effect_list.append(compilation.been_used(compilation.constant_map[step.parameter(i)]))

        for o_input in operator.inputs:
            for param in o_input.parameters:
                add_to_condition_list_pre_check(compilation, param)

                if isinstance(param, Parameter):
                    param = param.item_id

                precondition_list.append(
                    compilation.known(
                        compilation.constant_map[param],
                        compilation.constant_map[MemoryState.KNOWN.value],
                    )
                )

        outputs = operator.outputs[0]
        for o_output in outputs.outcomes:
            for param in o_output.parameters:
                add_to_condition_list_pre_check(compilation, param)

                if isinstance(param, Parameter):
                    param = param.item_id

                del_effect_list.append(compilation.mapped(compilation.constant_map[param]))
                add_effect_list.extend(
                    [
                        compilation.free(compilation.constant_map[param]),
                        compilation.known(
                            compilation.constant_map[param],
                            compilation.constant_map[MemoryState.UNCERTAIN.value]
                            if LifeCycleOptions.confirm_on_determination in variable_life_cycle
                            else compilation.constant_map[MemoryState.KNOWN.value],
                        ),
                    ]
                )

                if step.label:
                    add_effect_list.append(
                        compilation.label_tag(compilation.constant_map[param], compilation.constant_map[step.label])
                    )

    return step_predicate


def compile_reference_basic(compilation: Any, **kwargs: Any) -> None:
    report_type: Optional[SolutionQuality] = kwargs.get("report_type", None)
    optimization_options: Set[NL2FlowOptions] = set(kwargs["optimization_options"])

    if report_type != SolutionQuality.SOUND:
        raise NotImplementedError

    if NL2FlowOptions.multi_instance in optimization_options:
        raise NotImplementedError

    goal_predicates = set()

    for index, step in enumerate(compilation.flow_definition.reference.plan):
        pre_token_predicate = get_token_predicate(compilation, index)
        post_token_predicate = get_token_predicate(compilation, index + 1)

        goal_predicates.add(post_token_predicate)

        precondition_list = [pre_token_predicate]
        add_effect_list = [post_token_predicate]
        del_effect_list: List[Any] = []

        compilation.problem.action(
            f"{RestrictedOperations.UNTOKENIZE.value}_{index}_{step.name}",
            parameters=[],
            precondition=land(*precondition_list, flat=True),
            effects=[fs.AddEffect(add) for add in add_effect_list],
            cost=iofs.AdditiveActionCost(
                compilation.problem.language.constant(
                    CostOptions.HIGH.value,
                    compilation.problem.language.get_sort("Integer"),
                )
            ),
        )

        if isinstance(step, Step):
            action_name = f"{RestrictedOperations.TOKENIZE.value}_{index}//{step.name}"

            if step.label and step.label not in compilation.constant_map:
                add_to_condition_list_pre_check(
                    compilation, MemoryItem(item_id=step.label, item_type=TypeOptions.LABEL.value)
                )

            if step.name == BasicOperations.SLOT_FILLER.value:
                raise NotImplementedError

            elif step.name == BasicOperations.MAPPER.value:
                action_name = (
                    f"{action_name}{PARAMETER_DELIMITER}{step.parameter(0)}{PARAMETER_DELIMITER}{step.parameter(1)}"
                )
                step_predicate = add_instantiated_map(
                    compilation,
                    step,
                    index,
                    goal_predicates,
                    precondition_list,
                    add_effect_list,
                    del_effect_list,
                    post_token_predicate,
                    **kwargs,
                )

            elif step.name == BasicOperations.CONFIRM.value:
                raise NotImplementedError

            else:
                step_predicate = add_instantiated_operation(
                    compilation,
                    step,
                    index,
                    goal_predicates,
                    precondition_list,
                    add_effect_list,
                    del_effect_list,
                    **kwargs,
                )

            if step.label:
                action_name = f"{action_name}{PARAMETER_DELIMITER}{step.label}"

            if step_predicate:
                compilation.problem.action(
                    action_name,
                    parameters=[],
                    precondition=land(*precondition_list, flat=True),
                    effects=[fs.AddEffect(add) for add in add_effect_list]
                    + [fs.DelEffect(del_e) for del_e in del_effect_list],
                    cost=iofs.AdditiveActionCost(
                        compilation.problem.language.constant(
                            CostOptions.UNIT.value + len(step.parameters),
                            compilation.problem.language.get_sort("Integer"),
                        )
                    ),
                )

        elif isinstance(step, Constraint):
            raise NotImplementedError
        else:
            raise ValueError(f"Invalid reference object: {step}")

    if compilation.problem.goal is None or isinstance(compilation.problem.goal, Tautology):
        new_goal = land(*goal_predicates, flat=True)

    else:
        if isinstance(compilation.problem.goal, Atom):
            sub_formulas = [compilation.problem.goal]
        else:
            sub_formulas = list(compilation.problem.goal.subformulas)

        sub_formulas.extend(goal_predicates)
        new_goal = land(*sub_formulas, flat=True)

    compilation.problem.goal = new_goal
