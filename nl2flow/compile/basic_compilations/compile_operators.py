import copy
import tarski.fstrips as fs
from tarski.io import fstrips as iofs
from tarski.syntax import land, lor, neg, CompoundFormula
from typing import List, Set, Any, Optional

from nl2flow.compile.basic_compilations.utils import (
    add_to_condition_list_pre_check,
    get_type_of_constant,
)

from nl2flow.compile.basic_compilations.compile_constraints import compile_constraints
from nl2flow.compile.basic_compilations.compile_references.utils import get_token_predicate_name
from nl2flow.compile.schemas import FlowDefinition, OperatorDefinition, Parameter
from nl2flow.debug.schemas import DebugFlag
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
    debug_flag: Optional[DebugFlag] = kwargs.get("debug_flag", None)
    optimization_options: Set[NL2FlowOptions] = set(kwargs["optimization_options"])
    variable_life_cycle: Set[LifeCycleOptions] = set(kwargs["variable_life_cycle"])
    mapping_options: Set[MappingOptions] = set(kwargs["mapping_options"])

    for operator in list_of_actions:
        compilation.constant_map[operator.name] = compilation.lang.constant(operator.name, TypeOptions.OPERATOR.value)

    for operator in list_of_actions:
        parameter_list: List[Any] = list()
        precondition_list: List[Any] = list()
        must_know_list: List[Any] = list()
        optional_know_list: List[Any] = list()
        add_effect_list = [
            compilation.has_done(
                compilation.constant_map[operator.name],
                compilation.constant_map[HasDoneState.present.value],
            )
        ]
        del_effect_list = list()
        type_list = list()

        if debug_flag == DebugFlag.TOKENIZE:
            precondition_list.append(compilation.ready_for_token())
            del_effect_list.append(compilation.ready_for_token())

        for index_of_input, o_input in enumerate(operator.inputs):
            for index_of_nested_input, param in enumerate(o_input.parameters):
                add_to_condition_list_pre_check(compilation, param)
                index_of_param = index_of_input + list(o_input.parameters).index(param)
                type_of_param = (
                    param.item_type or TypeOptions.ROOT.value
                    if isinstance(param, Parameter)
                    else get_type_of_constant(compilation, param)
                )

                param_name = param.item_id if isinstance(param, Parameter) else param

                if NL2FlowOptions.multi_instance in optimization_options:
                    x = compilation.lang.variable(
                        f"x{index_of_param}{index_of_nested_input}", compilation.type_map[type_of_param]
                    )

                    parameter_list.append(x)
                    type_list.append(type_of_param)

                    add_effect_list.append(compilation.been_used(x))
                    precondition_list.extend(
                        [
                            compilation.mapped_to(x, compilation.constant_map[param_name]),
                            neg(compilation.not_usable(x)),
                        ]
                    )

                compilation.init.add(compilation.been_used(compilation.constant_map[param_name]))
                add_effect_list.append(compilation.been_used(compilation.constant_map[param_name]))

                if isinstance(param, Parameter) and not param.required:
                    optional_know_list.append(param_name)
                else:
                    must_know_list.append(param_name)

                if MappingOptions.prohibit_direct in mapping_options:
                    compilation.init.add(compilation.not_usable(compilation.constant_map[param_name]))

                if LifeCycleOptions.uncertain_on_use in variable_life_cycle:
                    del_effect_list.append(
                        compilation.known(
                            compilation.constant_map[param_name],
                            compilation.constant_map[MemoryState.KNOWN.value],
                        )
                    )

                    add_effect_list.append(
                        compilation.known(
                            compilation.constant_map[param_name],
                            compilation.constant_map[MemoryState.UNCERTAIN.value],
                        )
                    )

            for constraint in o_input.constraints:
                constraint_predicate = compile_constraints(compilation, constraint, **kwargs)
                precondition_list.append(constraint_predicate)

        if NL2FlowOptions.label_production in optimization_options:
            label_level = compilation.lang.variable("l", compilation.type_map[TypeOptions.LABEL.value])
            parameter_list.append(label_level)

            precondition_list.extend(
                [
                    neg(label_level == compilation.constant_map[get_token_predicate_name(index=0, token="var")]),
                    compilation.available(label_level),
                ]
            )

            del_effect_list.append(compilation.available(label_level))
            add_effect_list.append(
                compilation.assigned_to(
                    compilation.constant_map[operator.name],
                    label_level,
                )
            )

        if optimization_options:
            add_advanced_properties(
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

                if NL2FlowOptions.label_production in optimization_options:
                    add_effect_list.append(
                        compilation.label_tag(
                            compilation.constant_map[param],
                            parameter_list[0],
                        ),
                    )

            for constraint in o_output.constraints:
                constraint_predicate = compile_constraints(compilation, constraint, **kwargs)
                add_effect_list.append(constraint_predicate)

        add_partial_orders(compilation, operator, precondition_list)
        merged_preconditions = merge_optional_preconditions(
            compilation,
            must_know_list,
            optional_know_list,
            precondition_list,
        )

        compilation.problem.action(
            operator.name,
            parameters=parameter_list,
            precondition=merged_preconditions,
            effects=[fs.AddEffect(add) for add in add_effect_list] + [fs.DelEffect(del_e) for del_e in del_effect_list],
            cost=iofs.AdditiveActionCost(
                compilation.problem.language.constant(operator.cost, compilation.problem.language.get_sort("Integer"))
            ),
        )


def merge_optional_preconditions(
    compilation: Any,
    must_know_list: List[str],
    optional_know_list: List[str],
    precondition_list: List[Any],
) -> CompoundFormula:
    must_know_predicates = [
        compilation.known(
            compilation.constant_map[item],
            compilation.constant_map[MemoryState.KNOWN.value],
        )
        for item in must_know_list
    ]

    precondition_list.extend(must_know_predicates)

    if optional_know_list:
        for item in optional_know_list:
            precondition_list.append(
                neg(
                    compilation.known(
                        compilation.constant_map[item],
                        compilation.constant_map[MemoryState.UNCERTAIN.value],
                    )
                )
            )

        optional_know_predicates = [
            compilation.known(
                compilation.constant_map[item],
                compilation.constant_map[MemoryState.KNOWN.value],
            )
            for item in optional_know_list
        ]

        if must_know_list:
            optional_or = lor(lor(*optional_know_predicates), land(*must_know_predicates))
        else:
            optional_or = lor(*optional_know_predicates)

        merged_preconditions = land(land(*precondition_list, flat=True), optional_or)

    else:
        merged_preconditions = land(*precondition_list)

    return merged_preconditions


def add_advanced_properties(
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
    local_parameters = (
        parameter_list if NL2FlowOptions.label_production not in optimization_options else parameter_list[:-1]
    )

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
                getattr(compilation, new_has_done_predicate_name)(*local_parameters, pre_level),
                neg(getattr(compilation, new_has_done_predicate_name)(*local_parameters, post_level)),
                compilation.connected(compilation.constant_map[operator.name], pre_level, post_level),
            ]
        )

        add_effect_list.append(getattr(compilation, new_has_done_predicate_name)(*local_parameters, post_level))

        for try_level in range(operator.max_try):
            compilation.init.add(
                compilation.connected(
                    compilation.constant_map[operator.name],
                    compilation.constant_map[f"try_level_{try_level}"],
                    compilation.constant_map[f"try_level_{try_level + 1}"],
                )
            )

        add_enabler_action_for_operator(compilation, operator, local_parameters, new_has_done_predicate_name)
        parameter_list.extend([pre_level, post_level])

    else:
        precondition_list.append(
            neg(getattr(compilation, new_has_done_predicate_name)(*local_parameters)),
        )

        add_effect_list.append(getattr(compilation, new_has_done_predicate_name)(*local_parameters))


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
