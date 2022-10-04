import tarski
import tarski.fstrips as fs
from tarski.theories import Theory
from tarski.io import fstrips as iofs
from tarski.io import FstripsWriter
from tarski.syntax import land, neg

from abc import ABC, abstractmethod
from typing import List, Set, Dict, Any, Tuple

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
        self.not_slotfillable: Any = None

        self.type_map: Dict[str, Any] = dict()
        self.constant_map: Dict[str, Any] = dict()

    def __compile_slots(
        self, flow_definition: FlowDefinition, slot_options: Set[SlotOptions]
    ) -> None:

        self.not_slotfillable = self.lang.predicate(
            "not_slotfillable", self.type_map[TypeOptions.ROOT.value]
        )

        for slot_item in flow_definition.slot_properties:
            if not slot_item.slot_desirability:
                self.init.add(
                    self.not_slotfillable(self.constant_map[slot_item.slot_name])
                )

        if SlotOptions.higher_cost in slot_options:

            x = self.lang.variable("x", self.type_map[TypeOptions.ROOT.value])

            precondition_list = [neg(self.known(x)), neg(self.not_slotfillable(x))]
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

        if SlotOptions.last_resort in slot_options:
            source_map: Dict[str, List[str]] = dict()

            for constant in self.constant_map:
                source_map[constant] = list()

                for operator in self.flow_definition.operators:
                    outputs = operator.outputs[0]
                    for o_output in outputs.outcomes:
                        params = [
                            p if isinstance(p, str) else p.item_id
                            for p in o_output.parameters
                        ]

                        if constant in params:
                            source_map[constant].append(operator.name)

            not_slots = list(
                map(
                    lambda ns: str(ns.slot_name),
                    filter(
                        lambda sp: not sp.slot_desirability,
                        flow_definition.slot_properties,
                    ),
                )
            )

            for constant in self.constant_map:
                if constant not in not_slots and constant not in [
                    o.name for o in self.flow_definition.operators
                ]:

                    precondition_list = [neg(self.known(self.constant_map[constant]))]
                    add_effect_list = [self.known(self.constant_map[constant])]

                    for operator in source_map[constant]:
                        precondition_list.append(
                            self.has_done(self.constant_map[operator])
                        )

                    self.problem.action(
                        f"{BasicOperations.SLOT_FILLER.value}--slot--{constant}",
                        parameters=[],
                        precondition=land(*precondition_list),
                        effects=[fs.AddEffect(add) for add in add_effect_list],
                        cost=iofs.AdditiveActionCost(
                            self.problem.language.constant(
                                CostOptions.INTERMEDIATE.value,
                                self.problem.language.get_sort("Integer"),
                            )
                        ),
                    )

    def __compile_goals(self, list_of_goal_items: List[GoalItems]) -> None:
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

        self.problem.goal = land(*goal_predicates, flat=True)

    def __compile_actions(self, list_of_actions: List[OperatorDefinition]) -> None:

        for operator in list_of_actions:
            self.constant_map[operator.name] = self.lang.constant(
                operator.name, TypeOptions.OPERATOR.value
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

    def compile(self, **kwargs: Dict[str, Any]) -> Tuple[PDDL, List[Transform]]:

        self.type_map[TypeOptions.ROOT.value] = self.lang.sort(TypeOptions.ROOT.value)
        self.type_map[TypeOptions.OPERATOR.value] = self.lang.sort(
            TypeOptions.OPERATOR.value
        )

        self.has_done = self.lang.predicate(
            "has_done", self.type_map[TypeOptions.OPERATOR.value]
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
        self.__compile_slots(self.flow_definition, slot_options)

        self.init.set(self.cost(), 0)
        self.problem.init = self.init
        self.__compile_goals(self.flow_definition.goal_items)

        writer = FstripsWriter(self.problem)
        domain = writer.print_domain().replace(" :numeric-fluents", "")
        problem = writer.print_instance()

        return PDDL(domain=domain, problem=problem), self.cached_transforms
