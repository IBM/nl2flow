import enum

LOOKAHEAD: int = 2
RETRY: int = 3


class CompileOptions(enum.Enum):
    CLASSICAL = "CLASSICAL"
    ALLOUTCOMES = "ALL_OUTCOMES"
    MAXOUTCOMES = "MOST_LIKELY_OUTCOME"


class TypeOptions(enum.Enum):
    ROOT = "generic"
    LEAF = "end"


class CostOptions(enum.Enum):
    ZERO = 0
    UNIT = 1
    LOW = 5
    MEDIUM = 20
    INTERMEDIATE = 50
    HIGH = 100
    VERY_HIGH = 500


class MappingOptions(enum.Enum):
    relaxed = "RELAXED"
    immediate = "IMMEDIATE"
    eventual = "EVENTUAL"


class SlotOptions(enum.Enum):
    higher_cost = "COST"
    last_resort = "FALLBACK"
    ordered = "ORDERED"
    relaxed = "RELAXED"
    immediate = "IMMEDIATE"
    eventual = "EVENTUAL"


class MemoryState(enum.Enum):
    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"
    UNCERTAIN = "UNCERTAIN"


class LifeCycleOptions(enum.Enum):
    bistate = "BISTATE"
    bi_tristate = "BI_TRISTATE"
    tristate = "TRISTATE"


class GoalOptions(enum.Enum):
    AND = "AND-OR"
    OR = "OR-AND"


class GoalType(enum.Enum):
    OPERATOR = "OPERATOR"
    OBJECT = "OBJECT"
