from nl2flow.compile.schemas import (
    FlowDefinition,
    PDDL,
    GoalItem,
    GoalItems,
    Constraint,
    OperatorDefinition,
    Transform,
)
from nl2flow.compile.options import (
    TypeOptions,
    GoalType,
    SlotOptions,
    BasicOperations,
    CostOptions,
)
from abc import ABC, abstractmethod
from typing import List, Set, Dict, Any

import tarski
import tarski.fstrips as fs
from tarski.theories import Theory
from tarski.io import fstrips as iofs
from tarski.io import FstripsWriter
from tarski.syntax import land, neg


class Compilation(ABC):
    def __init__(self, flow_definition: FlowDefinition):
        self.flow_definition = flow_definition

    @abstractmethod
    def compile(self, **kwargs: Dict[str, Any]) -> PDDL:
        pass


class ClassicPDDL(Compilation):
    def __init__(self, flow_definition: FlowDefinition):
        Compilation.__init__(self, flow_definition)

        self.cached_transforms: List[Transform] = list()
        self.flow_definition = FlowDefinition.transform(
            self.flow_definition, self.cached_transforms
        )

        name = self.flow_definition.name
        lang = fs.language(name, theories=[Theory.EQUALITY, Theory.ARITHMETIC])

        self.lang = lang
        self.cost = self.lang.function("total-cost", self.lang.Real)

        self.problem = fs.create_fstrips_problem(
            domain_name=f"{name}-domain",
            problem_name=f"{name}-problem",
            language=self.lang,
        )
        self.problem.metric(self.cost(), fs.OptimizationType.MINIMIZE)

        # noinspection PyUnresolvedReferences
        self.init = tarski.model.create(self.lang)

        self.has_done: Any = None
        self.known: Any = None

        self.type_map: Dict[str, Any] = dict()
        self.constant_map: Dict[str, Any] = dict()

    def __compile_goals(self, list_of_goal_items: List[GoalItems]) -> Set[Any]:
        goal_predicates = set()

        for goal_items in list_of_goal_items:
            goals = goal_items.goals

            if not isinstance(goals, List):
                goals = [goals]

            for goal in goals:

                if isinstance(goal, GoalItem):

                    if goal.goal_type == GoalType.OPERATOR:
                        goal_predicates.add(
                            self.has_done(self.constant_map[goal.goal_name])
                        )

                elif isinstance(goal, Constraint):
                    pass

                else:
                    raise TypeError("Unrecognized goal type.")

        return goal_predicates

    def __compile_actions(self, list_of_actions: List[OperatorDefinition]) -> None:

        for operator in list_of_actions:
            self.constant_map[operator.name] = self.lang.constant(
                operator.name, TypeOptions.AGENT.value
            )

            precondition_list = list()
            add_effect_list = [self.has_done(self.constant_map[operator.name])]

            for o_input in operator.inputs:
                for param in o_input.parameters:

                    if isinstance(param, str):

                        if param not in self.constant_map:
                            self.constant_map[param] = self.lang.constant(
                                param, TypeOptions.ROOT.value
                            )

                        precondition_list.append(self.known(self.constant_map[param]))

            outputs = operator.outputs[0]
            for o_output in outputs.outcomes:
                for param in o_output.parameters:

                    if isinstance(param, str):

                        if param not in self.constant_map:
                            self.constant_map[param] = self.lang.constant(
                                param, TypeOptions.ROOT.value
                            )

                        add_effect_list.append(self.known(self.constant_map[param]))

            self.problem.action(
                operator.name,
                parameters=list(),
                precondition=land(*precondition_list),
                effects=[fs.AddEffect(add) for add in add_effect_list],
                cost=iofs.AdditiveActionCost(
                    self.problem.language.constant(
                        operator.cost, self.problem.language.get_sort("Integer")
                    )
                ),
            )

    def compile(self, **kwargs: Dict[str, Any]) -> PDDL:

        self.type_map[TypeOptions.ROOT.value] = self.lang.sort(TypeOptions.ROOT.value)
        self.type_map[TypeOptions.AGENT.value] = self.lang.sort(TypeOptions.AGENT.value)

        self.has_done = self.lang.predicate(
            "has_done", self.type_map[TypeOptions.AGENT.value]
        )
        self.known = self.lang.predicate("known", self.type_map[TypeOptions.ROOT.value])

        for type_item in self.flow_definition.type_hierarchy:
            self.type_map[type_item.name] = self.lang.sort(
                type_item.name, type_item.parent
            )

        for memory_item in self.flow_definition.memory_items:
            self.constant_map[memory_item.item_id] = self.lang.constant(
                memory_item.item_id,
                memory_item.item_type
                if memory_item.item_type
                else TypeOptions.ROOT.value,
            )

        self.__compile_actions(self.flow_definition.operators)
        slot_options: Set[SlotOptions] = set(kwargs["slot_options"])
        if SlotOptions.higher_cost in slot_options:

            x = self.lang.variable("x", self.type_map[TypeOptions.ROOT.value])

            precondition_list = [neg(self.known(x))]
            add_effect_list = [self.known(x)]

            self.problem.action(
                BasicOperations.SLOT_FILLER.value,
                parameters=[x],
                precondition=land(*precondition_list),
                effects=[fs.AddEffect(add) for add in add_effect_list],
                cost=iofs.AdditiveActionCost(
                    self.problem.language.constant(
                        CostOptions.VERY_HIGH.value,
                        self.problem.language.get_sort("Integer"),
                    )
                ),
            )

        self.init.set(self.cost(), 0)
        self.problem.init = self.init

        goal_set = self.__compile_goals(self.flow_definition.goal_items)
        self.problem.goal = land(*goal_set, flat=True)

        writer = FstripsWriter(self.problem)
        domain = writer.print_domain().replace(" :numeric-fluents", "")
        problem = writer.print_instance()

        return PDDL(domain=domain, problem=problem)
