from nl2flow.compile.basic_compilations.utils import add_to_condition_list_pre_check
from nl2flow.compile.schemas import Parameter, Constraint, Step, FlowDefinition
from nl2flow.compile.options import MemoryState, HasDoneState, BasicOperations, NL2FlowOptions
from nl2flow.compile.basic_compilations.utils import is_this_a_datum
from nl2flow.compile.basic_compilations.compile_references.utils import get_token_predicate_name
from nl2flow.debug.schemas import DebugFlag
from typing import Any, Optional, Set, List


def get_predicate_from_constraint(compilation: Any, constraint: Constraint) -> Optional[Any]:
    try:
        new_constraint_variable = f"status_{constraint.constraint}"
        constraint_parameters = constraint.get_variable_references_from_constraint(
            constraint.constraint, compilation.cached_transforms
        )

        set_variables = list()
        for item in constraint_parameters:
            if item not in compilation.constant_map and is_this_a_datum(compilation, item):
                add_to_condition_list_pre_check(compilation, item)

            set_variables.append(compilation.constant_map[item])

        constraint_predicate = getattr(compilation, new_constraint_variable)(
            *set_variables,
            compilation.constant_map[str(constraint.truth_value)],
        )

        return constraint_predicate

    except Exception as e:
        print(f"Error generating constraint predicate: {e}")
        return None


def get_predicate_from_step(compilation: Any, step: Step, repeat_index: int = 0, **kwargs: Any) -> Optional[Any]:
    optimization_options: Set[NL2FlowOptions] = set(kwargs["optimization_options"])
    debug_flag: Optional[DebugFlag] = kwargs.get("debug_flag", None)

    try:
        if step.name.startswith(BasicOperations.SLOT_FILLER.value):
            step_predicate = compilation.has_asked(compilation.constant_map[step.parameter(0)])
            return step_predicate

        elif step.name.startswith(BasicOperations.MAPPER.value):
            step_predicate = compilation.mapped_to(
                compilation.constant_map[step.parameter(0)],
                compilation.constant_map[step.parameter(1)],
            )
            return step_predicate

        elif step.name.startswith(BasicOperations.CONFIRM.value):
            step_predicate = compilation.known(
                compilation.constant_map[step.parameter(0)],
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
                num_try = repeat_index + 1
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


def compile_history(compilation: Any, **kwargs: Any) -> List[str]:
    used_up_labels: List[str] = []

    for index, step in enumerate(compilation.flow_definition.history):
        indices_of_interest = [i for i, h in enumerate(compilation.flow_definition.history) if h.name == step.name]

        index_of_operation = indices_of_interest.index(index)
        step_predicate = get_predicate_from_step(compilation, step, index_of_operation, **kwargs)

        if step.label and step.label != get_token_predicate_name(index=0, token="var"):
            used_up_labels.append(step.label)

        if step_predicate:
            compilation.init.add(step_predicate)

    for constraint in compilation.flow_definition.constraints:
        constraint_predicate = get_predicate_from_constraint(compilation, constraint)
        if constraint_predicate:
            compilation.init.add(constraint_predicate)

    return used_up_labels


def get_index_of_interest(compilation: Any, step: Step, flow_definition: FlowDefinition, current_index: int) -> int:
    indices_of_interest = []

    history = flow_definition.history
    cached_history_length = len(history)

    reference = compilation.flow_definition.reference.plan or []
    current_index += cached_history_length

    new_history = history + reference

    for i, r in enumerate(new_history):
        if i == current_index:
            indices_of_interest.append(i)

        if isinstance(r, Step) and step.name == r.name:
            indices_of_interest.append(i)

    return indices_of_interest.index(current_index) if current_index in indices_of_interest else 0
