import tarski
import tarski.fstrips as fs
from tarski.theories import Theory
from tarski.io import fstrips as iofs
from tarski.io import FstripsWriter
from tarski.syntax import land, neg

from abc import ABC, abstractmethod
from typing import List, Set, Dict, Any, Tuple, Union

from nl2flow.compile.schemas import (
    FlowDefinition,
    PDDL,
    GoalItem,
    GoalItems,
    Constraint,
    OperatorDefinition,
    Transform,
    MemoryItem,
    TypeItem,
    SlotProperty,
)

from nl2flow.compile.options import (
    SLOT_GOODNESS,
    LOOKAHEAD,
    TypeOptions,
    GoalType,
    SlotOptions,
    LifeCycleOptions,
    MappingOptions,
    BasicOperations,
    CostOptions,
    MemoryState,
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
        self.mapped: Any = None
        self.not_slotfillable: Any = None
        self.is_mappable: Any = None
        self.map_affinity: Any = None
        self.slot_goodness: Any = None

        self.type_map: Dict[str, Any] = dict()
        self.constant_map: Dict[str, Any] = dict()

    def __compile_slots(
        self,
        flow_definition: FlowDefinition,
        slot_options: Set[SlotOptions],
        variable_life_cycle: Set[LifeCycleOptions],
    ) -> None:

        for slot_item in flow_definition.slot_properties:
            if not slot_item.slot_desirability:
                self.init.add(
                    self.not_slotfillable(self.constant_map[slot_item.slot_name])
                )

        goodness_map: Dict[str, float] = dict()
        for constant in self.constant_map:
            if self.__is_this_a_datum(constant):
                slot_goodness = SLOT_GOODNESS

                for slot in self.flow_definition.slot_properties:
                    if slot.slot_name == constant:
                        slot_goodness = slot.slot_desirability
                        break

                goodness_map[constant] = slot_goodness
                self.init.set(
                    self.slot_goodness(self.constant_map[constant]),
                    int((2 - slot_goodness) * CostOptions.VERY_HIGH.value),
                )

        if variable_life_cycle:
            x = self.lang.variable("x", self.type_map[TypeOptions.ROOT.value])

            self.problem.action(
                BasicOperations.CONFIRM.value,
                parameters=[x],
                precondition=self.known(
                    x, self.constant_map[MemoryState.UNCERTAIN.value]
                ),
                effects=[
                    fs.AddEffect(
                        self.known(x, self.constant_map[MemoryState.KNOWN.value])
                    )
                ],
                cost=iofs.AdditiveActionCost(
                    self.problem.language.constant(
                        CostOptions.UNIT.value,
                        self.problem.language.get_sort("Integer"),
                    )
                ),
            )

        if SlotOptions.higher_cost in slot_options:
            x = self.lang.variable("x", self.type_map[TypeOptions.ROOT.value])

            precondition_list = [
                neg(self.known(x, self.constant_map[MemoryState.KNOWN.value])),
                neg(self.not_slotfillable(x)),
            ]

            add_effect_list = [
                self.known(
                    x,
                    self.constant_map[MemoryState.UNCERTAIN.value]
                    if LifeCycleOptions.confirm_on_slot in variable_life_cycle
                    else self.constant_map[MemoryState.KNOWN.value],
                )
            ]

            self.problem.action(
                BasicOperations.SLOT_FILLER.value,
                parameters=[x],
                precondition=land(*precondition_list),
                effects=[fs.AddEffect(add) for add in add_effect_list],
                cost=iofs.AdditiveActionCost(self.slot_goodness(x)),
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
                if constant not in not_slots and self.__is_this_a_datum(constant):

                    precondition_list = [
                        neg(
                            self.known(
                                self.constant_map[constant],
                                self.constant_map[MemoryState.KNOWN.value],
                            )
                        )
                    ]

                    add_effect_list = [
                        self.known(
                            self.constant_map[constant],
                            self.constant_map[MemoryState.UNCERTAIN.value]
                            if LifeCycleOptions.confirm_on_slot in variable_life_cycle
                            else self.constant_map[MemoryState.KNOWN.value],
                        )
                    ]

                    for operator in source_map[constant]:
                        precondition_list.append(
                            self.has_done(self.constant_map[operator])
                        )

                    slot_cost = int(
                        (2 - goodness_map[constant]) * CostOptions.INTERMEDIATE.value
                    )

                    self.problem.action(
                        f"{BasicOperations.SLOT_FILLER.value}----{constant}",
                        parameters=[],
                        precondition=land(*precondition_list),
                        effects=[fs.AddEffect(add) for add in add_effect_list],
                        cost=iofs.AdditiveActionCost(
                            self.problem.language.constant(
                                slot_cost,
                                self.problem.language.get_sort("Integer"),
                            )
                        ),
                    )

    def __compile_mappings(
        self,
        flow_definition: FlowDefinition,
        mapping_options: Set[MappingOptions],
        variable_life_cycle: Set[LifeCycleOptions],
    ) -> None:

        for constant in self.constant_map:
            if self.__is_this_a_datum(constant):
                self.init.add(
                    self.mapped(
                        self.constant_map[constant], self.constant_map[constant]
                    )
                )

        for mappable_item in flow_definition.list_of_mappings:
            source = self.constant_map[mappable_item.source_name]
            target = self.constant_map[mappable_item.target_name]

            self.init.add(self.is_mappable(source, target))
            self.init.set(
                self.map_affinity(source, target),
                int((2 - mappable_item.probability) * CostOptions.LOW.value),
            )

            if MappingOptions.transitive in mapping_options:
                self.init.add(self.is_mappable(target, source))
                self.init.set(
                    self.map_affinity(target, source),
                    int((2 - mappable_item.probability) * CostOptions.UNIT.value),
                )

        x = self.lang.variable("x", self.type_map[TypeOptions.ROOT.value])
        y = self.lang.variable("y", self.type_map[TypeOptions.ROOT.value])

        precondition_list = [
            self.known(x, self.constant_map[MemoryState.KNOWN.value]),
            neg(self.known(y, self.constant_map[MemoryState.KNOWN.value])),
            self.is_mappable(x, y),
        ]
        self.problem.action(
            BasicOperations.MAPPER.value,
            parameters=[x, y],
            precondition=land(*precondition_list),
            effects=[
                fs.AddEffect(
                    self.known(
                        y,
                        self.constant_map[MemoryState.UNCERTAIN.value]
                        if LifeCycleOptions.confirm_on_mapping in variable_life_cycle
                        else self.constant_map[MemoryState.KNOWN.value],
                    )
                ),
                fs.AddEffect(self.mapped(x, y)),
            ],
            cost=iofs.AdditiveActionCost(self.map_affinity(x, y)),
        )

        for typing in self.type_map:
            if typing not in [t.value for t in TypeOptions]:
                x = self.lang.variable("x", self.type_map[typing])
                y = self.lang.variable("y", self.type_map[typing])

                self.problem.action(
                    f"{BasicOperations.MAPPER.value}----{typing}",
                    parameters=[x, y],
                    precondition=land(
                        *[
                            self.known(x, self.constant_map[MemoryState.KNOWN.value]),
                            neg(
                                self.known(
                                    y, self.constant_map[MemoryState.KNOWN.value]
                                )
                            ),
                        ]
                    ),
                    effects=[
                        fs.AddEffect(
                            self.known(
                                y,
                                self.constant_map[MemoryState.UNCERTAIN.value]
                                if LifeCycleOptions.confirm_on_mapping
                                in variable_life_cycle
                                else self.constant_map[MemoryState.KNOWN.value],
                            )
                        ),
                        fs.AddEffect(self.mapped(x, y)),
                    ],
                    cost=iofs.AdditiveActionCost(
                        self.problem.language.constant(
                            CostOptions.UNIT.value,
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

    def __compile_actions(
        self,
        list_of_actions: List[OperatorDefinition],
        variable_life_cycle: Set[LifeCycleOptions],
        multi_instance: bool = True,
    ) -> None:
        def __add_to_condition_list_pre_check(
            parameter: Union[str, MemoryItem]
        ) -> None:
            if isinstance(parameter, str):
                self.__add_memory_item_to_constant_map(
                    MemoryItem(item_id=parameter, item_type=TypeOptions.ROOT.value)
                )

            elif isinstance(parameter, MemoryItem):
                self.__add_memory_item_to_constant_map(parameter)
            else:
                raise TypeError

        for operator in list_of_actions:

            self.constant_map[operator.name] = self.lang.constant(
                operator.name, TypeOptions.OPERATOR.value
            )

            parameter_list: List[Any] = list()
            precondition_list: List[Any] = list()
            add_effect_list = [self.has_done(self.constant_map[operator.name])]
            type_list = list()

            for o_input in operator.inputs:
                for param in o_input.parameters:
                    __add_to_condition_list_pre_check(param)
                    index_of_param = list(o_input.parameters).index(param)

                    if isinstance(param, MemoryItem):
                        type_of_param = param.item_type or TypeOptions.ROOT.value
                        param = param.item_id
                    else:
                        type_of_param = self.__get_type_of_constant(param)

                    x = self.lang.variable(
                        f"x{index_of_param}", self.type_map[type_of_param]
                    )

                    parameter_list.append(x)
                    type_list.append(type_of_param)

                    precondition_list.append(self.mapped(x, self.constant_map[param]))
                    precondition_list.append(
                        self.known(
                            self.constant_map[param],
                            self.constant_map[MemoryState.KNOWN.value],
                        )
                    )

                    if LifeCycleOptions.uncertain_on_use in variable_life_cycle:
                        add_effect_list.append(
                            self.known(
                                self.constant_map[param],
                                self.constant_map[MemoryState.UNCERTAIN.value],
                            )
                        )

            outputs = operator.outputs[0]
            for o_output in outputs.outcomes:
                for param in o_output.parameters:
                    __add_to_condition_list_pre_check(param)

                    if isinstance(param, MemoryItem):
                        param = param.item_id

                    add_effect_list.append(
                        self.known(
                            self.constant_map[param],
                            self.constant_map[MemoryState.UNCERTAIN.value]
                            if LifeCycleOptions.confirm_on_determination
                            in variable_life_cycle
                            else self.constant_map[MemoryState.KNOWN.value],
                        )
                    )

            if multi_instance:
                new_has_done_predicate_name = f"has_done_{operator.name}"
                new_has_done_predicate = self.lang.predicate(
                    new_has_done_predicate_name,
                    *[self.type_map[type_name] for type_name in type_list],
                )

                setattr(self, new_has_done_predicate_name, new_has_done_predicate)
                add_effect_list.append(
                    getattr(self, new_has_done_predicate_name)(*parameter_list)
                )
                precondition_list.append(
                    neg(getattr(self, new_has_done_predicate_name)(*parameter_list))
                )

            else:
                precondition_list.append(
                    neg(self.has_done(self.constant_map[operator.name]))
                )

            self.problem.action(
                operator.name,
                parameters=parameter_list,
                precondition=land(*precondition_list),
                effects=[fs.AddEffect(add) for add in add_effect_list],
                cost=iofs.AdditiveActionCost(
                    self.problem.language.constant(
                        operator.cost, self.problem.language.get_sort("Integer")
                    )
                ),
            )

    def __get_type_of_constant(self, constant: str) -> str:
        constant_type: str = TypeOptions.ROOT.value

        for item in self.constant_map:
            if item == constant:
                constant_type = self.constant_map[item].sort.name
                break

        return constant_type

    def __is_this_a_datum(self, constant: str) -> bool:
        return constant not in [
            o.name for o in self.flow_definition.operators
        ] and constant not in [m.value for m in MemoryState]

    def __add_extra_objects(self, num_lookahead: int) -> None:
        for type_name in self.type_map:
            if type_name not in [TypeOptions.MEMORY.value, TypeOptions.OPERATOR.value]:
                new_objects = [
                    f"new_object_{type_name}_{index}" for index in range(num_lookahead)
                ]

                for new_object in new_objects:
                    self.__add_memory_item_to_constant_map(
                        MemoryItem(item_id=new_object, item_type=type_name)
                    )

                    if type_name != TypeOptions.ROOT.value:
                        temp_slot_properties = self.flow_definition.slot_properties

                        for slot in temp_slot_properties:
                            if (
                                slot.propagate_desirability
                                and self.__get_type_of_constant(slot.slot_name)
                                == type_name
                            ):
                                self.flow_definition.slot_properties.append(
                                    SlotProperty(
                                        slot_name=new_object,
                                        slot_desirability=slot.slot_desirability,
                                    )
                                )

    def __add_type_item_to_type_map(self, type_item: TypeItem) -> None:
        if type_item.parent not in self.type_map:
            self.type_map[type_item.parent] = self.lang.sort(
                type_item.parent, TypeOptions.ROOT.value
            )

        if type_item.name not in self.type_map:
            self.type_map[type_item.name] = self.lang.sort(
                type_item.name, type_item.parent
            )

    def __add_memory_item_to_constant_map(self, memory_item: MemoryItem) -> None:
        type_name: str = (
            memory_item.item_type if memory_item.item_type else TypeOptions.ROOT.value
        )

        self.__add_type_item_to_type_map(
            TypeItem(name=type_name, parent=TypeOptions.ROOT.value)
        )

        if memory_item.item_id not in self.constant_map:
            self.constant_map[memory_item.item_id] = self.lang.constant(
                memory_item.item_id, type_name
            )

    def compile(self, **kwargs: Dict[str, Any]) -> Tuple[PDDL, List[Transform]]:

        self.type_map[TypeOptions.ROOT.value] = self.lang.sort(TypeOptions.ROOT.value)
        self.type_map[TypeOptions.OPERATOR.value] = self.lang.sort(
            TypeOptions.OPERATOR.value
        )

        self.type_map[TypeOptions.MEMORY.value] = self.lang.sort(
            TypeOptions.MEMORY.value
        )

        for memory_state in MemoryState:
            self.constant_map[memory_state.value] = self.lang.constant(
                memory_state.value, TypeOptions.MEMORY.value
            )

        self.has_done = self.lang.predicate(
            "has_done", self.type_map[TypeOptions.OPERATOR.value]
        )

        self.known = self.lang.predicate(
            "known",
            self.type_map[TypeOptions.ROOT.value],
            self.type_map[TypeOptions.MEMORY.value],
        )

        self.not_slotfillable = self.lang.predicate(
            "not_slotfillable", self.type_map[TypeOptions.ROOT.value]
        )

        self.slot_goodness = self.lang.function(
            "slot_goodness",
            self.type_map[TypeOptions.ROOT.value],
            self.lang.Real,
        )

        self.is_mappable = self.lang.predicate(
            "is_mappable",
            self.type_map[TypeOptions.ROOT.value],
            self.type_map[TypeOptions.ROOT.value],
        )

        self.mapped = self.lang.predicate(
            "mapped",
            self.type_map[TypeOptions.ROOT.value],
            self.type_map[TypeOptions.ROOT.value],
        )

        self.map_affinity = self.lang.function(
            "affinity",
            self.type_map[TypeOptions.ROOT.value],
            self.type_map[TypeOptions.ROOT.value],
            self.lang.Real,
        )

        for type_item in self.flow_definition.type_hierarchy:
            self.__add_type_item_to_type_map(type_item)

        for memory_item in self.flow_definition.memory_items:
            self.__add_memory_item_to_constant_map(memory_item)

        multi_instance_option: bool = kwargs.get("multi_instance", True)  # type: ignore
        variable_life_cycle: Set[LifeCycleOptions] = set(kwargs["variable_life_cycle"])
        self.__compile_actions(
            self.flow_definition.operators,
            variable_life_cycle,
            multi_instance=multi_instance_option,
        )

        self.__compile_goals(self.flow_definition.goal_items)

        lookahead_option: int = kwargs.get("lookahead", LOOKAHEAD)  # type: ignore
        self.__add_extra_objects(num_lookahead=lookahead_option)

        slot_options: Set[SlotOptions] = set(kwargs["slot_options"])
        self.__compile_slots(self.flow_definition, slot_options, variable_life_cycle)

        mapping_options: Set[MappingOptions] = set(kwargs["mapping_options"])
        self.__compile_mappings(
            self.flow_definition, mapping_options, variable_life_cycle
        )

        self.init.set(self.cost(), 0)
        self.problem.init = self.init

        writer = FstripsWriter(self.problem)
        domain = writer.print_domain().replace(" :numeric-fluents", "")
        problem = writer.print_instance()

        return PDDL(domain=domain, problem=problem), self.cached_transforms
