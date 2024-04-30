import copy
import tarski.fstrips as fs
from tarski.io import fstrips as iofs
from tarski.syntax import land, neg
from typing import List, Set, Any, Optional

from nl2flow.compile.basic_compilations.utils import (
    add_to_condition_list_pre_check,
    get_type_of_constant,
)

from nl2flow.compile.basic_compilations.compile_constraints import compile_constraints
from nl2flow.compile.schemas import FlowDefinition, OperatorDefinition, Parameter
from nl2flow.debug.schemas import SolutionQuality
from nl2flow.compile.options import (
    TypeOptions,
    LifeCycleOptions,
    MappingOptions,
    RestrictedOperations,
    CostOptions,
    MemoryState,
    HasDoneState,
    NL2FlowOptions,
)


def compile_operators(compilation: Any, **kwargs: Any) -> None:
    flow_definition: FlowDefinition = compilation.flow_definition
    list_of_actions: List[OperatorDefinition] = flow_definition.operators
    debug_flag: Optional[SolutionQuality] = kwargs.get("debug_flag", None)
    optimization_options: Set[NL2FlowOptions] = set(kwargs["optimization_options"])
    variable_life_cycle: Set[LifeCycleOptions] = set(kwargs["variable_life_cycle"])
    mapping_options: Set[MappingOptions] = set(kwargs["mapping_options"])

    for operator in list_of_actions:
        compilation.constant_map[operator.name] = compilation.lang.constant(operator.name, TypeOptions.OPERATOR.value)

    for operator in list_of_actions:
        parameter_list: List[Any] = list()
        precondition_list: List[Any] = list()
        add_effect_list = [
            compilation.has_done(
                compilation.constant_map[operator.name],
                compilation.constant_map[HasDoneState.present.value],
            )
        ]
        del_effect_list = list()
        type_list = list()

        if debug_flag:
            precondition_list.append(compilation.ready_for_token())
            del_effect_list.append(compilation.ready_for_token())

        for index_of_input, o_input in enumerate(operator.inputs):
            for index_of_nested_input, param in enumerate(o_input.parameters):
                add_to_condition_list_pre_check(compilation, param)
                index_of_param = index_of_input + list(o_input.parameters).index(param)

                if isinstance(param, Parameter):
                    type_of_param = param.item_type or TypeOptions.ROOT.value
                    param = param.item_id
                else:
                    type_of_param = get_type_of_constant(compilation, param)

                if NL2FlowOptions.multi_instance in optimization_options:
                    x = compilation.lang.variable(
                        f"x{index_of_param}{index_of_nested_input}", compilation.type_map[type_of_param]
                    )

                    parameter_list.append(x)
                    type_list.append(type_of_param)

                    precondition_list.append(compilation.mapped_to(x, compilation.constant_map[param]))
                    add_effect_list.append(compilation.been_used(x))

                    if NL2FlowOptions.multi_instance in optimization_options:
                        precondition_list.append(neg(compilation.not_usable(x)))

                compilation.init.add(compilation.been_used(compilation.constant_map[param]))
                add_effect_list.append(compilation.been_used(compilation.constant_map[param]))
                precondition_list.append(
                    compilation.known(
                        compilation.constant_map[param],
                        compilation.constant_map[MemoryState.KNOWN.value],
                    )
                )

                if MappingOptions.prohibit_direct in mapping_options:
                    compilation.init.add(compilation.not_usable(compilation.constant_map[param]))

                if LifeCycleOptions.uncertain_on_use in variable_life_cycle:
                    del_effect_list.append(
                        compilation.known(
                            compilation.constant_map[param],
                            compilation.constant_map[MemoryState.KNOWN.value],
                        )
                    )

                    add_effect_list.append(
                        compilation.known(
                            compilation.constant_map[param],
                            compilation.constant_map[MemoryState.UNCERTAIN.value],
                        )
                    )

            for constraint in o_input.constraints:
                constraint_predicate = compile_constraints(compilation, constraint, **kwargs)
                precondition_list.append(constraint_predicate)

        if (
            NL2FlowOptions.allow_retries in optimization_options
            or NL2FlowOptions.multi_instance in optimization_options
        ):
            add_multi_instance_properties(
                compilation, operator, parameter_list, type_list, precondition_list, add_effect_list, **kwargs
            )

        else:
            precondition_list.append(
                neg(
                    compilation.has_done(
                        compilation.constant_map[operator.name],
                        compilation.constant_map[HasDoneState.past.value],
                    )
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

            for constraint in o_output.constraints:
                constraint_predicate = compile_constraints(compilation, constraint, **kwargs)
                add_effect_list.append(constraint_predicate)

        add_partial_orders(compilation, operator, precondition_list)
        compilation.problem.action(
            operator.name,
            parameters=parameter_list,
            precondition=land(*precondition_list, flat=True),
            effects=[fs.AddEffect(add) for add in add_effect_list] + [fs.DelEffect(del_e) for del_e in del_effect_list],
            cost=iofs.AdditiveActionCost(
                compilation.problem.language.constant(operator.cost, compilation.problem.language.get_sort("Integer"))
            ),
        )


def add_multi_instance_properties(
    compilation: Any,
    operator: OperatorDefinition,
    parameter_list: List[Any],
    type_list: List[str],
    precondition_list: List[Any],
    add_effect_list: List[Any],
    **kwargs: Any,
) -> None:
    optimization_options: Set[NL2FlowOptions] = set(kwargs["optimization_options"])
    new_has_done_predicate_name = f"has_done_{operator.name}"
    has_done_parameters = []

    if NL2FlowOptions.multi_instance in optimization_options:
        has_done_parameters = [compilation.type_map[type_name] for type_name in type_list]

    if NL2FlowOptions.allow_retries in optimization_options:
        has_done_parameters.append(compilation.type_map[TypeOptions.RETRY.value])

    new_has_done_predicate = compilation.lang.predicate(
        new_has_done_predicate_name,
        *has_done_parameters,
    )

    setattr(compilation, new_has_done_predicate_name, new_has_done_predicate)

    if NL2FlowOptions.allow_retries in optimization_options:
        pre_level = compilation.lang.variable("pre_level", compilation.type_map[TypeOptions.RETRY.value])
        post_level = compilation.lang.variable("post_level", compilation.type_map[TypeOptions.RETRY.value])

        precondition_list.extend(
            [
                getattr(compilation, new_has_done_predicate_name)(*parameter_list, pre_level),
                neg(getattr(compilation, new_has_done_predicate_name)(*parameter_list, post_level)),
                compilation.connected(compilation.constant_map[operator.name], pre_level, post_level),
            ]
        )

        add_effect_list.append(getattr(compilation, new_has_done_predicate_name)(*parameter_list, post_level))

        for try_level in range(operator.max_try):
            compilation.init.add(
                compilation.connected(
                    compilation.constant_map[operator.name],
                    compilation.constant_map[f"try_level_{try_level}"],
                    compilation.constant_map[f"try_level_{try_level + 1}"],
                )
            )

        add_enabler_action_for_operator(compilation, operator, parameter_list, new_has_done_predicate_name)
        parameter_list.extend([pre_level, post_level])

    else:
        precondition_list.append(
            neg(getattr(compilation, new_has_done_predicate_name)(*parameter_list)),
        )

        add_effect_list.append(getattr(compilation, new_has_done_predicate_name)(*parameter_list))
        # add_enabler_action_for_operator(compilation, operator, parameter_list, new_has_done_predicate_name)


def add_enabler_action_for_operator(
    compilation: Any,
    operator: OperatorDefinition,
    parameter_list: List[Any],
    new_has_done_predicate_name: Any,
) -> None:
    enabler_predicate = getattr(compilation, new_has_done_predicate_name)(
        *parameter_list, compilation.constant_map["try_level_0"]
    )

    shadow_predicate = getattr(compilation, new_has_done_predicate_name)(
        *parameter_list, compilation.constant_map["try_level_1"]
    )

    compilation.problem.action(
        f"{RestrictedOperations.ENABLER.value}__{operator.name}",
        parameters=copy.deepcopy(parameter_list),
        precondition=land(*[neg(enabler_predicate), neg(shadow_predicate)], flat=True),
        effects=[fs.AddEffect(enabler_predicate)],
        cost=iofs.AdditiveActionCost(
            compilation.problem.language.constant(
                CostOptions.HIGH.value,
                compilation.problem.language.get_sort("Integer"),
            )
        ),
    )


def add_partial_orders(compilation: Any, operator: OperatorDefinition, precondition_list: List[Any]) -> None:
    for partial_order in compilation.flow_definition.partial_orders:
        if partial_order.consequent == operator.name and partial_order.antecedent not in [
            o.name for o in compilation.flow_definition.history
        ]:
            precondition_list.append(
                compilation.has_done(
                    compilation.constant_map[partial_order.antecedent],
                    compilation.constant_map[HasDoneState.present.value],
                )
            )

        if partial_order.antecedent == operator.name:
            precondition_list.append(
                neg(
                    compilation.has_done(
                        compilation.constant_map[partial_order.consequent],
                        compilation.constant_map[HasDoneState.past.value],
                    )
                )
            )

    if compilation.flow_definition.starts_with and compilation.flow_definition.starts_with != operator.name:
        precondition_list.append(
            compilation.has_done(
                compilation.constant_map[compilation.flow_definition.starts_with],
                compilation.constant_map[HasDoneState.present.value],
            )
        )

    if compilation.flow_definition.ends_with:
        precondition_list.append(
            neg(
                compilation.has_done(
                    compilation.constant_map[compilation.flow_definition.ends_with],
                    compilation.constant_map[HasDoneState.present.value],
                )
            )
        )
