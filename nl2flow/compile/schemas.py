from __future__ import annotations
from typing import Set, List, Optional, Union
from pydantic import BaseModel, validator

from nl2flow.plan.schemas import HistoricalStep, Parameter
from nl2flow.compile.utils import string_transform, Transform
from nl2flow.compile.options import (
    TypeOptions,
    CostOptions,
    GoalType,
    MemoryState,
    SLOT_GOODNESS,
    RETRY,
)


class MappingItem(BaseModel):
    source_name: str
    target_name: str
    probability: float = 1.0

    @classmethod
    def transform(
        cls, mapping_item: MappingItem, transforms: List[Transform]
    ) -> MappingItem:
        return MappingItem(
            source_name=string_transform(mapping_item.source_name, transforms),
            target_name=string_transform(mapping_item.target_name, transforms),
            probability=mapping_item.probability,
        )

    @validator("probability")
    def _(cls, value: float) -> float:
        assert 0.0 <= value <= 1.0, "Probability must be between 0 and 1."
        return value


class MemoryItem(Parameter):
    item_state: MemoryState = MemoryState.UNKNOWN

    @classmethod
    def transform(
        cls, memory_item: MemoryItem, transforms: List[Transform]
    ) -> MemoryItem:
        return MemoryItem(
            item_id=string_transform(memory_item.item_id, transforms),
            item_type=string_transform(memory_item.item_type, transforms),
            item_state=memory_item.item_state,
        )


class Constraint(BaseModel):
    constraint_id: str
    constraint: str
    parameters: List[str]
    truth_value: Optional[bool]

    @classmethod
    def transform(
        cls, constraint: Constraint, transforms: List[Transform]
    ) -> Constraint:
        return Constraint(
            constraint_id=string_transform(constraint.constraint_id, transforms),
            constraint=constraint.constraint,
            parameters=[
                string_transform(param, transforms) for param in constraint.parameters
            ],
            truth_value=constraint.truth_value
            if constraint.truth_value is not None
            else True,
        )


class GoalItem(BaseModel):
    goal_name: str
    goal_type: GoalType = GoalType.OPERATOR

    @classmethod
    def transform(cls, goal_item: GoalItem, transforms: List[Transform]) -> GoalItem:
        return GoalItem(
            goal_name=string_transform(goal_item.goal_name, transforms),
            goal_type=goal_item.goal_type,
        )


class GoalItems(BaseModel):
    goals: Union[GoalItem, List[GoalItem]]

    @classmethod
    def transform(cls, goal_items: GoalItems, transforms: List[Transform]) -> GoalItems:
        temp = goal_items.goals
        if not isinstance(temp, List):
            temp = [temp]

        return GoalItems(goals=[goal.transform(goal, transforms) for goal in temp])


class SignatureItem(BaseModel):
    parameters: List[Union[str, MemoryItem]]
    constraints: List[Constraint] = []

    @classmethod
    def transform(
        cls, signature: SignatureItem, transforms: List[Transform]
    ) -> SignatureItem:
        return SignatureItem(
            parameters=[
                string_transform(param, transforms)
                if isinstance(param, str)
                else param.transform(param, transforms)
                for param in signature.parameters
            ],
            constraints=[
                constraint.transform(constraint, transforms)
                for constraint in signature.constraints
            ],
        )


class Outcome(BaseModel):
    constraints: List[Constraint] = []
    outcomes: List[SignatureItem] = []
    probability: Optional[float]

    @classmethod
    def transform(cls, outcome: Outcome, transforms: List[Transform]) -> Outcome:
        return Outcome(
            constraints=[
                constraint.transform(constraint, transforms)
                for constraint in outcome.constraints
            ],
            outcomes=[
                outcome.transform(outcome, transforms) for outcome in outcome.outcomes
            ],
            probability=outcome.probability,
        )


class PartialOrder(BaseModel):
    antecedent: str
    precedent: str

    @classmethod
    def transform(
        cls, partial_order: PartialOrder, transforms: List[Transform]
    ) -> PartialOrder:
        return PartialOrder(
            antecedent=string_transform(partial_order.antecedent, transforms),
            precedent=string_transform(partial_order.precedent, transforms),
        )


class TypeItem(BaseModel):
    name: str
    parent: str = TypeOptions.ROOT.value
    children: Union[str, Set[str]] = set()

    @classmethod
    def transform(cls, type_item: TypeItem, transforms: List[Transform]) -> TypeItem:
        return TypeItem(
            name=string_transform(type_item.name, transforms),
            parent=string_transform(type_item.parent, transforms),
            children=[
                string_transform(child, transforms) for child in type_item.children
            ],
        )


class OperatorDefinition(BaseModel):
    name: str
    cost: int = CostOptions.UNIT.value
    max_try: int = RETRY
    inputs: List[SignatureItem] = []
    outputs: Union[Outcome, List[Outcome]] = []

    @classmethod
    def transform(
        cls, operator: OperatorDefinition, transforms: List[Transform]
    ) -> OperatorDefinition:
        temp = operator.outputs
        if not isinstance(temp, List):
            temp = [temp]

        return OperatorDefinition(
            name=string_transform(operator.name, transforms),
            cost=operator.cost,
            max_try=operator.max_try,
            inputs=[
                signature.transform(signature, transforms)
                for signature in operator.inputs
            ],
            outputs=[output.transform(output, transforms) for output in temp],
        )


class SlotProperty(BaseModel):
    slot_name: str
    slot_desirability: float = SLOT_GOODNESS
    propagate_desirability: bool = False
    do_not_last_resort: bool = False

    @classmethod
    def transform(
        cls, slot_property: SlotProperty, transforms: List[Transform]
    ) -> SlotProperty:
        return SlotProperty(
            slot_name=string_transform(slot_property.slot_name, transforms),
            slot_desirability=slot_property.slot_desirability,
            propagate_desirability=slot_property.propagate_desirability,
            do_not_last_resort=slot_property.do_not_last_resort,
        )

    @validator("slot_desirability")
    def _(cls, value: float) -> float:
        assert 0.0 <= value <= 1.0, "Probability must be between 0 and 1."
        return value


class PDDL(BaseModel):
    domain: str
    problem: str


class FlowDefinition(BaseModel):
    name: str
    operators: List[OperatorDefinition] = []
    type_hierarchy: List[TypeItem] = []
    memory_items: List[MemoryItem] = []
    constraints: List[Constraint] = []
    partial_orders: List[PartialOrder] = []
    list_of_mappings: List[MappingItem] = []
    history: List[HistoricalStep] = []
    slot_properties: List[SlotProperty] = []
    goal_items: List[GoalItems] = []
    starts_with: Optional[str]
    ends_with: Optional[str]

    @classmethod
    def transform(
        cls, flow: FlowDefinition, transforms: List[Transform]
    ) -> FlowDefinition:

        new_flow = FlowDefinition(
            name=string_transform(flow.name, transforms),
            starts_with=string_transform(flow.starts_with, transforms),
            ends_with=string_transform(flow.ends_with, transforms),
        )

        for defn in cls.__fields__.items():
            if "transform" in dir(defn[1].type_):
                setattr(
                    new_flow,
                    defn[0],
                    [
                        item.transform(item, transforms)
                        for item in getattr(flow, defn[0])
                    ],
                )

        return new_flow
