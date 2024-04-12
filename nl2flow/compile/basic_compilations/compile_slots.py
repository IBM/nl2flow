import tarski.fstrips as fs
from tarski.io import fstrips as iofs
from tarski.syntax import land, neg
from typing import List, Set, Dict, Any, Optional

from nl2flow.debug.schemas import SolutionQuality
from nl2flow.compile.basic_compilations.utils import (
    get_type_of_constant,
    is_this_a_datum,
    get_item_requirement_map,
    get_agent_to_slot_map,
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


def get_slots_as_not_last_resort(compilation: Any) -> List[str]:
    return list(
        map(
            lambda ns: str(ns.slot_name),
            filter(
                lambda sp: sp.do_not_last_resort,
                compilation.flow_definition.slot_properties,
            ),
        )
    )


def get_goodness_map(compilation: Any, no_edit: bool = False) -> Dict[str, float]:
    not_slotfillable_types = get_not_slotfillable_types(compilation)
    goodness_map = dict()

    for constant in compilation.constant_map:
        if is_this_a_datum(compilation, constant):
            type_of_datum = get_type_of_constant(compilation, constant)
            if type_of_datum in not_slotfillable_types and not no_edit:
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

            if not no_edit:
                compilation.init.set(
                    compilation.slot_goodness(compilation.constant_map[constant]),
                    int((2 - slot_goodness) * CostOptions.VERY_HIGH.value),
                )

    return goodness_map


def compile_higher_cost_slots(compilation: Any, **kwargs: Any) -> None:
    variable_life_cycle: Set[LifeCycleOptions] = set(kwargs["variable_life_cycle"])
    slot_options: Set[SlotOptions] = set(kwargs["slot_options"])
    debug_flag: Optional[SolutionQuality] = kwargs.get("debug_flag", None)

    if SlotOptions.ordered in slot_options:
        not_slots = get_not_slots(compilation)
        agent_to_slot_map = get_agent_to_slot_map(compilation)

        for operator in compilation.flow_definition.operators:
            slot_list = agent_to_slot_map[operator.name]

            for index, slot in enumerate(slot_list):
                if slot not in not_slots:
                    precondition_list = [
                        neg(
                            compilation.known(
                                compilation.constant_map[slot], compilation.constant_map[MemoryState.KNOWN.value]
                            )
                        ),
                        neg(compilation.not_slotfillable(compilation.constant_map[slot])),
                    ]

                    precondition_list.extend(
                        [
                            compilation.known(
                                compilation.constant_map[item], compilation.constant_map[MemoryState.KNOWN.value]
                            )
                            for item in slot_list[:index]
                        ]
                    )

                    del_effect_list = [
                        compilation.not_usable(compilation.constant_map[slot]),
                        compilation.mapped(compilation.constant_map[slot]),
                    ]

                    add_effect_list = [
                        compilation.free(compilation.constant_map[slot]),
                        compilation.mapped_to(compilation.constant_map[slot], compilation.constant_map[slot]),
                        compilation.known(
                            compilation.constant_map[slot],
                            compilation.constant_map[MemoryState.UNCERTAIN.value]
                            if LifeCycleOptions.confirm_on_slot in variable_life_cycle
                            else compilation.constant_map[MemoryState.KNOWN.value],
                        ),
                    ]

                    if debug_flag:
                        precondition_list.append(compilation.ready_for_token())
                        add_effect_list.append(compilation.has_asked(compilation.constant_map[slot]))
                        del_effect_list.append(compilation.ready_for_token())

                    compilation.problem.action(
                        f"{BasicOperations.SLOT_FILLER.value}--for-{operator.name}----{slot}",
                        parameters=[],
                        precondition=land(*precondition_list, flat=True),
                        effects=[fs.AddEffect(add_e) for add_e in add_effect_list]
                        + [fs.DelEffect(del_e) for del_e in del_effect_list],
                        cost=iofs.AdditiveActionCost(compilation.slot_goodness(compilation.constant_map[slot])),
                    )
    else:
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

        if debug_flag:
            precondition_list.append(compilation.ready_for_token())
            add_effect_list.append(compilation.has_asked(x))
            del_effect_list.append(compilation.ready_for_token())

        compilation.problem.action(
            BasicOperations.SLOT_FILLER.value,
            parameters=[x],
            precondition=land(*precondition_list, flat=True),
            effects=[fs.AddEffect(add_e) for add_e in add_effect_list]
            + [fs.DelEffect(del_e) for del_e in del_effect_list],
            cost=iofs.AdditiveActionCost(compilation.slot_goodness(x)),
        )


def compile_last_resort_slots(compilation: Any, **kwargs: Any) -> None:
    slot_options: Set[SlotOptions] = set(kwargs["slot_options"])
    variable_life_cycle: Set[LifeCycleOptions] = set(kwargs["variable_life_cycle"])
    debug_flag: Optional[SolutionQuality] = kwargs.get("debug_flag", None)

    not_slots = get_not_slots(compilation)
    source_map = get_item_source_map(compilation)
    requirement_map = get_item_requirement_map(compilation)
    agent_to_slot_map = get_agent_to_slot_map(compilation)
    goodness_map = get_goodness_map(compilation, no_edit=True)
    not_slots_as_last_resort = get_slots_as_not_last_resort(compilation)

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

            if SlotOptions.ordered in slot_options:
                for operator_name in requirement_map[constant]:
                    slot_list = agent_to_slot_map[operator_name]
                    index_of_current_slot = slot_list.index(constant)

                    extra_preconditions = [
                        compilation.known(
                            compilation.constant_map[s], compilation.constant_map[MemoryState.KNOWN.value]
                        )
                        for s in slot_list[:index_of_current_slot]
                    ]

                    if debug_flag:
                        precondition_list.append(compilation.ready_for_token())
                        add_effect_list.append(compilation.has_asked(compilation.constant_map[constant]))
                        del_effect_list.append(compilation.ready_for_token())

                    compilation.problem.action(
                        f"{BasicOperations.SLOT_FILLER.value}--last-resort--for-{operator_name}----{constant}",
                        parameters=[],
                        precondition=land(*precondition_list + extra_preconditions, flat=True),
                        effects=[fs.AddEffect(add_e) for add_e in add_effect_list]
                        + [fs.DelEffect(del_e) for del_e in del_effect_list],
                        cost=iofs.AdditiveActionCost(
                            compilation.problem.language.constant(
                                slot_cost,
                                compilation.problem.language.get_sort("Integer"),
                            )
                        ),
                    )
            else:
                if debug_flag:
                    precondition_list.append(compilation.ready_for_token())
                    add_effect_list.append(compilation.has_asked(compilation.constant_map[constant]))
                    del_effect_list.append(compilation.ready_for_token())

                compilation.problem.action(
                    f"{BasicOperations.SLOT_FILLER.value}--last-resort----{constant}",
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


def compile_all_together(compilation: Any, **kwargs: Any) -> None:
    slot_options: Set[SlotOptions] = set(kwargs["slot_options"])
    variable_life_cycle: Set[LifeCycleOptions] = set(kwargs["variable_life_cycle"])
    debug_flag: Optional[SolutionQuality] = kwargs.get("debug_flag", None)

    not_slots = get_not_slots(compilation)
    source_map = get_item_source_map(compilation)
    agent_to_slot_map = get_agent_to_slot_map(compilation)
    not_slots_as_last_resort = get_slots_as_not_last_resort(compilation)
    goodness_map = get_goodness_map(compilation, no_edit=True)

    for operator in compilation.flow_definition.operators:
        slot_list = agent_to_slot_map[operator.name]

        if len(slot_list) > 0:
            precondition_list = []
            add_effect_list = []
            del_effect_list = []
            params = []
            slot_cost = 0

            for constant in slot_list:
                if constant not in not_slots:
                    params.append(constant)
                    precondition_list.append(
                        neg(
                            compilation.known(
                                compilation.constant_map[constant],
                                compilation.constant_map[MemoryState.KNOWN.value],
                            )
                        ),
                    )

                    del_effect_list.extend(
                        [
                            compilation.not_usable(compilation.constant_map[constant]),
                            compilation.mapped(compilation.constant_map[constant]),
                        ]
                    )

                    add_effect_list.extend(
                        [
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
                    )

                    if debug_flag:
                        add_effect_list.append(compilation.has_asked(compilation.constant_map[constant]))

                    if SlotOptions.last_resort in slot_options and constant not in not_slots_as_last_resort:
                        for reference_operator in source_map[constant]:
                            precondition_list.append(
                                compilation.has_done(
                                    compilation.constant_map[reference_operator],
                                    compilation.constant_map[HasDoneState.past.value],
                                )
                            )

                    slot_cost += int((2 - goodness_map[constant]) * CostOptions.INTERMEDIATE.value)

            if debug_flag:
                precondition_list.append(compilation.ready_for_token())
                del_effect_list.append(compilation.ready_for_token())

            compilation.problem.action(
                f"{BasicOperations.SLOT_FILLER.value}--for-{operator.name}----{'----'.join(params)}",
                parameters=[],
                precondition=land(*precondition_list, flat=True),
                effects=[fs.AddEffect(add_e) for add_e in add_effect_list]
                + [fs.DelEffect(del_e) for del_e in del_effect_list],
                cost=iofs.AdditiveActionCost(
                    compilation.problem.language.constant(
                        slot_cost,
                        compilation.problem.language.get_sort("Integer"),
                    )
                ),
            )
