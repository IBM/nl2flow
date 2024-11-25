import tarski
import tarski.fstrips as fs
from tarski.theories import Theory
from tarski.io import FstripsWriter
from abc import ABC, abstractmethod
from typing import List, Set, Dict, Any, Tuple, Optional
from nl2flow.debug.schemas import DebugFlag
from nl2flow.compile.schemas import (
    FlowDefinition,
    PDDL,
    Transform,
    TypeItem,
    MemoryItem,
)

from nl2flow.compile.basic_compilations.compile_operators import compile_operators
from nl2flow.compile.basic_compilations.compile_confirmation import compile_confirmation
from nl2flow.compile.basic_compilations.compile_references.utils import (
    set_token_predicate,
    get_token_predicate,
    get_token_predicate_name,
)
from nl2flow.compile.basic_compilations.compile_references.compile_reference_tokenize import compile_reference_tokenize
from nl2flow.compile.basic_compilations.compile_references.compile_reference_basic import compile_reference_basic

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
    MAX_LABELS,
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
        self.label_tag: Any = None
        self.available: Any = None
        self.assigned_to: Any = None
        self.ready_for_token: Any = None

        self.type_map: Dict[str, Any] = dict()
        self.constant_map: Dict[str, Any] = dict()

    def compile(self, **kwargs: Any) -> Tuple[PDDL, List[Transform]]:
        used_labels_in_memory = self.construct_state_predicates(**kwargs)

        debug_flag: Optional[DebugFlag] = kwargs.get("debug_flag", None)
        slot_options: Set[SlotOptions] = set(kwargs["slot_options"])
        optimization_options: Set[NL2FlowOptions] = set(kwargs["optimization_options"])

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
        used_labels_in_history = compile_history(self, **kwargs)

        if NL2FlowOptions.label_production in optimization_options:
            for label in range(0, MAX_LABELS + 1):
                label_name = get_token_predicate_name(index=label, token="var")
                if label_name not in used_labels_in_history and label_name not in used_labels_in_memory:
                    self.init.add(self.available(self.constant_map[label_name]))

        if debug_flag == DebugFlag.TOKENIZE:
            compile_reference_tokenize(self, flow_definition=self.flow_definition, **kwargs)
        elif debug_flag == DebugFlag.DIRECT:
            compile_reference_basic(self, flow_definition=self.flow_definition, **kwargs)

        self.init.set(self.cost(), 0)
        self.problem.init = self.init

        writer = FstripsWriter(self.problem)
        domain = writer.print_domain(constant_objects=list(self.constant_map.values())).replace(" :numeric-fluents", "")
        problem = writer.print_instance(constant_objects=list(self.constant_map.values()))

        return PDDL(domain=domain, problem=problem), self.cached_transforms

    def construct_state_predicates(self, **kwargs: Any) -> List[str]:
        debug_flag: Optional[DebugFlag] = kwargs.get("debug_flag", None)
        optimization_options: Set[NL2FlowOptions] = set(kwargs["optimization_options"])

        reserved_types = [
            TypeOptions.ROOT,
            TypeOptions.OPERATOR,
            TypeOptions.HAS_DONE,
            TypeOptions.STATUS,
            TypeOptions.MEMORY,
            TypeOptions.LABEL,
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

        if NL2FlowOptions.label_production in optimization_options:
            self.construct_labels()

        if debug_flag:
            if self.flow_definition.reference is not None:
                for index in range(len(self.flow_definition.reference.plan) + 1):
                    set_token_predicate(self, index)

            if debug_flag == DebugFlag.DIRECT:
                init_token = get_token_predicate(self, index=0)
                self.init.add(init_token)

            if debug_flag == DebugFlag.TOKENIZE:
                self.ready_for_token = self.lang.predicate("ready_for_token")
                self.has_asked = self.lang.predicate(
                    "has_asked",
                    self.type_map[TypeOptions.ROOT.value],
                )

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

        used_labels = self.construct_memory(**kwargs)

        if NL2FlowOptions.allow_retries in optimization_options:
            add_retry_states(self)

        return used_labels

    def construct_labels(self) -> None:
        self.available = self.lang.predicate(
            "available",
            self.type_map[TypeOptions.LABEL.value],
        )

        self.assigned_to = self.lang.predicate(
            "assigned_to",
            self.type_map[TypeOptions.OPERATOR.value],
            self.type_map[TypeOptions.LABEL.value],
        )

        self.label_tag = self.lang.predicate(
            "label_tag",
            self.type_map[TypeOptions.ROOT.value],
            self.type_map[TypeOptions.LABEL.value],
        )

        memory_label_name = get_token_predicate_name(index=0, token="varm")
        add_memory_item_to_constant_map(
            self,
            MemoryItem(item_id=memory_label_name, item_type=TypeOptions.LABEL.value),
        )

        self.init.add(self.available(self.constant_map[memory_label_name]))

        for label in range(0, MAX_LABELS + 1):
            label_name = get_token_predicate_name(index=label, token="var")
            add_memory_item_to_constant_map(
                self,
                MemoryItem(item_id=label_name, item_type=TypeOptions.LABEL.value),
            )

    def construct_memory(self, **kwargs: Any) -> List[str]:
        optimization_options: Set[NL2FlowOptions] = set(kwargs["optimization_options"])
        used_labels = [get_token_predicate_name(index=0, token="var")]

        for memory_item in self.flow_definition.memory_items:
            add_memory_item_to_constant_map(self, memory_item)

            if memory_item.item_state != MemoryState.UNKNOWN:
                self.init.add(
                    self.known(
                        self.constant_map[memory_item.item_id],
                        self.constant_map[memory_item.item_state.value],
                    )
                )

                if NL2FlowOptions.label_production in optimization_options:
                    if memory_item.label:
                        used_labels.append(memory_item.label)

                    self.init.add(
                        self.label_tag(
                            self.constant_map[memory_item.item_id],
                            self.constant_map[memory_item.label or get_token_predicate_name(index=0, token="var")],
                        )
                    )

        return used_labels
