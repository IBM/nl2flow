from nl2flow.compile.basic_compilations.utils import add_memory_item_to_constant_map
from nl2flow.compile.schemas import Parameter, MemoryItem, Constraint, Step
from nl2flow.compile.options import MemoryState, HasDoneState, TypeOptions, BasicOperations, NL2FlowOptions
from nl2flow.compile.basic_compilations.utils import is_this_a_datum
from nl2flow.debug.schemas import SolutionQuality
from typing import Any, Optional, Set


def get_predicate_from_constraint(compilation: Any, constraint: Constraint) -> Optional[Any]:
    try:
        new_constraint_variable = f"status_{constraint.constraint}"
        constraint_parameters = constraint.get_variable_references_from_constraint(
            constraint.constraint, compilation.cached_transforms
        )

        set_variables = list()
        for item in constraint_parameters:
            if item not in compilation.constant_map and is_this_a_datum(compilation, item):
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

    except Exception as e:
        print(f"Error generating constraint predicate: {e}")
        return None


def get_predicate_from_step(compilation: Any, step: Step, index: int = 0, **kwargs: Any) -> Optional[Any]:
    optimization_options: Set[NL2FlowOptions] = set(kwargs["optimization_options"])
    debug_flag: Optional[SolutionQuality] = kwargs.get("debug_flag", None)

    mapped_items = kwargs.get("mapped_items", dict())
    step.parameters = [
        Parameter(item_id=mapped_items.get(p.item_id, p.item_id), item_type=p.item_type) for p in step.parameters
    ]

    try:
        if step.name.startswith(BasicOperations.SLOT_FILLER.value):
            step_predicate = compilation.has_asked(compilation.constant_map[step.parameters[0].item_id])
            return step_predicate

        elif step.name.startswith(BasicOperations.MAPPER.value):
            step_predicate = compilation.mapped_to(
                compilation.constant_map[step.parameters[0].item_id],
                compilation.constant_map[step.parameters[1].item_id],
            )
            return step_predicate

        elif step.name.startswith(BasicOperations.CONFIRM.value):
            step_predicate = compilation.known(
                compilation.constant_map[step.parameters[0].item_id],
                compilation.constant_map[MemoryState.KNOWN.value],
            )
            return step_predicate

        else:
            step_predicate = compilation.has_done(
                compilation.constant_map[step.name],
                compilation.constant_map[HasDoneState.present.value]
                if debug_flag
                else compilation.constant_map[HasDoneState.past.value],
            )

            if not debug_flag:
                compilation.init.add(step_predicate)

            has_done_predicate_name = f"has_done_{step.name}"
            parameter_names = (
                [p.item_id if isinstance(p, Parameter) else p for p in step.parameters]
                if NL2FlowOptions.multi_instance in optimization_options
                else []
            )

            if NL2FlowOptions.allow_retries in optimization_options:
                num_try = index + 1
                parameter_names.append(f"try_level_{num_try}")

            step_predicate_parameterized = (
                None
                if not parameter_names
                else getattr(compilation, has_done_predicate_name)(
                    *[compilation.constant_map[p] for p in parameter_names]
                )
            )

            return step_predicate if step_predicate_parameterized is None else step_predicate_parameterized

    except Exception as e:
        print(f"Error generating step predicate: {e}")
        return None


def compile_history(compilation: Any, **kwargs: Any) -> None:
    for index, step in enumerate(compilation.flow_definition.history):
        indices_of_interest = [i for i, h in enumerate(compilation.flow_definition.history) if h.name == step.name]

        index_of_operation = indices_of_interest.index(index)
        step_predicate = get_predicate_from_step(compilation, step, index_of_operation, **kwargs)

        if step_predicate:
            compilation.init.add(step_predicate)

    for constraint in compilation.flow_definition.constraints:
        constraint_predicate = get_predicate_from_constraint(compilation, constraint)
        if constraint_predicate:
            compilation.init.add(constraint_predicate)
