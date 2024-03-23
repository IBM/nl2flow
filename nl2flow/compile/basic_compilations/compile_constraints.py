import tarski.fstrips as fs
from tarski.io import fstrips as iofs
from tarski.syntax import land, neg
from typing import Any

from nl2flow.compile.basic_compilations.utils import add_memory_item_to_constant_map, get_type_of_constant

from nl2flow.compile.schemas import Constraint, MemoryItem
from nl2flow.compile.options import (
    TypeOptions,
    BasicOperations,
    RestrictedOperations,
    CostOptions,
    MemoryState,
    ConstraintState,
)


def compile_manifest_constraints(compilation: Any) -> None:
    for manifest_constraint in compilation.flow_definition.manifest_constraints:
        manifest_predicate = compile_constraints(compilation, manifest_constraint.manifest)
        reference_predicate = compile_constraints(compilation, manifest_constraint.constraint)

        compilation.problem.action(
            f"{RestrictedOperations.MANIFEST.value}_{manifest_constraint.manifest.constraint_id}",
            parameters=list(),
            precondition=land(reference_predicate),
            effects=[fs.AddEffect(manifest_predicate)],
            cost=iofs.AdditiveActionCost(
                compilation.problem.language.constant(
                    CostOptions.UNIT.value,
                    compilation.problem.language.get_sort("Integer"),
                )
            ),
        )


def compile_constraints(
    compilation: Any,
    constraint: Constraint,
) -> Any:
    new_constraint_variable = f"status_{constraint.constraint_id}"
    set_variables = list()
    for item in constraint.parameters:
        if item not in compilation.constant_map:
            add_memory_item_to_constant_map(
                compilation,
                MemoryItem(item_id=item, item_type=TypeOptions.ROOT.value),
            )
        set_variables.append(compilation.constant_map[item])

    closed_variables = [
        compilation.type_map[get_type_of_constant(compilation, item)] for item in constraint.parameters
    ] + [compilation.type_map[TypeOptions.STATUS.value]]

    if new_constraint_variable not in [item.symbol for item in compilation.lang.predicates]:
        new_constraint_predicate = compilation.lang.predicate(
            new_constraint_variable,
            *closed_variables,
        )

        setattr(compilation, new_constraint_variable, new_constraint_predicate)

        for truth_value in ConstraintState:
            operator_name = f"{BasicOperations.CONSTRAINT.value}_{constraint.constraint_id}_to_{truth_value.value}"

            precondition_list = list()
            add_effect_list = list()
            del_effect_list = list()

            for index, parameter in enumerate(constraint.parameters):
                del_effect_list.append(compilation.free(compilation.constant_map[parameter]))
                precondition_list.extend(
                    [
                        compilation.known(
                            compilation.constant_map[parameter],
                            compilation.constant_map[MemoryState.KNOWN.value],
                        ),
                    ]
                )

                set_predicate = getattr(compilation, new_constraint_variable)(
                    *set_variables, compilation.constant_map[str(truth_value.value)]
                )
                shadow_predicate = getattr(compilation, new_constraint_variable)(
                    *set_variables, compilation.constant_map[str(not truth_value.value)]
                )

                enabler_name = f"{RestrictedOperations.ENABLER.value}__{constraint.constraint_id}_{parameter}"

                if enabler_name not in compilation.problem.actions:
                    compilation.problem.action(
                        enabler_name,
                        parameters=list(),
                        precondition=land(compilation.free(compilation.constant_map[parameter])),
                        effects=[
                            fs.DelEffect(set_predicate),
                            fs.DelEffect(shadow_predicate),
                        ],
                        cost=iofs.AdditiveActionCost(
                            compilation.problem.language.constant(
                                CostOptions.UNIT.value,
                                compilation.problem.language.get_sort("Integer"),
                            )
                        ),
                    )

            set_predicate = getattr(compilation, new_constraint_variable)(
                *set_variables, compilation.constant_map[str(truth_value.value)]
            )
            shadow_predicate = getattr(compilation, new_constraint_variable)(
                *set_variables, compilation.constant_map[str(not truth_value.value)]
            )
            add_effect_list.append(set_predicate)
            precondition_list.extend(
                [
                    neg(set_predicate),
                    neg(shadow_predicate),
                ]
            )

            if operator_name not in compilation.problem.actions:
                compilation.problem.action(
                    operator_name,
                    parameters=list(),
                    precondition=land(*precondition_list, flat=True),
                    effects=[fs.AddEffect(add) for add in add_effect_list]
                    + [fs.DelEffect(del_e) for del_e in del_effect_list],
                    cost=iofs.AdditiveActionCost(
                        compilation.problem.language.constant(
                            CostOptions.VERY_LOW.value,
                            compilation.problem.language.get_sort("Integer"),
                        )
                    ),
                )

    for known_constraint in compilation.flow_definition.constraints:
        if known_constraint.constraint_id == constraint.constraint_id:
            compilation.init.add(
                getattr(compilation, new_constraint_variable)(
                    *set_variables,
                    compilation.constant_map[str(known_constraint.truth_value)],
                )
            )

    return getattr(compilation, new_constraint_variable)(
        *set_variables, compilation.constant_map[str(constraint.truth_value)]
    )
