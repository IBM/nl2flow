import tarski.fstrips as fs
from tarski.io import fstrips as iofs
from typing import Set, Any

from nl2flow.compile.options import (
    TypeOptions,
    LifeCycleOptions,
    BasicOperations,
    CostOptions,
    MemoryState,
)


def compile_confirmation(compilation: Any, **kwargs: Any) -> None:
    variable_life_cycle: Set[LifeCycleOptions] = set(kwargs["variable_life_cycle"])

    if variable_life_cycle:
        x = compilation.lang.variable("x", compilation.type_map[TypeOptions.ROOT.value])

        compilation.problem.action(
            BasicOperations.CONFIRM.value,
            parameters=[x],
            precondition=compilation.known(x, compilation.constant_map[MemoryState.UNCERTAIN.value]),
            effects=[
                fs.AddEffect(compilation.known(x, compilation.constant_map[MemoryState.KNOWN.value])),
                fs.DelEffect(compilation.known(x, compilation.constant_map[MemoryState.UNCERTAIN.value])),
            ],
            cost=iofs.AdditiveActionCost(
                compilation.problem.language.constant(
                    CostOptions.UNIT.value,
                    compilation.problem.language.get_sort("Integer"),
                )
            ),
        )
