import tarski.fstrips as fs
from tarski.io import fstrips as iofs
from tarski.syntax import land, Atom, Tautology
from typing import Any, Optional
from nl2flow.compile.schemas import Step, Constraint
from nl2flow.debug.schemas import SolutionQuality
from nl2flow.compile.options import (
    BasicOperations,
    RestrictedOperations,
    CostOptions,
)
from nl2flow.compile.basic_compilations.compile_references.utils import get_token_predicate
from nl2flow.compile.basic_compilations.compile_history import (
    get_predicate_from_constraint,
    get_predicate_from_step,
    get_index_of_interest,
)


def compile_reference_tokenize(compilation: Any, **kwargs: Any) -> None:
    report_type: Optional[SolutionQuality] = kwargs.get("report_type", None)

    cached_predicates = list()
    token_predicates = list()
    operator_index = 0

    for index in range(len(compilation.flow_definition.reference.plan) + 1):
        if index < len(compilation.flow_definition.reference.plan):
            item = compilation.flow_definition.reference.plan[index]

            if isinstance(item, Step):
                if not BasicOperations.is_basic(item.name):
                    operator_index += 1

                repeat_index = get_index_of_interest(compilation, item, index)
                step_predicate = get_predicate_from_step(compilation, item, repeat_index, operator_index, **kwargs)

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
