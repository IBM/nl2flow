from nl2flow.compile.basic_compilations.utils import add_memory_item_to_constant_map
from nl2flow.compile.schemas import Parameter, MemoryItem, Constraint, Step
from nl2flow.compile.options import MemoryState, HasDoneState, TypeOptions, BasicOperations, LifeCycleOptions
from typing import Any, Set


def get_predicate_from_constraint(compilation: Any, constraint: Constraint) -> Any:
    new_constraint_variable = f"status_{constraint.constraint}"
    constraint_parameters = constraint.get_variable_references_from_constraint(
        constraint.constraint, compilation.cached_transforms
    )

    set_variables = list()
    for item in constraint_parameters:
        if item not in compilation.constant_map:
            add_memory_item_to_constant_map(
                compilation,
                MemoryItem(item_id=item, item_type=TypeOptions.ROOT.value),
            )
        set_variables.append(compilation.constant_map[item])

    constraint_predicate = getattr(compilation, new_constraint_variable)(
        *set_variables,
        compilation.constant_map[str(constraint.truth_value)],
    )

    return constraint_predicate


def get_predicate_from_step(
    compilation: Any, step: Step, variable_life_cycle: Set[LifeCycleOptions], num_try: int = 0
) -> Any:
    if step.name.startswith(BasicOperations.SLOT_FILLER.value):
        step_predicate = compilation.known(
            compilation.constant_map[step.parameters[0].item_id],
            compilation.constant_map[MemoryState.UNCERTAIN.value]
            if LifeCycleOptions.confirm_on_slot in variable_life_cycle
            else compilation.constant_map[MemoryState.KNOWN.value],
        )

    elif step.name.startswith(BasicOperations.MAPPER.value):
        step_predicate = compilation.mapped_to(
            compilation.constant_map[step.parameters[0].item_id],
            compilation.constant_map[step.parameters[1].item_id],
        )

    elif step.name.startswith(BasicOperations.CONFIRM.value):
        step_predicate = compilation.known(
            compilation.constant_map[step.parameters[0].item_id],
            compilation.constant_map[MemoryState.KNOWN.value],
        )

    else:
        has_done_predicate_name = f"has_done_{step.name}"
        parameter_names = [p.item_id if isinstance(p, Parameter) else p for p in step.parameters]
        parameter_names.append(f"try_level_{num_try}")

        step_predicate = getattr(compilation, has_done_predicate_name)(
            *[compilation.constant_map[p] for p in parameter_names]
        )

    return step_predicate


def compile_history(compilation: Any, **kwargs: Any) -> None:
    multi_instance: bool = kwargs.get("multi_instance", True)
    variable_life_cycle: Set[LifeCycleOptions] = set(kwargs["variable_life_cycle"])

    for index, step in enumerate(compilation.flow_definition.history):
        step_predicate = compilation.has_done(
            compilation.constant_map[step.name],
            compilation.constant_map[HasDoneState.past.value],
        )
        compilation.init.add(step_predicate)

        if multi_instance:
            indices_of_interest = [i for i, h in enumerate(compilation.flow_definition.history) if h.name == step.name]
            num_try = indices_of_interest.index(index) + 1

            parameterized_step_predicate = get_predicate_from_step(compilation, step, variable_life_cycle, num_try)
            compilation.init.add(parameterized_step_predicate)

    for constraint in compilation.flow_definition.constraints:
        constraint_predicate = get_predicate_from_constraint(compilation, constraint)
        compilation.init.add(constraint_predicate)
