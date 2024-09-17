import tarski.fstrips as fs
from tarski.io import fstrips as iofs
from tarski.syntax import land, Atom, Tautology
from typing import Any, Optional
from nl2flow.compile.schemas import Step, Constraint
from nl2flow.compile.options import RestrictedOperations, CostOptions
from nl2flow.debug.schemas import SolutionQuality
from nl2flow.compile.basic_compilations.compile_history import get_predicate_from_constraint, get_predicate_from_step


def compile_reference(compilation: Any, **kwargs: Any) -> None:
    debug_flag: Optional[SolutionQuality] = kwargs.get("debug_flag", None)

    cached_predicates = list()
    token_predicates = list()
    # mapped_items = dict()
    # del_predicates = []

    for index in range(len(compilation.flow_definition.reference.plan) + 1):
        if index < len(compilation.flow_definition.reference.plan):
            item = compilation.flow_definition.reference.plan[index]
            # del_predicates = []

            if isinstance(item, Step):
                indices_of_interest = []

                for i, r in enumerate(compilation.flow_definition.reference.plan):
                    if isinstance(r, Step) and r.name == item.name:
                        indices_of_interest.append(i)

                index_of_operation = indices_of_interest.index(index)

                # if item.name == BasicOperations.MAPPER.value:
                # if item.parameters[1].item_id in mapped_items:
                # del_predicates = [
                #     compilation.mapped_to(
                #         compilation.constant_map[item.parameters[0].item_id],
                #         compilation.constant_map[item.parameters[1].item_id]
                #     ),
                #     compilation.known(
                #         compilation.constant_map[item.parameters[1].item_id],
                #         compilation.constant_map[MemoryState.KNOWN.value],
                #     ),
                # ]

                # mapped_items[item.parameters[1].item_id] = item.parameters[0].item_id

                step_predicate = get_predicate_from_step(compilation, item, index_of_operation, **kwargs)

            elif isinstance(item, Constraint):
                step_predicate = get_predicate_from_constraint(compilation, item)

            else:
                raise ValueError(f"Invalid reference object: {item}")

            if step_predicate:
                cached_predicates.append(step_predicate)

        token_predicate_name = f"token_{index}"
        token_predicate = getattr(compilation, token_predicate_name)()
        token_predicates.append(token_predicate)

        precondition_list = [p for p in cached_predicates[:index]]
        effect_list = [fs.AddEffect(compilation.ready_for_token()), fs.AddEffect(token_predicate)]

        # for del_p in del_predicates:
        #     effect_list.append(fs.DelEffect(del_p))

        for i in range(index):
            shadow_token_predicate_name = f"token_{i}"
            shadow_token_predicate = getattr(compilation, shadow_token_predicate_name)()
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

        if debug_flag == SolutionQuality.OPTIMAL:
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
