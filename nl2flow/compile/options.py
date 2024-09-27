from __future__ import annotations
from typing import Optional
from enum import Enum


LOOKAHEAD: int = 1
RETRY: int = 1
MAX_RETRY: int = 5
SLOT_GOODNESS: float = 0.5
MAX_LABELS: int = 7
PARAMETER_DELIMITER = "----"


class NL2FlowOptions(Enum):
    multi_instance = "MULTI_INSTANCE"
    allow_retries = "ALLOW_RETRIES"
    label_production = "LABELS"


class RestrictedOperations(Enum):
    UNTOKENIZE = "untokenize"
    TOKENIZE = "tokenize"
    MANIFEST = "manifest"
    ENABLER = "enabler_operator"
    GOAL = "goal_operator"

    @classmethod
    def is_restricted(cls, name: str) -> bool:
        return any([name.startswith(x.value) for x in cls])


class BasicOperations(Enum):
    SLOT_FILLER = "ask"
    MAPPER = "map"
    CONFIRM = "confirm"
    CONSTRAINT = "assert"

    @classmethod
    def is_basic(cls, name: str) -> bool:
        return name in [x.value for x in cls]

    @classmethod
    def which_basic(cls, name: str) -> Optional[BasicOperations]:
        for item in BasicOperations:
            if name.startswith(item.value):
                return item

        return None


class CompileOptions(Enum):
    CLASSICAL = "CLASSICAL"
    ALL_OUTCOMES = "ALL_OUTCOMES"
    MAX_OUTCOMES = "MOST_LIKELY_OUTCOME"


class TypeOptions(Enum):
    LABEL = "label"
    RETRY = "num-retries"
    HAS_DONE = "has-done-state"
    MEMORY = "datum-state"
    STATUS = "constraint-status"
    OPERATOR = "operator"
    CONSTRAINT = "constraint"
    ROOT = "generic"
    LEAF = "end"


class CostOptions(Enum):
    ZERO = 0
    EDIT = 1
    UNIT = 10
    VERY_LOW = 20
    LOW = 50
    MEDIUM = 250
    INTERMEDIATE = 1000
    HIGH = 5000
    VERY_HIGH = 100000


class ConfirmOptions(Enum):
    group_confirms = "GROUP"


class MappingOptions(Enum):
    ignore_types = "IGNORE_TYPES"
    group_maps = "GROUP"
    relaxed = "RELAXED"
    immediate = "IMMEDIATE"
    eventual = "EVENTUAL"
    transitive = "TRANSITIVE"
    prohibit_direct = "INDIRECT_MAP"


class SlotOptions(Enum):
    group_slots = "GROUP"
    higher_cost = "COST"
    last_resort = "FALLBACK"
    ordered = "ORDERED"
    all_together = "TOGETHER"
    relaxed = "RELAXED"
    immediate = "IMMEDIATE"
    eventual = "EVENTUAL"


class HasDoneState(Enum):
    past = "past"
    present = "present"
    future = "future"


class MemoryState(Enum):
    KNOWN = "certain"
    UNKNOWN = "unknown"
    UNCERTAIN = "uncertain"


class ConstraintState(Enum):
    TRUE = True
    FALSE = False


class LifeCycleOptions(Enum):
    uncertain_on_use = "UNCERTAIN-USE"
    confirm_on_mapping = "CONFIRM-MAP"
    confirm_on_determination = "CONFIRM-DET"
    confirm_on_slot = "CONFIRM-SLOT"


class GoalOptions(Enum):
    AND_AND = "DEFAULT"
    AND_OR = "AND-OR"
    OR_AND = "OR-AND"


class GoalType(Enum):
    OPERATOR = "OPERATOR"
    OBJECT_KNOWN = "OBJECT_KNOWN"
    OBJECT_USED = "OBJECT_USED"
    CONSTRAINT = "CONSTRAINT"
