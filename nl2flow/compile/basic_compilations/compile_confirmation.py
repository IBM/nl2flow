import tarski.fstrips as fs
from tarski.io import fstrips as iofs
from tarski.syntax import land
from typing import Set, Any, Optional

from nl2flow.debug.schemas import SolutionQuality
from nl2flow.compile.options import (
    TypeOptions,
    LifeCycleOptions,
    BasicOperations,
    CostOptions,
    MemoryState,
)


def compile_confirmation(compilation: Any, **kwargs: Any) -> None:
    variable_life_cycle: Set[LifeCycleOptions] = set(kwargs["variable_life_cycle"])
    debug_flag: Optional[SolutionQuality] = kwargs.get("debug_flag", None)

    if variable_life_cycle:
        x = compilation.lang.variable("x", compilation.type_map[TypeOptions.ROOT.value])

        precondition_list = [compilation.known(x, compilation.constant_map[MemoryState.UNCERTAIN.value])]
        effect_list = [
            fs.AddEffect(compilation.known(x, compilation.constant_map[MemoryState.KNOWN.value])),
            fs.DelEffect(compilation.known(x, compilation.constant_map[MemoryState.UNCERTAIN.value])),
        ]

        if debug_flag:
            precondition_list.append(compilation.ready_for_token())
            effect_list.append(fs.DelEffect(compilation.ready_for_token()))

        compilation.problem.action(
            BasicOperations.CONFIRM.value,
            parameters=[x],
            precondition=land(*precondition_list, flat=True),
            effects=effect_list,
            cost=iofs.AdditiveActionCost(
                compilation.problem.language.constant(
                    CostOptions.UNIT.value,
                    compilation.problem.language.get_sort("Integer"),
                )
            ),
        )
