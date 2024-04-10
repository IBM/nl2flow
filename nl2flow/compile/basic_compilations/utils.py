from typing import List, Set, Dict, Union, Any
from nl2flow.compile.options import TypeOptions, MAX_RETRY, LOOKAHEAD
from nl2flow.compile.schemas import MemoryItem, TypeItem, SlotProperty, Parameter, SignatureItem


def unpack_list_of_signature_items(signature_items: List[SignatureItem]) -> List[str]:
    items = list()

    for signature_item in signature_items:
        params = signature_item.parameters

        if isinstance(params, List):
            items.extend([p if isinstance(p, str) else p.item_id for p in params])
        else:
            items.append(params if isinstance(params, str) else params.item_id)

    return items


def get_agent_to_slot_map(compilation: Any) -> Dict[str, List[str]]:
    agent_to_slot_map: Dict[str, List[str]] = dict()

    for operator in compilation.flow_definition.operators:
        agent_to_slot_map[operator.name] = unpack_list_of_signature_items(operator.inputs)

    return agent_to_slot_map


def get_item_requirement_map(compilation: Any) -> Dict[str, Set[str]]:
    requirement_map: Dict[str, Set[str]] = dict()
    agent_to_slot_map = get_agent_to_slot_map(compilation)

    for constant in compilation.constant_map:
        requirement_map[constant] = set()

        for operator in compilation.flow_definition.operators:
            if constant in agent_to_slot_map[operator.name]:
                requirement_map[constant].add(operator.name)

    return requirement_map


def get_item_source_map(compilation: Any) -> Dict[str, Set[str]]:
    source_map: Dict[str, Set[str]] = dict()

    for constant in compilation.constant_map:
        source_map[constant] = set()

        for operator in compilation.flow_definition.operators:
            outputs = operator.outputs[0]
            params = unpack_list_of_signature_items(outputs.outcomes)

            if constant in params:
                source_map[constant].add(operator.name)

    return source_map


def get_type_of_constant(compilation: Any, constant: str) -> str:
    for item in compilation.constant_map:
        if item == constant:
            constant_type: str = compilation.constant_map[item].sort.name
            return constant_type

    raise ValueError(f"Unknown constant: {constant}")


def is_this_a_datum_type(type_name: str) -> bool:
    return type_name not in [
        TypeOptions.MEMORY.value,
        TypeOptions.OPERATOR.value,
        TypeOptions.HAS_DONE.value,
        TypeOptions.RETRY.value,
        TypeOptions.STATUS.value,
    ]


def is_this_a_datum(compilation: Any, constant: str) -> bool:
    type_name = get_type_of_constant(compilation, constant)
    return is_this_a_datum_type(type_name)


def add_retry_states(compilation: Any) -> None:
    for item in range(MAX_RETRY + 2):
        add_memory_item_to_constant_map(
            compilation,
            MemoryItem(item_id=f"try_level_{item}", item_type=TypeOptions.RETRY.value),
        )


def generate_new_objects(type_name: str, num_lookahead: int) -> List[str]:
    return [f"new_object_{type_name}_{index}" for index in range(num_lookahead)]


def add_extra_objects(compilation: Any, **kwargs: Any) -> None:
    num_lookahead: int = kwargs.get("lookahead", LOOKAHEAD)  # type: ignore

    for type_name in compilation.type_map:
        if is_this_a_datum_type(type_name):
            new_objects = generate_new_objects(type_name, num_lookahead)

            for new_object in new_objects:
                add_memory_item_to_constant_map(compilation, MemoryItem(item_id=new_object, item_type=type_name))
                compilation.init.add(compilation.new_item(compilation.constant_map[new_object]))

                if type_name != TypeOptions.ROOT.value:
                    temp_slot_properties = compilation.flow_definition.slot_properties

                    for slot in temp_slot_properties:
                        if (
                            slot.propagate_desirability
                            and get_type_of_constant(compilation, slot.slot_name) == type_name
                        ):
                            compilation.flow_definition.slot_properties.append(
                                SlotProperty(
                                    slot_name=new_object,
                                    slot_desirability=slot.slot_desirability,
                                )
                            )


def add_type_item_to_type_map(compilation: Any, type_item: TypeItem) -> None:
    if type_item.parent and type_item.parent not in compilation.type_map:
        compilation.type_map[type_item.parent] = compilation.lang.sort(type_item.parent, TypeOptions.ROOT.value)

    if type_item.name not in compilation.type_map:
        if type_item.parent:
            compilation.type_map[type_item.name] = compilation.lang.sort(type_item.name, type_item.parent)

        else:
            compilation.type_map[type_item.name] = compilation.lang.sort(type_item.name)


def add_memory_item_to_constant_map(compilation: Any, memory_item: Parameter) -> None:
    type_name: str = memory_item.item_type if memory_item.item_type else TypeOptions.ROOT.value

    add_type_item_to_type_map(compilation, TypeItem(name=type_name, parent=TypeOptions.ROOT.value))

    if memory_item.item_id not in compilation.constant_map:
        compilation.constant_map[memory_item.item_id] = compilation.lang.constant(memory_item.item_id, type_name)


def add_to_condition_list_pre_check(compilation: Any, parameter: Union[str, Parameter]) -> None:
    if isinstance(parameter, str):
        add_memory_item_to_constant_map(compilation, MemoryItem(item_id=parameter, item_type=TypeOptions.ROOT.value))

    elif isinstance(parameter, Parameter):
        add_memory_item_to_constant_map(compilation, parameter)
    else:
        raise TypeError(f"This is not a valid parameter: {parameter}")
