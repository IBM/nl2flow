import tarski.fstrips as fs
from tarski.io import fstrips as iofs
from tarski.syntax import land, neg
from typing import Any, Set

from nl2flow.compile.schemas import Step, Constraint
from nl2flow.compile.basic_compilations.compile_history import get_predicate_from_constraint, get_predicate_from_step
from nl2flow.compile.options import LifeCycleOptions, RestrictedOperations, CostOptions


def compile_reference(compilation: Any, **kwargs: Any) -> None:
    variable_life_cycle: Set[LifeCycleOptions] = set(kwargs["variable_life_cycle"])

    cached_predicates = []
    for index, item in enumerate(compilation.flow_definition.reference.plan):
        if isinstance(item, Step):
            indices_of_interest = []

            for i, r in enumerate(compilation.flow_definition.reference.plan):
                if isinstance(r, Step) and r.name == item.name:
                    indices_of_interest.append(i)

            index_of_operation = indices_of_interest.index(index) + 1
            step_predicate = get_predicate_from_step(compilation, item, variable_life_cycle, index_of_operation)

        elif isinstance(item, Constraint):
            step_predicate = get_predicate_from_constraint(compilation, item)

        else:
            raise ValueError(f"Invalid reference object: {item}")

        cached_predicates.append(step_predicate)

        precondition_list = [p for p in cached_predicates[:index]]
        precondition_list.append(neg(compilation.ready_for_token()))
        effect_list = [fs.AddEffect(compilation.ready_for_token())]

        compilation.problem.action(
            f"{RestrictedOperations.TOKENIZE.value}_{index}",
            parameters=[],
            precondition=land(*precondition_list, flat=True),
            effects=effect_list,
            cost=iofs.AdditiveActionCost(
                compilation.problem.language.constant(
                    CostOptions.ZERO.value,
                    compilation.problem.language.get_sort("Integer"),
                )
            ),
        )

    if compilation.problem.goal is None:
        new_goal = land(*cached_predicates, flat=True)

    else:
        sub_formulas = list(compilation.problem.goal.subformulas)
        sub_formulas.extend(cached_predicates)

        new_goal = land(*sub_formulas, flat=True)

    compilation.problem.goal = new_goal
