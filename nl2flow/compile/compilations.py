import copy
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

from nl2flow.plan.schemas import Step, Parameter
from nl2flow.compile.options import (
    MAX_RETRY,
    SLOT_GOODNESS,
    LOOKAHEAD,
    TypeOptions,
    GoalType,
    GoalOptions,
    SlotOptions,
    LifeCycleOptions,
    MappingOptions,
    BasicOperations,
    RestrictedOperations,
    CostOptions,
    MemoryState,
    ConstraintState,
    HasDoneState,
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
        self.free: Any = None
        self.been_used: Any = None
        self.not_usable: Any = None
        self.new_item: Any = None
        self.known: Any = None
        self.mapped: Any = None
        self.mapped_to: Any = None
        self.not_slotfillable: Any = None
        self.is_mappable: Any = None
        self.not_mappable: Any = None
        self.map_affinity: Any = None
        self.slot_goodness: Any = None
        self.connected: Any = None
        self.done_goal_pre: Any = None
        self.done_goal_post: Any = None

        self.type_map: Dict[str, Any] = dict()
        self.constant_map: Dict[str, Any] = dict()

    def __compile_confirmation(
        self,
        variable_life_cycle: Set[LifeCycleOptions],
    ) -> None:

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
                    ),
                    fs.DelEffect(
                        self.known(x, self.constant_map[MemoryState.UNCERTAIN.value])
                    ),
                ],
                cost=iofs.AdditiveActionCost(
                    self.problem.language.constant(
                        CostOptions.UNIT.value,
                        self.problem.language.get_sort("Integer"),
                    )
                ),
            )

    def __compile_slots(
        self,
        flow_definition: FlowDefinition,
        slot_options: Set[SlotOptions],
        variable_life_cycle: Set[LifeCycleOptions],
        num_lookahead: int = LOOKAHEAD,
    ) -> None:

        not_slotfillable_types = list()
        propagate_types = list()

        for slot_item in flow_definition.slot_properties:
            if not slot_item.slot_desirability:
                self.init.add(
                    self.not_slotfillable(self.constant_map[slot_item.slot_name])
                )

                if slot_item.propagate_desirability:
                    not_slotfillable_types.append(
                        self.__get_type_of_constant(slot_item.slot_name)
                    )

            else:

                if slot_item.propagate_desirability:
                    propagate_types.append(
                        self.__get_type_of_constant(slot_item.slot_name)
                    )

        goodness_map: Dict[str, float] = dict()
        for constant in self.constant_map:
            if self.__is_this_a_datum(constant):

                type_of_datum = self.__get_type_of_constant(constant)
                if type_of_datum in not_slotfillable_types:
                    self.init.add(self.not_slotfillable(self.constant_map[constant]))

                slot_goodness = SLOT_GOODNESS

                for slot in self.flow_definition.slot_properties:
                    if (
                        type_of_datum == self.__get_type_of_constant(slot.slot_name)
                        and slot.propagate_desirability
                    ):
                        slot_goodness = slot.slot_desirability
                        break

                    if slot.slot_name == constant:
                        slot_goodness = slot.slot_desirability
                        break

                goodness_map[constant] = slot_goodness
                self.init.set(
                    self.slot_goodness(self.constant_map[constant]),
                    int((2 - slot_goodness) * CostOptions.VERY_HIGH.value),
                )

        if SlotOptions.higher_cost in slot_options:
            x = self.lang.variable("x", self.type_map[TypeOptions.ROOT.value])

            precondition_list = [
                neg(self.known(x, self.constant_map[MemoryState.KNOWN.value])),
                neg(self.not_slotfillable(x)),
            ]

            del_effect_list = [
                self.not_usable(x),
                self.mapped(x),
            ]
            add_effect_list = [
                self.free(x),
                self.mapped_to(x, x),
                self.known(
                    x,
                    self.constant_map[MemoryState.UNCERTAIN.value]
                    if LifeCycleOptions.confirm_on_slot in variable_life_cycle
                    else self.constant_map[MemoryState.KNOWN.value],
                ),
            ]

            self.problem.action(
                BasicOperations.SLOT_FILLER.value,
                parameters=[x],
                precondition=land(*precondition_list, flat=True),
                effects=[fs.AddEffect(add) for add in add_effect_list]
                + [fs.DelEffect(dele) for dele in del_effect_list],
                cost=iofs.AdditiveActionCost(self.slot_goodness(x)),
            )

        not_slots = list(
            map(
                lambda ns: str(ns.slot_name),
                filter(
                    lambda sp: not sp.slot_desirability,
                    flow_definition.slot_properties,
                ),
            )
        )

        if SlotOptions.last_resort in slot_options:
            source_map = self.__get_source_map()

            not_slots_as_last_resort = list(
                map(
                    lambda ns: str(ns.slot_name),
                    filter(
                        lambda sp: sp.do_not_last_resort,
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
                        ),
                    ]

                    del_effect_list = [
                        self.not_usable(self.constant_map[constant]),
                        self.mapped(self.constant_map[constant]),
                    ]
                    add_effect_list = [
                        self.free(self.constant_map[constant]),
                        self.mapped_to(
                            self.constant_map[constant], self.constant_map[constant]
                        ),
                        self.known(
                            self.constant_map[constant],
                            self.constant_map[MemoryState.UNCERTAIN.value]
                            if LifeCycleOptions.confirm_on_slot in variable_life_cycle
                            else self.constant_map[MemoryState.KNOWN.value],
                        ),
                    ]

                    if constant not in not_slots_as_last_resort:
                        for operator in source_map[constant]:
                            precondition_list.append(
                                self.has_done(
                                    self.constant_map[operator],
                                    self.constant_map[HasDoneState.past.value],
                                )
                            )

                    slot_cost = int(
                        (2 - goodness_map[constant]) * CostOptions.INTERMEDIATE.value
                    )

                    self.problem.action(
                        f"{BasicOperations.SLOT_FILLER.value}----{constant}",
                        parameters=[],
                        precondition=land(*precondition_list, flat=True),
                        effects=[fs.AddEffect(add) for add in add_effect_list]
                        + [fs.DelEffect(dele) for dele in del_effect_list],
                        cost=iofs.AdditiveActionCost(
                            self.problem.language.constant(
                                slot_cost,
                                self.problem.language.get_sort("Integer"),
                            )
                        ),
                    )

        self.__compile_new_object_maps(not_slots, not_slotfillable_types, num_lookahead)

    def __compile_new_object_maps(
        self,
        not_slots: List[str],
        not_slotfillable_types: List[str],
        num_lookahead: int,
    ) -> None:
        for constant in self.constant_map:
            type_of_datum = self.__get_type_of_constant(constant)
            if constant in not_slots or type_of_datum in not_slotfillable_types:
                new_object_names = self.__generate_new_objects(
                    type_of_datum, num_lookahead
                )

                for new_object in new_object_names:
                    self.init.add(
                        self.not_mappable(
                            self.constant_map[new_object], self.constant_map[constant]
                        )
                    )

    def __compile_mappings(
        self,
        flow_definition: FlowDefinition,
        mapping_options: Set[MappingOptions],
        variable_life_cycle: Set[LifeCycleOptions],
    ) -> None:

        for constant in self.constant_map:
            if (
                self.__is_this_a_datum(constant)
                and MappingOptions.prohibit_direct not in mapping_options
            ):
                self.init.add(
                    self.mapped_to(
                        self.constant_map[constant], self.constant_map[constant]
                    )
                )

        for mappable_item in flow_definition.list_of_mappings:
            source = self.constant_map[mappable_item.source_name]
            target = self.constant_map[mappable_item.target_name]

            if not mappable_item.probability:
                self.init.add(self.not_mappable(source, target))
            else:
                self.init.add(self.is_mappable(source, target))
                self.init.set(
                    self.map_affinity(source, target),
                    int((2 - mappable_item.probability) * CostOptions.UNIT.value),
                )

            if MappingOptions.transitive in mapping_options:
                if not mappable_item.probability:
                    self.init.add(self.not_mappable(target, source))

                else:
                    self.init.add(self.is_mappable(target, source))
                    self.init.set(
                        self.map_affinity(target, source),
                        int((2 - mappable_item.probability) * CostOptions.UNIT.value),
                    )

        x = self.lang.variable("x", self.type_map[TypeOptions.ROOT.value])
        y = self.lang.variable("y", self.type_map[TypeOptions.ROOT.value])

        precondition_list = [
            self.known(x, self.constant_map[MemoryState.KNOWN.value]),
            self.is_mappable(x, y),
            neg(self.not_mappable(x, y)),
            neg(self.mapped_to(x, y)),
            neg(self.new_item(y)),
            self.been_used(y),
        ]

        self.problem.action(
            BasicOperations.MAPPER.value,
            parameters=[x, y],
            precondition=land(*precondition_list, flat=True),
            effects=[
                fs.AddEffect(
                    self.known(
                        y,
                        self.constant_map[MemoryState.UNCERTAIN.value]
                        if LifeCycleOptions.confirm_on_mapping in variable_life_cycle
                        else self.constant_map[MemoryState.KNOWN.value],
                    )
                ),
                fs.AddEffect(self.mapped_to(x, y)),
                fs.AddEffect(self.mapped(x)),
                fs.DelEffect(self.been_used(y)),
                fs.DelEffect(self.not_usable(y)),
            ],
            cost=iofs.AdditiveActionCost(self.map_affinity(x, y)),
        )

        self.problem.action(
            f"{BasicOperations.MAPPER.value}--free-alt",
            parameters=[x, y],
            precondition=land(*precondition_list, self.free(x), flat=True),
            effects=[
                fs.AddEffect(
                    self.known(
                        y,
                        self.constant_map[MemoryState.UNCERTAIN.value]
                        if LifeCycleOptions.confirm_on_mapping in variable_life_cycle
                        else self.constant_map[MemoryState.KNOWN.value],
                    )
                ),
                fs.AddEffect(self.mapped_to(x, y)),
                fs.AddEffect(self.mapped(x)),
                fs.AddEffect(self.free(y)),
                fs.DelEffect(self.been_used(y)),
                fs.DelEffect(self.not_usable(y)),
            ],
            cost=iofs.AdditiveActionCost(
                self.problem.language.constant(
                    CostOptions.INTERMEDIATE.value,
                    self.problem.language.get_sort("Integer"),
                )
            ),
        )

        for typing in self.type_map:
            if typing not in [t.value for t in TypeOptions]:
                x = self.lang.variable("x", self.type_map[typing])
                y = self.lang.variable("y", self.type_map[typing])

                precondition_list = [
                    self.known(x, self.constant_map[MemoryState.KNOWN.value]),
                    neg(self.mapped_to(x, y)),
                    neg(self.mapped(x)),
                    neg(self.not_mappable(x, y)),
                    neg(self.new_item(y)),
                    self.been_used(y),
                ]

                self.problem.action(
                    f"{BasicOperations.MAPPER.value}----{typing}",
                    parameters=[x, y],
                    precondition=land(*precondition_list, flat=True),
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
                        fs.AddEffect(self.mapped_to(x, y)),
                        fs.AddEffect(self.mapped(x)),
                        fs.DelEffect(self.been_used(y)),
                        fs.DelEffect(self.not_usable(y)),
                    ],
                    cost=iofs.AdditiveActionCost(
                        self.problem.language.constant(
                            CostOptions.LOW.value,
                            self.problem.language.get_sort("Integer"),
                        )
                    ),
                )

                self.problem.action(
                    f"{BasicOperations.MAPPER.value}----{typing}--free-alt",
                    parameters=[x, y],
                    precondition=land(*precondition_list, self.free(x), flat=True),
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
                        fs.AddEffect(self.mapped_to(x, y)),
                        fs.AddEffect(self.mapped(x)),
                        fs.AddEffect(self.free(y)),
                        fs.DelEffect(self.been_used(y)),
                        fs.DelEffect(self.not_usable(y)),
                    ],
                    cost=iofs.AdditiveActionCost(
                        self.problem.language.constant(
                            CostOptions.INTERMEDIATE.value,
                            self.problem.language.get_sort("Integer"),
                        )
                    ),
                )

    def __compile_goal_item(
        self, goal_item: GoalItem, goal_predicates: Set[Any]
    ) -> None:

        if goal_item.goal_type == GoalType.OPERATOR:
            goal = goal_item.goal_name

            if isinstance(goal, Step):
                new_goal_predicate = f"has_done_{goal.name}"
                new_goal_parameters = [
                    self.constant_map[p.item_id]
                    if isinstance(p, Parameter)
                    else self.constant_map[p]
                    for p in goal.parameters
                ]

                try_level = 1
                for historical_step in self.flow_definition.history:
                    try_level += int(goal == historical_step)

                try_level_parameter = self.constant_map[f"try_level_{try_level}"]
                new_goal_parameters.append(try_level_parameter)
                goal_predicates.add(
                    getattr(self, new_goal_predicate)(*new_goal_parameters)
                )

            elif isinstance(goal, str):
                goal_predicates.add(
                    self.has_done(
                        self.constant_map[goal],
                        self.constant_map[HasDoneState.present.value],
                    )
                )

            else:
                TypeError("Unrecognized goal type.")

        else:

            list_of_constants = list()
            if goal_item.goal_name in self.type_map:
                for item in self.constant_map:
                    type_of_item = self.__get_type_of_constant(item)

                    if type_of_item == goal_item.goal_name and "new_object" not in item:
                        list_of_constants.append(item)
            else:
                list_of_constants = [goal_item.goal_name]

            if goal_item.goal_type == GoalType.OBJECT_USED:
                goal_predicates.update(
                    self.been_used(self.constant_map[item])
                    for item in list_of_constants
                )

            elif goal_item.goal_type == GoalType.OBJECT_KNOWN:
                goal_predicates.update(
                    self.known(
                        self.constant_map[item],
                        self.constant_map[MemoryState.KNOWN.value],
                    )
                    for item in list_of_constants
                )

            else:
                raise TypeError("Unrecognized goal type.")

    def __compile_goals(
        self, list_of_goal_items: List[GoalItems], goal_type: GoalOptions
    ) -> None:

        goal_predicates: Set[Any]

        if goal_type == GoalOptions.AND_AND:
            goal_predicates = set()

            for goal_items in list_of_goal_items:
                for goal_item in goal_items.goals:
                    self.__compile_goal_item(goal_item, goal_predicates)

            self.problem.goal = land(*goal_predicates, flat=True)

        elif goal_type == GoalOptions.OR_AND:

            for goal_index, goal_items in enumerate(list_of_goal_items):
                goal_predicates = set()
                for goal_item in goal_items.goals:
                    self.__compile_goal_item(goal_item, goal_predicates)

                self.problem.action(
                    f"{RestrictedOperations.GOAL.value}-{goal_index}",
                    parameters=[],
                    precondition=land(*goal_predicates, flat=True),
                    effects=[fs.AddEffect(self.done_goal_pre())],
                    cost=iofs.AdditiveActionCost(
                        self.problem.language.constant(
                            CostOptions.VERY_HIGH.value,
                            self.problem.language.get_sort("Integer"),
                        )
                    ),
                )

            self.problem.goal = self.done_goal_post()
            self.problem.action(
                f"{RestrictedOperations.GOAL.value}",
                parameters=[],
                precondition=self.done_goal_pre(),
                effects=[fs.AddEffect(self.done_goal_post())],
                cost=iofs.AdditiveActionCost(
                    self.problem.language.constant(
                        CostOptions.VERY_HIGH.value,
                        self.problem.language.get_sort("Integer"),
                    )
                ),
            )

        elif goal_type == GoalOptions.AND_OR:
            goal_predicates = set()

            for goal_index, goal_items in enumerate(list_of_goal_items):
                new_goal_predicate_name = f"has_done_pre_{goal_index}"
                new_goal_predicate = self.lang.predicate(new_goal_predicate_name)

                setattr(self, new_goal_predicate_name, new_goal_predicate)

                new_goal = getattr(self, new_goal_predicate_name)()
                goal_predicates.add(new_goal)

                for goal_item_index, goal_item in enumerate(goal_items.goals):
                    precondition_set: Set[Any] = set()

                    self.__compile_goal_item(goal_item, precondition_set)
                    self.problem.action(
                        f"{RestrictedOperations.GOAL.value}-{goal_index}-{goal_item_index}",
                        parameters=[],
                        precondition=land(*precondition_set, flat=True),
                        effects=[fs.AddEffect(new_goal)],
                        cost=iofs.AdditiveActionCost(
                            self.problem.language.constant(
                                CostOptions.VERY_HIGH.value,
                                self.problem.language.get_sort("Integer"),
                            )
                        ),
                    )

            self.problem.goal = land(*goal_predicates, flat=True)

        else:
            raise TypeError("Unrecognized goal option.")

    def __add_to_condition_list_pre_check(
        self, parameter: Union[str, MemoryItem]
    ) -> None:
        if isinstance(parameter, str):
            self.__add_memory_item_to_constant_map(
                MemoryItem(item_id=parameter, item_type=TypeOptions.ROOT.value)
            )

        elif isinstance(parameter, MemoryItem):
            self.__add_memory_item_to_constant_map(parameter)
        else:
            raise TypeError

    def __compile_actions(
        self,
        list_of_actions: List[OperatorDefinition],
        variable_life_cycle: Set[LifeCycleOptions],
        mapping_options: Set[MappingOptions],
        multi_instance: bool = True,
    ) -> None:

        for operator in list_of_actions:
            self.constant_map[operator.name] = self.lang.constant(
                operator.name, TypeOptions.OPERATOR.value
            )

        for operator in list_of_actions:
            parameter_list: List[Any] = list()
            precondition_list: List[Any] = list()
            add_effect_list = [
                self.has_done(
                    self.constant_map[operator.name],
                    self.constant_map[HasDoneState.present.value],
                )
            ]
            del_effect_list = list()
            type_list = list()

            for o_input in operator.inputs:
                for param in o_input.parameters:
                    self.__add_to_condition_list_pre_check(param)
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

                    self.init.add(self.been_used(self.constant_map[param]))

                    add_effect_list.extend(
                        [
                            self.been_used(x),
                            self.been_used(self.constant_map[param]),
                        ]
                    )
                    precondition_list.extend(
                        [
                            self.mapped_to(x, self.constant_map[param]),
                            self.known(
                                self.constant_map[param],
                                self.constant_map[MemoryState.KNOWN.value],
                            ),
                        ]
                    )

                    if MappingOptions.prohibit_direct in mapping_options:
                        self.init.add(self.not_usable(self.constant_map[param]))
                        precondition_list.append(neg(self.not_usable(x)))

                    if LifeCycleOptions.uncertain_on_use in variable_life_cycle:
                        del_effect_list.append(
                            self.known(
                                self.constant_map[param],
                                self.constant_map[MemoryState.KNOWN.value],
                            )
                        )

                        add_effect_list.append(
                            self.known(
                                self.constant_map[param],
                                self.constant_map[MemoryState.UNCERTAIN.value],
                            )
                        )

                for constraint in o_input.constraints:
                    constraint_predicate = self.__compile_constraints(constraint)
                    precondition_list.append(constraint_predicate)

            if multi_instance:
                new_has_done_predicate_name = f"has_done_{operator.name}"
                has_done_parameters = [
                    self.type_map[type_name] for type_name in type_list
                ]
                has_done_parameters.append(self.type_map[TypeOptions.RETRY.value])

                new_has_done_predicate = self.lang.predicate(
                    new_has_done_predicate_name,
                    *has_done_parameters,
                )

                setattr(self, new_has_done_predicate_name, new_has_done_predicate)

                pre_level = self.lang.variable(
                    "pre_level", self.type_map[TypeOptions.RETRY.value]
                )
                post_level = self.lang.variable(
                    "post_level", self.type_map[TypeOptions.RETRY.value]
                )

                precondition_list.extend(
                    [
                        getattr(self, new_has_done_predicate_name)(
                            *parameter_list, pre_level
                        ),
                        neg(
                            getattr(self, new_has_done_predicate_name)(
                                *parameter_list, post_level
                            )
                        ),
                        self.connected(
                            self.constant_map[operator.name], pre_level, post_level
                        ),
                    ]
                )

                add_effect_list.append(
                    getattr(self, new_has_done_predicate_name)(
                        *parameter_list, post_level
                    )
                )

                for try_level in range(operator.max_try):
                    self.init.add(
                        self.connected(
                            self.constant_map[operator.name],
                            self.constant_map[f"try_level_{try_level}"],
                            self.constant_map[f"try_level_{try_level+1}"],
                        )
                    )

                self.__add_enabler_action_for_operator(
                    operator, parameter_list, new_has_done_predicate_name
                )
                parameter_list.extend([pre_level, post_level])

            else:
                precondition_list.append(
                    neg(
                        self.has_done(
                            self.constant_map[operator.name],
                            self.constant_map[HasDoneState.past.value],
                        )
                    )
                )

            outputs = operator.outputs[0]
            for o_output in outputs.outcomes:
                for param in o_output.parameters:
                    self.__add_to_condition_list_pre_check(param)

                    if isinstance(param, MemoryItem):
                        param = param.item_id

                    del_effect_list.append(self.mapped(self.constant_map[param]))
                    add_effect_list.extend(
                        [
                            self.free(self.constant_map[param]),
                            self.known(
                                self.constant_map[param],
                                self.constant_map[MemoryState.UNCERTAIN.value]
                                if LifeCycleOptions.confirm_on_determination
                                in variable_life_cycle
                                else self.constant_map[MemoryState.KNOWN.value],
                            ),
                        ]
                    )

                for constraint in o_output.constraints:
                    constraint_predicate = self.__compile_constraints(constraint)
                    add_effect_list.append(constraint_predicate)

            self.__add_partial_orders(operator, precondition_list)
            self.problem.action(
                operator.name,
                parameters=parameter_list,
                precondition=land(*precondition_list, flat=True),
                effects=[fs.AddEffect(add) for add in add_effect_list]
                + [fs.DelEffect(dele) for dele in del_effect_list],
                cost=iofs.AdditiveActionCost(
                    self.problem.language.constant(
                        operator.cost, self.problem.language.get_sort("Integer")
                    )
                ),
            )

    def __add_partial_orders(
        self, operator: OperatorDefinition, precondition_list: List[Any]
    ) -> None:
        for partial_order in self.flow_definition.partial_orders:
            if (
                partial_order.consequent == operator.name
                and partial_order.antecedent
                not in [o.name for o in self.flow_definition.history]
            ):
                precondition_list.append(
                    self.has_done(
                        self.constant_map[partial_order.antecedent],
                        self.constant_map[HasDoneState.present.value],
                    )
                )

            if partial_order.antecedent == operator.name:
                precondition_list.append(
                    neg(
                        self.has_done(
                            self.constant_map[partial_order.consequent],
                            self.constant_map[HasDoneState.past.value],
                        )
                    )
                )

        if (
            self.flow_definition.starts_with
            and self.flow_definition.starts_with != operator.name
        ):
            precondition_list.append(
                self.has_done(
                    self.constant_map[self.flow_definition.starts_with],
                    self.constant_map[HasDoneState.present.value],
                )
            )

        if self.flow_definition.ends_with:
            precondition_list.append(
                neg(
                    self.has_done(
                        self.constant_map[self.flow_definition.ends_with],
                        self.constant_map[HasDoneState.present.value],
                    )
                )
            )

    def __add_enabler_action_for_operator(
        self,
        operator: OperatorDefinition,
        parameter_list: List[Any],
        new_has_done_predicate_name: Any,
    ) -> None:
        enabler_predicate = getattr(self, new_has_done_predicate_name)(
            *parameter_list, self.constant_map["try_level_0"]
        )
        shadow_predicate = getattr(self, new_has_done_predicate_name)(
            *parameter_list, self.constant_map["try_level_1"]
        )

        self.problem.action(
            f"{RestrictedOperations.ENABLER.value}__{operator.name}",
            parameters=copy.deepcopy(parameter_list),
            precondition=land(
                *[neg(enabler_predicate), neg(shadow_predicate)], flat=True
            ),
            effects=[fs.AddEffect(enabler_predicate)],
            cost=iofs.AdditiveActionCost(
                self.problem.language.constant(
                    CostOptions.HIGH.value,
                    self.problem.language.get_sort("Integer"),
                )
            ),
        )

    def __compile_constraints(
        self,
        constraint: Constraint,
    ) -> Any:

        new_constraint_variable = f"status_{constraint.constraint_id}"
        set_variables = [self.constant_map[item] for item in constraint.parameters]
        closed_variables = [
            self.type_map[self.__get_type_of_constant(item)]
            for item in constraint.parameters
        ] + [self.type_map[TypeOptions.STATUS.value]]

        if new_constraint_variable not in [
            item.symbol for item in self.lang.predicates
        ]:
            new_constraint_predicate = self.lang.predicate(
                new_constraint_variable,
                *closed_variables,
            )

            setattr(self, new_constraint_variable, new_constraint_predicate)

            for truth_value in ConstraintState:
                operator_name = f"{BasicOperations.CONSTRAINT.value}_{constraint.constraint_id}_to_{truth_value.value}"

                precondition_list = list()
                add_effect_list = list()
                del_effect_list = list()

                for index, parameter in enumerate(constraint.parameters):

                    if parameter not in self.constant_map:
                        self.__add_memory_item_to_constant_map(
                            MemoryItem(
                                item_id=parameter, item_type=TypeOptions.ROOT.value
                            )
                        )

                    del_effect_list.append(self.free(self.constant_map[parameter]))
                    precondition_list.extend(
                        [
                            self.known(
                                self.constant_map[parameter],
                                self.constant_map[MemoryState.KNOWN.value],
                            ),
                        ]
                    )

                    set_predicate = getattr(self, new_constraint_variable)(
                        *set_variables, self.constant_map[str(truth_value.value)]
                    )
                    shadow_predicate = getattr(self, new_constraint_variable)(
                        *set_variables, self.constant_map[str(not truth_value.value)]
                    )

                    enabler_name = f"{RestrictedOperations.ENABLER.value}__{constraint.constraint_id}_{parameter}"

                    if enabler_name not in self.problem.actions:
                        self.problem.action(
                            enabler_name,
                            parameters=list(),
                            precondition=land(self.free(self.constant_map[parameter])),
                            effects=[
                                fs.DelEffect(set_predicate),
                                fs.DelEffect(shadow_predicate),
                            ],
                            cost=iofs.AdditiveActionCost(
                                self.problem.language.constant(
                                    CostOptions.UNIT.value,
                                    self.problem.language.get_sort("Integer"),
                                )
                            ),
                        )

                set_predicate = getattr(self, new_constraint_variable)(
                    *set_variables, self.constant_map[str(truth_value.value)]
                )
                shadow_predicate = getattr(self, new_constraint_variable)(
                    *set_variables, self.constant_map[str(not truth_value.value)]
                )
                add_effect_list.append(set_predicate)
                precondition_list.extend(
                    [
                        neg(set_predicate),
                        neg(shadow_predicate),
                    ]
                )

                if operator_name not in self.problem.actions:
                    self.problem.action(
                        operator_name,
                        parameters=list(),
                        precondition=land(*precondition_list, flat=True),
                        effects=[fs.AddEffect(add) for add in add_effect_list]
                        + [fs.DelEffect(dele) for dele in del_effect_list],
                        cost=iofs.AdditiveActionCost(
                            self.problem.language.constant(
                                CostOptions.UNIT.value,
                                self.problem.language.get_sort("Integer"),
                            )
                        ),
                    )

        for known_constraint in self.flow_definition.constraints:
            if known_constraint.constraint_id == constraint.constraint_id:
                self.init.add(
                    getattr(self, new_constraint_variable)(
                        *set_variables,
                        self.constant_map[str(known_constraint.truth_value)],
                    )
                )

        return getattr(self, new_constraint_variable)(
            *set_variables, self.constant_map[str(constraint.truth_value)]
        )

    def __compile_history(
        self, flow: FlowDefinition, multi_instance: bool = True
    ) -> None:
        for idx, history_item in enumerate(flow.history):
            operator_name = history_item.name
            self.init.add(
                self.has_done(
                    self.constant_map[operator_name],
                    self.constant_map[HasDoneState.past.value],
                )
            )

            if multi_instance:
                indices_of_interest = [
                    index
                    for index, item in enumerate(flow.history)
                    if item.name == operator_name
                ]
                num_try = indices_of_interest.index(idx) + 1

                has_done_predicate_name = f"has_done_{operator_name}"
                parameter_names = [p.item_id for p in history_item.parameters]
                parameter_names.append(f"try_level_{num_try}")

                self.init.add(
                    getattr(self, has_done_predicate_name)(
                        *[self.constant_map[p] for p in parameter_names]
                    )
                )

    def __get_source_map(self) -> Dict[str, List[str]]:
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

        return source_map

    def __get_type_of_constant(self, constant: str) -> str:
        constant_type: str = TypeOptions.ROOT.value

        for item in self.constant_map:
            if item == constant:
                constant_type = self.constant_map[item].sort.name
                break

        return constant_type

    @staticmethod
    def __is_this_a_datum_type(type_name: str) -> bool:
        return type_name not in [
            TypeOptions.MEMORY.value,
            TypeOptions.OPERATOR.value,
            TypeOptions.HASDONE.value,
            TypeOptions.RETRY.value,
            TypeOptions.STATUS.value,
        ]

    def __is_this_a_datum(self, constant: str) -> bool:
        type_name = self.__get_type_of_constant(constant)
        return self.__is_this_a_datum_type(type_name)

    def __add_retry_states(self, max_retry: int) -> None:
        for item in range(max_retry + 2):
            self.__add_memory_item_to_constant_map(
                MemoryItem(
                    item_id=f"try_level_{item}", item_type=TypeOptions.RETRY.value
                )
            )

    @staticmethod
    def __generate_new_objects(type_name: str, num_lookahead: int) -> List[str]:
        return [f"new_object_{type_name}_{index}" for index in range(num_lookahead)]

    def __add_extra_objects(self, num_lookahead: int) -> None:
        for type_name in self.type_map:
            if self.__is_this_a_datum_type(type_name):
                new_objects = self.__generate_new_objects(type_name, num_lookahead)

                for new_object in new_objects:
                    self.__add_memory_item_to_constant_map(
                        MemoryItem(item_id=new_object, item_type=type_name)
                    )
                    self.init.add(self.new_item(self.constant_map[new_object]))

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

        self.type_map[TypeOptions.HASDONE.value] = self.lang.sort(
            TypeOptions.HASDONE.value
        )

        for has_done_state in HasDoneState:
            self.constant_map[has_done_state.value] = self.lang.constant(
                has_done_state.value, TypeOptions.HASDONE.value
            )

        self.type_map[TypeOptions.STATUS.value] = self.lang.sort(
            TypeOptions.STATUS.value
        )

        for constraint_state in ConstraintState:
            self.constant_map[str(constraint_state.value)] = self.lang.constant(
                str(constraint_state.value), TypeOptions.STATUS.value
            )

        self.type_map[TypeOptions.MEMORY.value] = self.lang.sort(
            TypeOptions.MEMORY.value
        )

        for memory_state in MemoryState:
            self.constant_map[memory_state.value] = self.lang.constant(
                memory_state.value, TypeOptions.MEMORY.value
            )

        self.has_done = self.lang.predicate(
            "has_done",
            self.type_map[TypeOptions.OPERATOR.value],
            self.type_map[TypeOptions.HASDONE.value],
        )

        self.been_used = self.lang.predicate(
            "been_used",
            self.type_map[TypeOptions.ROOT.value],
        )

        self.new_item = self.lang.predicate(
            "new_item", self.type_map[TypeOptions.ROOT.value]
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

        self.not_mappable = self.lang.predicate(
            "not_mappable",
            self.type_map[TypeOptions.ROOT.value],
            self.type_map[TypeOptions.ROOT.value],
        )

        self.mapped = self.lang.predicate(
            "mapped",
            self.type_map[TypeOptions.ROOT.value],
        )

        self.not_usable = self.lang.predicate(
            "not_usable",
            self.type_map[TypeOptions.ROOT.value],
        )

        self.mapped_to = self.lang.predicate(
            "mapped_to",
            self.type_map[TypeOptions.ROOT.value],
            self.type_map[TypeOptions.ROOT.value],
        )

        self.map_affinity = self.lang.function(
            "affinity",
            self.type_map[TypeOptions.ROOT.value],
            self.type_map[TypeOptions.ROOT.value],
            self.lang.Real,
        )

        self.type_map[TypeOptions.RETRY.value] = self.lang.sort(TypeOptions.RETRY.value)

        self.connected = self.lang.predicate(
            "connected",
            self.type_map[TypeOptions.OPERATOR.value],
            self.type_map[TypeOptions.RETRY.value],
            self.type_map[TypeOptions.RETRY.value],
        )

        self.free = self.lang.predicate(
            "free",
            self.type_map[TypeOptions.ROOT.value],
        )

        self.done_goal_pre = self.lang.predicate("done_goal_pre")
        self.done_goal_post = self.lang.predicate("done_goal_post")

        for type_item in self.flow_definition.type_hierarchy:
            self.__add_type_item_to_type_map(type_item)

        for memory_item in self.flow_definition.memory_items:
            self.__add_memory_item_to_constant_map(memory_item)

            if memory_item.item_state != MemoryState.UNKNOWN:
                self.init.add(
                    self.known(
                        self.constant_map[memory_item.item_id],
                        self.constant_map[memory_item.item_state.value],
                    )
                )

        multi_instance_option: bool = kwargs.get("multi_instance", True)  # type: ignore
        variable_life_cycle: Set[LifeCycleOptions] = set(kwargs["variable_life_cycle"])

        lookahead_option: int = kwargs.get("lookahead", LOOKAHEAD)  # type: ignore
        slot_options: Set[SlotOptions] = set(kwargs["slot_options"])
        mapping_options: Set[MappingOptions] = set(kwargs["mapping_options"])

        self.__add_retry_states(MAX_RETRY)
        self.__compile_actions(
            self.flow_definition.operators,
            variable_life_cycle,
            mapping_options,
            multi_instance=multi_instance_option,
        )

        self.__add_extra_objects(num_lookahead=lookahead_option)
        self.__compile_confirmation(variable_life_cycle)

        self.__compile_slots(
            self.flow_definition, slot_options, variable_life_cycle, lookahead_option
        )

        self.__compile_mappings(
            self.flow_definition, mapping_options, variable_life_cycle
        )

        self.__compile_history(self.flow_definition, multi_instance_option)

        goal_type: GoalOptions = kwargs["goal_type"]
        self.__compile_goals(self.flow_definition.goal_items, goal_type)

        self.init.set(self.cost(), 0)
        self.problem.init = self.init

        writer = FstripsWriter(self.problem)
        domain = writer.print_domain().replace(" :numeric-fluents", "")
        problem = writer.print_instance()

        return PDDL(domain=domain, problem=problem), self.cached_transforms
