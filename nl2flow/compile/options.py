import enum

LOOKAHEAD: int = 2
RETRY: int = 3
SLOT_GOODNESS: float = 0.5


class BasicOperations(enum.Enum):
    SLOT_FILLER = "ask"
    MAPPER = "map"
    TRANSFORM = "transform"
    CONFIRM = "confirm"


class CompileOptions(enum.Enum):
    CLASSICAL = "CLASSICAL"
    ALLOUTCOMES = "ALL_OUTCOMES"
    MAXOUTCOMES = "MOST_LIKELY_OUTCOME"


class TypeOptions(enum.Enum):
    MEMORY = "datum-state"
    OPERATOR = "operator"
    ROOT = "generic"
    LEAF = "end"


class CostOptions(enum.Enum):
    ZERO = 0
    UNIT = 10
    LOW = 50
    MEDIUM = 250
    INTERMEDIATE = 1000
    HIGH = 5000
    VERY_HIGH = 100000


class MappingOptions(enum.Enum):
    relaxed = "RELAXED"
    immediate = "IMMEDIATE"
    eventual = "EVENTUAL"
    transitive = "TRANSITIVE"


class SlotOptions(enum.Enum):
    group_slots = "GROUP"
    higher_cost = "COST"
    last_resort = "FALLBACK"
    ordered = "ORDERED"
    relaxed = "RELAXED"
    immediate = "IMMEDIATE"
    eventual = "EVENTUAL"


class MemoryState(enum.Enum):
    KNOWN = "certain"
    UNKNOWN = "unknown"
    UNCERTAIN = "uncertain"


class LifeCycleOptions(enum.Enum):
    uncertain_on_use = "UNCERTAIN-USE"
    confirm_on_mapping = "CONFIRM-MAP"
    confirm_on_determination = "CONFIRM-DET"
    confirm_on_transform = "CONFIRM-TRANS"
    confirm_on_slot = "CONFIRM-SLOT"


class GoalOptions(enum.Enum):
    AND = "AND-OR"
    OR = "OR-AND"


class GoalType(enum.Enum):
    OPERATOR = "OPERATOR"
    OBJECT = "OBJECT"
