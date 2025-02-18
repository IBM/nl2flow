import tarski.fstrips as fs
from tarski.io import fstrips as iofs
from tarski.syntax import land, neg
from typing import Any
from nl2flow.compile.options import TypeOptions, CostOptions, RestrictedOperations


def compile_label_maker(compilation: Any) -> None:
    x = compilation.lang.variable("x", compilation.type_map[TypeOptions.LABEL.value])
    y = compilation.lang.variable("y", compilation.type_map[TypeOptions.LABEL.value])

    precondition_list = [
        compilation.available(x),
        neg(compilation.available(y)),
        compilation.label_ladder(x, y),
    ]

    effect_list = [
        fs.AddEffect(compilation.available(y)),
    ]

    compilation.problem.action(
        RestrictedOperations.LABEL_MAKER.value,
        parameters=[x, y],
        precondition=land(*precondition_list, flat=True),
        effects=effect_list,
        cost=iofs.AdditiveActionCost(
            compilation.problem.language.constant(
                CostOptions.ZERO.value,
                compilation.problem.language.get_sort("Integer"),
            )
        ),
    )
