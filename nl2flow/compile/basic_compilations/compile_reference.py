# import tarski.fstrips as fs
# from tarski.io import fstrips as iofs
# from tarski.syntax import land
from typing import Any

# from nl2flow.compile.basic_compilations.compile_history import get_predicate_from_constraint, get_predicate_from_step


# from nl2flow.compile.schemas import Step, Constraint
#
# from nl2flow.compile.options import (
#     TypeOptions,
#     LifeCycleOptions,
#     BasicOperations,
#     CostOptions,
#     MemoryState,
# )


def compile_reference(compilation: Any, **kwargs: Any) -> None:
    _ = kwargs
    compilation.init.add(compilation.ready_for_token())
    # for index, item in enumerate(compilation.flow_definition.reference):
    #     if isinstance(item, Step):
    #         indices_of_interest = [i for i, r in enumerate(compilation.flow_definition.reference) if item.name == r.name]
    #         index_of_operation = indices_of_interest.index(index) + 1
    #
    #         basic_operations = [
    #             BasicOperations.SLOT_FILLER.value,
    #             BasicOperations.MAPPER.value,
    #             BasicOperations.CONFIRM.value,
    #         ]
    #
    #         if any([item.name.startswith(b_op) for b_op in basic_operations]):
    #             token_predicate = f"token_{item.name} {item.parameters}"
    #         else:
    #             token_predicate = f"token_{item.name}_{index_of_operation}_{}"
    #
    #         pass
    #     elif isinstance(item, Constraint):
    #         pass
    #     else:
    #         raise ValueError(f"Invalid reference object: {item}")

    # x = compilation.lang.variable("x", compilation.type_map[TypeOptions.ROOT.value])
    #
    # precondition_list = [compilation.known(x, compilation.constant_map[MemoryState.UNCERTAIN.value])]
    # effect_list = [
    #     fs.AddEffect(compilation.known(x, compilation.constant_map[MemoryState.KNOWN.value])),
    #     fs.DelEffect(compilation.known(x, compilation.constant_map[MemoryState.UNCERTAIN.value])),
    # ]
    #
    # if debug_flag:
    #     precondition_list.append(compilation.ready_for_token())
    #     effect_list.append(fs.DelEffect(compilation.ready_for_token()))
    #
    # compilation.problem.action(
    #     BasicOperations.CONFIRM.value,
    #     parameters=[x],
    #     precondition=land(*precondition_list, flat=True),
    #     effects=effect_list,
    #     cost=iofs.AdditiveActionCost(
    #         compilation.problem.language.constant(
    #             CostOptions.UNIT.value,
    #             compilation.problem.language.get_sort("Integer"),
    #         )
    #     ),
    # )
