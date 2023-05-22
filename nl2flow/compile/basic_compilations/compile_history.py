from nl2flow.compile.schemas import FlowDefinition, Parameter
from nl2flow.compile.options import HasDoneState
from typing import Dict, Any


def compile_history(compilation: Any, **kwargs: Dict[str, Any]) -> None:
    multi_instance: bool = kwargs.get("multi_instance", True)  # type: ignore
    flow_definition: FlowDefinition = compilation.flow_definition

    for idx, history_item in enumerate(flow_definition.history):
        operator_name = history_item.name
        compilation.init.add(
            compilation.has_done(
                compilation.constant_map[operator_name],
                compilation.constant_map[HasDoneState.past.value],
            )
        )

        if multi_instance:
            indices_of_interest = [
                index
                for index, item in enumerate(flow_definition.history)
                if item.name == operator_name
            ]
            num_try = indices_of_interest.index(idx) + 1

            has_done_predicate_name = f"has_done_{operator_name}"
            parameter_names = [
                p.item_id if isinstance(p, Parameter) else p
                for p in history_item.parameters
            ]
            parameter_names.append(f"try_level_{num_try}")

            compilation.init.add(
                getattr(compilation, has_done_predicate_name)(
                    *[compilation.constant_map[p] for p in parameter_names]
                )
            )
