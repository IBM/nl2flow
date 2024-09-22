import tarski.fstrips as fs
from tarski.io import fstrips as iofs
from tarski.syntax import land, neg, Atom, Tautology
from typing import Any, Optional, Set, List
from nl2flow.compile.schemas import Step, Constraint, Parameter, OperatorDefinition
from nl2flow.compile.basic_compilations.utils import add_to_condition_list_pre_check
from nl2flow.debug.schemas import SolutionQuality
from nl2flow.compile.options import (
    BasicOperations,
    MemoryState,
    LifeCycleOptions,
    RestrictedOperations,
    CostOptions,
    NL2FlowOptions,
)
from nl2flow.compile.basic_compilations.compile_history import (
    get_predicate_from_constraint,
    get_predicate_from_step,
    get_index_of_interest,
)


def get_token_predicate_name(index: int) -> str:
    return f"token_{index}"


def set_token_predicate(compilation: Any, index: int) -> Any:
    token_predicate_name = get_token_predicate_name(index)
    token_predicate = compilation.lang.predicate(token_predicate_name)
    setattr(compilation, token_predicate_name, token_predicate)

    return token_predicate


def get_token_predicate(compilation: Any, index: int) -> Any:
    token_predicate_name = get_token_predicate_name(index)
    attr = getattr(compilation, token_predicate_name, None)

    if attr:
        return attr()
    else:
        return set_token_predicate(compilation, index)()


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


def compile_reference_basic(compilation: Any, **kwargs: Any) -> None:
    report_type: Optional[SolutionQuality] = kwargs.get("report_type", None)
    optimization_options: Set[NL2FlowOptions] = set(kwargs["optimization_options"])
    variable_life_cycle: Set[LifeCycleOptions] = set(kwargs["variable_life_cycle"])

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

            if step.name == BasicOperations.SLOT_FILLER.value:
                raise NotImplementedError

            elif step.name == BasicOperations.MAPPER.value:
                step_predicate = get_predicate_from_step(compilation, step, **kwargs)

                if step_predicate:
                    goal_predicates.add(step_predicate)

                source = compilation.constant_map[step.parameters[0].item_id]
                target = compilation.constant_map[step.parameters[1].item_id]

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

                action_name = f"{action_name}----{step.parameters[0].item_id}----{step.parameters[1].item_id}"

            elif step.name == BasicOperations.CONFIRM.value:
                raise NotImplementedError

            else:
                index_of_operation = get_index_of_interest(compilation, step, index)
                step_predicate = get_predicate_from_step(compilation, step, index_of_operation, **kwargs)

                if step_predicate:
                    goal_predicates.add(step_predicate)

                    precondition_list.append(neg(step_predicate))
                    add_effect_list.append(step_predicate)

                    operator: OperatorDefinition = next(
                        filter(lambda x: x.name == step.name, compilation.flow_definition.operators)
                    )

                    for param in step.parameters:
                        add_to_condition_list_pre_check(compilation, param.item_id)
                        add_effect_list.append(compilation.been_used(compilation.constant_map[param.item_id]))

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

            compilation.problem.action(
                action_name,
                parameters=[],
                precondition=land(*precondition_list, flat=True),
                effects=[fs.AddEffect(add) for add in add_effect_list]
                + [fs.DelEffect(del_e) for del_e in del_effect_list],
                cost=iofs.AdditiveActionCost(
                    compilation.problem.language.constant(
                        CostOptions.ZERO.value,
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


def compile_reference(compilation: Any, **kwargs: Any) -> None:
    report_type: Optional[SolutionQuality] = kwargs.get("report_type", None)

    cached_predicates = list()
    token_predicates = list()

    for index in range(len(compilation.flow_definition.reference.plan) + 1):
        if index < len(compilation.flow_definition.reference.plan):
            item = compilation.flow_definition.reference.plan[index]

            if isinstance(item, Step):
                index_of_operation = get_index_of_interest(compilation, item, index)
                step_predicate = get_predicate_from_step(compilation, item, index_of_operation, **kwargs)

            elif isinstance(item, Constraint):
                step_predicate = get_predicate_from_constraint(compilation, item)

            else:
                raise ValueError(f"Invalid reference object: {item}")

            if step_predicate:
                cached_predicates.append(step_predicate)

        token_predicate = get_token_predicate(compilation, index)
        token_predicates.append(token_predicate)

        precondition_list = [p for p in cached_predicates[:index]]
        effect_list = [fs.AddEffect(compilation.ready_for_token()), fs.AddEffect(token_predicate)]

        for i in range(index):
            shadow_token_predicate = get_token_predicate(compilation, i)
            precondition_list.append(shadow_token_predicate)

        compilation.problem.action(
            f"{RestrictedOperations.TOKENIZE.value}_{index}",
            parameters=[],
            precondition=land(*precondition_list, flat=True),
            effects=effect_list,
            cost=iofs.AdditiveActionCost(
                compilation.problem.language.constant(
                    CostOptions.EDIT.value,
                    compilation.problem.language.get_sort("Integer"),
                )
            ),
        )

        if report_type == SolutionQuality.OPTIMAL:
            precondition_list = []
            effect_list = [fs.AddEffect(token_predicate)]

            compilation.problem.action(
                f"{RestrictedOperations.UNTOKENIZE.value}_{index}",
                parameters=[],
                precondition=land(*precondition_list, flat=True),
                effects=effect_list,
                cost=iofs.AdditiveActionCost(
                    compilation.problem.language.constant(
                        CostOptions.EDIT.value,
                        compilation.problem.language.get_sort("Integer"),
                    )
                ),
            )

    if compilation.problem.goal is None or isinstance(compilation.problem.goal, Tautology):
        new_goal = land(*token_predicates, flat=True)

    else:
        if isinstance(compilation.problem.goal, Atom):
            sub_formulas = [compilation.problem.goal]
        else:
            sub_formulas = list(compilation.problem.goal.subformulas)

        sub_formulas.extend(token_predicates)
        new_goal = land(*sub_formulas, flat=True)

    compilation.problem.goal = new_goal
