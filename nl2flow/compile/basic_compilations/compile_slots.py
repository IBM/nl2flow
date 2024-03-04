import tarski.fstrips as fs
from tarski.io import fstrips as iofs
from tarski.syntax import land, neg
from typing import List, Set, Dict, Any

from nl2flow.compile.schemas import FlowDefinition
from nl2flow.compile.basic_compilations.utils import (
    get_type_of_constant,
    is_this_a_datum,
    # get_agent_to_slot_map,
    # get_item_requirement_map,
    get_item_source_map,
    generate_new_objects,
)

from nl2flow.compile.options import (
    SLOT_GOODNESS,
    LOOKAHEAD,
    SlotOptions,
    TypeOptions,
    LifeCycleOptions,
    BasicOperations,
    CostOptions,
    MemoryState,
    HasDoneState,
)


def get_not_slots(compilation: Any) -> List[str]:
    return list(
        map(
            lambda ns: str(ns.slot_name),
            filter(
                lambda sp: not sp.slot_desirability,
                compilation.flow_definition.slot_properties,
            ),
        )
    )


def get_not_slotfillable_types(compilation: Any) -> List[str]:
    not_slotfillable_types = list()

    for slot_item in compilation.flow_definition.slot_properties:
        if not slot_item.slot_desirability:
            compilation.init.add(compilation.not_slotfillable(compilation.constant_map[slot_item.slot_name]))

            if slot_item.propagate_desirability:
                not_slotfillable_types.append(get_type_of_constant(compilation, slot_item.slot_name))

    return not_slotfillable_types


def get_goodness_map(compilation: Any) -> Dict[str, float]:
    not_slotfillable_types = get_not_slotfillable_types(compilation)
    goodness_map = dict()

    for constant in compilation.constant_map:
        if is_this_a_datum(compilation, constant):
            type_of_datum = get_type_of_constant(compilation, constant)
            if type_of_datum in not_slotfillable_types:
                compilation.init.add(compilation.not_slotfillable(compilation.constant_map[constant]))

            slot_goodness = SLOT_GOODNESS
            for slot in compilation.flow_definition.slot_properties:
                if type_of_datum == get_type_of_constant(compilation, slot.slot_name) and slot.propagate_desirability:
                    slot_goodness = slot.slot_desirability
                    break

                if slot.slot_name == constant:
                    slot_goodness = slot.slot_desirability
                    break

            goodness_map[constant] = slot_goodness
            compilation.init.set(
                compilation.slot_goodness(compilation.constant_map[constant]),
                int((2 - slot_goodness) * CostOptions.VERY_HIGH.value),
            )

    return goodness_map


def compile_higher_cost_slots(compilation: Any, **kwargs: Any) -> None:
    variable_life_cycle: Set[LifeCycleOptions] = set(kwargs["variable_life_cycle"])
    slot_options: Set[SlotOptions] = set(kwargs["slot_options"])

    if SlotOptions.last_resort not in slot_options:
        _ = get_goodness_map(compilation)

    x = compilation.lang.variable("x", compilation.type_map[TypeOptions.ROOT.value])

    precondition_list = [
        neg(compilation.known(x, compilation.constant_map[MemoryState.KNOWN.value])),
        neg(compilation.not_slotfillable(x)),
    ]

    del_effect_list = [
        compilation.not_usable(x),
        compilation.mapped(x),
    ]

    add_effect_list = [
        compilation.free(x),
        compilation.mapped_to(x, x),
        compilation.known(
            x,
            compilation.constant_map[MemoryState.UNCERTAIN.value]
            if LifeCycleOptions.confirm_on_slot in variable_life_cycle
            else compilation.constant_map[MemoryState.KNOWN.value],
        ),
    ]

    if SlotOptions.ordered not in slot_options:
        compilation.problem.action(
            BasicOperations.SLOT_FILLER.value,
            parameters=[x],
            precondition=land(*precondition_list, flat=True),
            effects=[fs.AddEffect(add_e) for add_e in add_effect_list]
            + [fs.DelEffect(del_e) for del_e in del_effect_list],
            cost=iofs.AdditiveActionCost(compilation.slot_goodness(x)),
        )

    else:
        # for constant in compilation.constant_map:
        #     if constant not in not_slots and is_this_a_datum(compilation, constant):
        pass

    if SlotOptions.last_resort not in slot_options:
        compile_new_object_maps(compilation, **kwargs)


def compile_last_resort_slots(compilation: Any, **kwargs: Any) -> None:
    variable_life_cycle: Set[LifeCycleOptions] = set(kwargs["variable_life_cycle"])
    flow_definition: FlowDefinition = compilation.flow_definition

    not_slots = get_not_slots(compilation)
    source_map = get_item_source_map(compilation)
    goodness_map = get_goodness_map(compilation)

    not_slots_as_last_resort = list(
        map(
            lambda ns: str(ns.slot_name),
            filter(
                lambda sp: sp.do_not_last_resort,
                flow_definition.slot_properties,
            ),
        )
    )

    for constant in compilation.constant_map:
        if constant not in not_slots and is_this_a_datum(compilation, constant):
            precondition_list = [
                neg(
                    compilation.known(
                        compilation.constant_map[constant],
                        compilation.constant_map[MemoryState.KNOWN.value],
                    )
                ),
            ]

            del_effect_list = [
                compilation.not_usable(compilation.constant_map[constant]),
                compilation.mapped(compilation.constant_map[constant]),
            ]

            add_effect_list = [
                compilation.free(compilation.constant_map[constant]),
                compilation.mapped_to(
                    compilation.constant_map[constant],
                    compilation.constant_map[constant],
                ),
                compilation.known(
                    compilation.constant_map[constant],
                    compilation.constant_map[MemoryState.UNCERTAIN.value]
                    if LifeCycleOptions.confirm_on_slot in variable_life_cycle
                    else compilation.constant_map[MemoryState.KNOWN.value],
                ),
            ]

            if constant not in not_slots_as_last_resort:
                for operator in source_map[constant]:
                    precondition_list.append(
                        compilation.has_done(
                            compilation.constant_map[operator],
                            compilation.constant_map[HasDoneState.past.value],
                        )
                    )

            slot_cost = int((2 - goodness_map[constant]) * CostOptions.INTERMEDIATE.value)

            compilation.problem.action(
                f"{BasicOperations.SLOT_FILLER.value}----{constant}",
                parameters=[],
                precondition=land(*precondition_list, flat=True),
                effects=[fs.AddEffect(add) for add in add_effect_list]
                + [fs.DelEffect(del_e) for del_e in del_effect_list],
                cost=iofs.AdditiveActionCost(
                    compilation.problem.language.constant(
                        slot_cost,
                        compilation.problem.language.get_sort("Integer"),
                    )
                ),
            )

    compile_new_object_maps(compilation, **kwargs)


def compile_new_object_maps(
    compilation: Any,
    **kwargs: Any,
) -> None:
    num_lookahead: int = kwargs.get("lookahead", LOOKAHEAD)

    not_slotfillable_types = get_not_slotfillable_types(compilation)
    not_slots = get_not_slots(compilation)

    for constant in compilation.constant_map:
        type_of_datum = get_type_of_constant(compilation, constant)
        if constant in not_slots or type_of_datum in not_slotfillable_types:
            new_object_names = generate_new_objects(type_of_datum, num_lookahead)

            for new_object in new_object_names:
                compilation.init.add(
                    compilation.not_mappable(
                        compilation.constant_map[new_object],
                        compilation.constant_map[constant],
                    )
                )
