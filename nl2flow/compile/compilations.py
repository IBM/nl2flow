import tarski
import tarski.fstrips as fs
from tarski.theories import Theory
from tarski.io import FstripsWriter
from abc import ABC, abstractmethod
from typing import List, Set, Dict, Any, Tuple, Optional
from nl2flow.debug.schemas import SolutionQuality
from nl2flow.compile.schemas import (
    FlowDefinition,
    PDDL,
    Transform,
    TypeItem,
    MemoryItem,
)

from nl2flow.compile.basic_compilations.compile_operators import compile_operators
from nl2flow.compile.basic_compilations.compile_confirmation import compile_confirmation
from nl2flow.compile.basic_compilations.compile_reference import compile_reference
from nl2flow.compile.basic_compilations.compile_slots import (
    compile_higher_cost_slots,
    compile_last_resort_slots,
    compile_all_together,
    compile_new_object_maps,
    get_goodness_map,
)
from nl2flow.compile.basic_compilations.compile_mappings import (
    compile_typed_mappings,
    compile_declared_mappings,
)
from nl2flow.compile.basic_compilations.compile_goals import compile_goals
from nl2flow.compile.basic_compilations.compile_history import compile_history
from nl2flow.compile.basic_compilations.compile_constraints import compile_manifest_constraints

from nl2flow.compile.basic_compilations.utils import (
    add_type_item_to_type_map,
    add_memory_item_to_constant_map,
    add_extra_objects,
    add_retry_states,
)

from nl2flow.compile.options import (
    NL2FlowOptions,
    SlotOptions,
    MappingOptions,
    TypeOptions,
    MemoryState,
    ConstraintState,
    HasDoneState,
)


class Compilation(ABC):
    def __init__(self, flow_definition: FlowDefinition):
        self.flow_definition = flow_definition

    @abstractmethod
    def compile(self, **kwargs: Any) -> Tuple[PDDL, List[Transform]]:
        pass


class ClassicPDDL(Compilation):
    def __init__(self, flow_definition: FlowDefinition):
        Compilation.__init__(self, flow_definition)

        self.cached_transforms: List[Transform] = list()
        self.flow_definition = FlowDefinition.transform(self.flow_definition, self.cached_transforms)

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
        self.has_asked: Any = None
        self.ready_for_token: Any = None

        self.type_map: Dict[str, Any] = dict()
        self.constant_map: Dict[str, Any] = dict()

    def compile(self, **kwargs: Any) -> Tuple[PDDL, List[Transform]]:
        debug_flag: Optional[SolutionQuality] = kwargs.get("debug_flag", None)
        optimization_options: Set[NL2FlowOptions] = set(kwargs["optimization_options"])
        slot_options: Set[SlotOptions] = set(kwargs["slot_options"])

        reserved_types = [
            TypeOptions.ROOT,
            TypeOptions.OPERATOR,
            TypeOptions.HAS_DONE,
            TypeOptions.STATUS,
            TypeOptions.MEMORY,
        ]

        if NL2FlowOptions.allow_retries in optimization_options:
            reserved_types.append(TypeOptions.RETRY)

        for reserved_type in reserved_types:
            add_type_item_to_type_map(self, TypeItem(name=reserved_type.value, parent=None))

        reserved_type_map = {
            HasDoneState: TypeOptions.HAS_DONE,
            ConstraintState: TypeOptions.STATUS,
            MemoryState: TypeOptions.MEMORY,
        }

        for item in reserved_type_map:
            for item_state in item:
                add_memory_item_to_constant_map(
                    self,
                    MemoryItem(
                        item_id=str(item_state.value),
                        item_type=reserved_type_map[item].value,
                    ),
                )

        if debug_flag:
            self.ready_for_token = self.lang.predicate("ready_for_token")
            self.has_asked = self.lang.predicate(
                "has_asked",
                self.type_map[TypeOptions.ROOT.value],
            )

            for index in range(len(self.flow_definition.reference.plan) + 1):
                token_predicate_name = f"token_{index}"
                token_predicate = self.lang.predicate(token_predicate_name)
                setattr(self, token_predicate_name, token_predicate)

        self.has_done = self.lang.predicate(
            "has_done",
            self.type_map[TypeOptions.OPERATOR.value],
            self.type_map[TypeOptions.HAS_DONE.value],
        )

        self.been_used = self.lang.predicate(
            "been_used",
            self.type_map[TypeOptions.ROOT.value],
        )

        self.new_item = self.lang.predicate("new_item", self.type_map[TypeOptions.ROOT.value])

        self.known = self.lang.predicate(
            "known",
            self.type_map[TypeOptions.ROOT.value],
            self.type_map[TypeOptions.MEMORY.value],
        )

        self.not_slotfillable = self.lang.predicate("not_slotfillable", self.type_map[TypeOptions.ROOT.value])

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

        if NL2FlowOptions.allow_retries in optimization_options:
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
            add_type_item_to_type_map(self, type_item)

        for memory_item in self.flow_definition.memory_items:
            add_memory_item_to_constant_map(self, memory_item)

            if memory_item.item_state != MemoryState.UNKNOWN:
                self.init.add(
                    self.known(
                        self.constant_map[memory_item.item_id],
                        self.constant_map[memory_item.item_state.value],
                    )
                )

        if NL2FlowOptions.allow_retries in optimization_options:
            add_retry_states(self)

        compile_operators(self, **kwargs)
        compile_confirmation(self, **kwargs)
        add_extra_objects(self, **kwargs)

        if len(slot_options) > 1:
            compile_new_object_maps(self, **kwargs)
            get_goodness_map(self)

        if SlotOptions.higher_cost in slot_options:
            compile_higher_cost_slots(self, **kwargs)

        if SlotOptions.last_resort in slot_options:
            compile_last_resort_slots(self, **kwargs)

        if SlotOptions.all_together in slot_options:
            compile_all_together(self, **kwargs)

        compile_declared_mappings(self, **kwargs)

        if MappingOptions.ignore_types not in set(kwargs["mapping_options"]):
            compile_typed_mappings(self, **kwargs)

        compile_goals(self, **kwargs)
        compile_manifest_constraints(self)
        compile_history(self, **kwargs)

        if debug_flag:
            compile_reference(self, **kwargs)

        self.init.set(self.cost(), 0)
        self.problem.init = self.init

        writer = FstripsWriter(self.problem)
        domain = writer.print_domain(constant_objects=list(self.constant_map.values())).replace(" :numeric-fluents", "")
        problem = writer.print_instance(constant_objects=list(self.constant_map.values()))

        return PDDL(domain=domain, problem=problem), self.cached_transforms
