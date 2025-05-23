import tarski.fstrips as fs

from tarski.io import fstrips as iofs
from tarski.syntax import land, neg
from typing import Set, Any, Optional
from copy import deepcopy

from nl2flow.debug.schemas import DebugFlag
from nl2flow.compile.schemas import FlowDefinition, MemoryItem
from nl2flow.compile.basic_compilations.utils import is_this_a_datum, add_memory_item_to_constant_map
from nl2flow.compile.basic_compilations.compile_references.utils import get_token_predicate_name
from nl2flow.compile.options import (
    TypeOptions,
    LifeCycleOptions,
    NL2FlowOptions,
    MappingOptions,
    BasicOperations,
    CostOptions,
    MemoryState,
)


def compile_declared_mappings(compilation: Any, **kwargs: Any) -> None:
    flow_definition: FlowDefinition = compilation.flow_definition
    mapping_options: Set[MappingOptions] = set(kwargs["mapping_options"])
    variable_life_cycle: Set[LifeCycleOptions] = set(kwargs["variable_life_cycle"])
    optimization_options: Set[NL2FlowOptions] = set(kwargs["optimization_options"])
    debug_flag: Optional[DebugFlag] = kwargs.get("debug_flag", None)

    for constant in compilation.constant_map:
        if is_this_a_datum(compilation, constant) and MappingOptions.prohibit_direct not in mapping_options:
            compilation.init.add(
                compilation.mapped_to(
                    compilation.constant_map[constant],
                    compilation.constant_map[constant],
                )
            )

    if len(flow_definition.list_of_mappings) > 0:
        for mappable_item in flow_definition.list_of_mappings:
            for item in [mappable_item.source_name, mappable_item.target_name]:
                if item not in compilation.constant_map:
                    add_memory_item_to_constant_map(
                        compilation,
                        memory_item=MemoryItem(
                            item_id=item, item_type=TypeOptions.ROOT.value, item_state=MemoryState.UNKNOWN.value
                        ),
                    )

            source = compilation.constant_map[mappable_item.source_name]
            target = compilation.constant_map[mappable_item.target_name]

            if not mappable_item.probability:
                compilation.init.add(compilation.not_mappable(source, target))
            else:
                compilation.init.add(compilation.is_mappable(source, target))
                compilation.init.set(
                    compilation.map_affinity(source, target),
                    int((2 - mappable_item.probability) * CostOptions.EDIT.value),
                )

            if MappingOptions.transitive in mapping_options:
                if not mappable_item.probability:
                    compilation.init.add(compilation.not_mappable(target, source))

                else:
                    compilation.init.add(compilation.is_mappable(target, source))
                    compilation.init.set(
                        compilation.map_affinity(target, source),
                        int((2 - mappable_item.probability) * CostOptions.EDIT.value),
                    )

        x = compilation.lang.variable("x", compilation.type_map[TypeOptions.ROOT.value])
        y = compilation.lang.variable("y", compilation.type_map[TypeOptions.ROOT.value])

        parameter_list = [x, y]

        precondition_list = [
            compilation.known(x, compilation.constant_map[MemoryState.KNOWN.value]),
            compilation.is_mappable(x, y),
            neg(compilation.not_mappable(x, y)),
            neg(compilation.new_item(y)),
        ]

        effect_list = [
            fs.AddEffect(
                compilation.known(
                    y,
                    compilation.constant_map[MemoryState.UNCERTAIN.value]
                    if LifeCycleOptions.confirm_on_mapping in variable_life_cycle
                    else compilation.constant_map[MemoryState.KNOWN.value],
                )
            ),
            fs.AddEffect(compilation.mapped_to(x, y)),
            fs.AddEffect(compilation.mapped(x)),
            fs.DelEffect(compilation.been_used(y)),
            fs.DelEffect(compilation.not_usable(y)),
        ]

        if debug_flag == DebugFlag.TOKENIZE:
            precondition_list.append(compilation.ready_for_token())
            effect_list.append(fs.DelEffect(compilation.ready_for_token()))

        if NL2FlowOptions.label_production in optimization_options:
            label_param = compilation.lang.variable("l", compilation.type_map[TypeOptions.LABEL.value])
            token_name = get_token_predicate_name(index=0, token="var")

            parameter_list.append(label_param)

            precondition_list.append(compilation.label_tag(x, label_param))
            effect_list.append(fs.AddEffect(compilation.label_tag(y, label_param)))

            tmp_precondition_list = deepcopy(precondition_list)
            tmp_effect_list = deepcopy(effect_list)

            tmp_precondition_list.append(label_param == compilation.constant_map[token_name])

            compilation.problem.action(
                f"{BasicOperations.MAPPER.value}--{token_name}",
                parameters=parameter_list,
                precondition=land(*tmp_precondition_list, flat=True),
                effects=tmp_effect_list,
                cost=iofs.AdditiveActionCost(compilation.map_affinity(x, y)),
            )

            precondition_list.append(neg(label_param == compilation.constant_map[token_name]))
            effect_list.append(fs.DelEffect(compilation.label_tag(x, label_param)))

        else:
            compilation.problem.action(
                f"{BasicOperations.MAPPER.value}--free-alt",
                parameters=parameter_list,
                precondition=land(*precondition_list, compilation.free(x), flat=True),
                effects=effect_list + [fs.AddEffect(compilation.free(y))],
                cost=iofs.AdditiveActionCost(
                    compilation.problem.language.constant(
                        CostOptions.INTERMEDIATE.value,
                        compilation.problem.language.get_sort("Integer"),
                    )
                ),
            )

        compilation.problem.action(
            BasicOperations.MAPPER.value,
            parameters=parameter_list,
            precondition=land(*precondition_list, flat=True),
            effects=effect_list,
            cost=iofs.AdditiveActionCost(compilation.map_affinity(x, y)),
        )


def compile_typed_mappings(compilation: Any, **kwargs: Any) -> None:
    variable_life_cycle: Set[LifeCycleOptions] = set(kwargs["variable_life_cycle"])
    optimization_options: Set[NL2FlowOptions] = set(kwargs["optimization_options"])
    debug_flag: Optional[DebugFlag] = kwargs.get("debug_flag", None)

    for typing in compilation.type_map:
        if typing not in [t.value for t in TypeOptions]:
            x = compilation.lang.variable("x", compilation.type_map[typing])
            y = compilation.lang.variable("y", compilation.type_map[typing])

            parameter_list = [x, y]

            precondition_list = [
                compilation.known(x, compilation.constant_map[MemoryState.KNOWN.value]),
                neg(compilation.mapped(x)),
                neg(compilation.not_mappable(x, y)),
                neg(compilation.new_item(y)),
                compilation.been_used(y),
            ]

            effect_list = [
                fs.AddEffect(
                    compilation.known(
                        y,
                        compilation.constant_map[MemoryState.UNCERTAIN.value]
                        if LifeCycleOptions.confirm_on_mapping in variable_life_cycle
                        else compilation.constant_map[MemoryState.KNOWN.value],
                    )
                ),
                fs.AddEffect(compilation.mapped_to(x, y)),
                fs.AddEffect(compilation.mapped(x)),
                fs.DelEffect(compilation.been_used(y)),
                fs.DelEffect(compilation.not_usable(y)),
            ]

            compilation.problem.action(
                f"{BasicOperations.MAPPER.value}--{typing}-free-alt",
                parameters=parameter_list,
                precondition=land(*precondition_list, compilation.free(x), flat=True),
                effects=effect_list + [fs.AddEffect(compilation.free(y))],
                cost=iofs.AdditiveActionCost(
                    compilation.problem.language.constant(
                        CostOptions.INTERMEDIATE.value,
                        compilation.problem.language.get_sort("Integer"),
                    )
                ),
            )

            if debug_flag == DebugFlag.TOKENIZE:
                precondition_list.append(compilation.ready_for_token())
                effect_list.append(fs.DelEffect(compilation.ready_for_token()))

            if NL2FlowOptions.label_production in optimization_options:
                label_param = compilation.lang.variable("l", compilation.type_map[TypeOptions.LABEL.value])
                parameter_list.append(label_param)

                precondition_list.append(compilation.label_tag(x, label_param))
                effect_list.append(fs.AddEffect(compilation.label_tag(y, label_param)))

            compilation.problem.action(
                f"{BasicOperations.MAPPER.value}--{typing}",
                parameters=parameter_list,
                precondition=land(*precondition_list, flat=True),
                effects=effect_list,
                cost=iofs.AdditiveActionCost(
                    compilation.problem.language.constant(
                        CostOptions.VERY_LOW.value,
                        compilation.problem.language.get_sort("Integer"),
                    )
                ),
            )
