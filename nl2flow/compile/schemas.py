from __future__ import annotations
from typing import Set, List, Dict, Optional, Union, Any
from collections import Counter
from re import findall
from pydantic import BaseModel, field_validator, model_validator, ConfigDict
from pydantic_core.core_schema import FieldValidationInfo
from nl2flow.compile.utils import string_transform, revert_string_transform, Transform
from nl2flow.compile.options import (
    TypeOptions,
    CostOptions,
    GoalType,
    MemoryState,
    SLOT_GOODNESS,
    RETRY,
)


class Parameter(BaseModel):
    item_id: str
    item_type: Optional[str] = None

    @classmethod
    def transform(cls, parameter: Parameter, transforms: List[Transform]) -> Parameter:
        return Parameter(
            item_id=string_transform(parameter.item_id, transforms),
            item_type=string_transform(parameter.item_type, transforms)
            if parameter.item_type is not None
            else TypeOptions.ROOT.value,
        )


class Step(BaseModel):
    name: str
    parameters: List[Union[Parameter, str]] = []

    @classmethod
    def transform(cls, step: Step, transforms: List[Transform]) -> Step:
        parameters = [p if isinstance(p, Parameter) else Parameter(item_id=p) for p in step.parameters]
        return Step(
            name=string_transform(step.name, transforms),
            parameters=[p.transform(p, transforms) for p in parameters],
        )


class MappingItem(BaseModel):
    source_name: str
    target_name: str
    probability: float = 1.0

    @classmethod
    def transform(cls, mapping_item: MappingItem, transforms: List[Transform]) -> MappingItem:
        return MappingItem(
            source_name=string_transform(mapping_item.source_name, transforms),
            target_name=string_transform(mapping_item.target_name, transforms),
            probability=mapping_item.probability,
        )

    @field_validator("probability")
    @classmethod
    def probability_within_range(cls, value: float) -> float:
        assert 0.0 <= value <= 1.0, "Probability must be between 0 and 1."
        return value


class MemoryItem(Parameter):
    item_state: MemoryState = MemoryState.UNKNOWN

    @classmethod
    def transform(cls, memory_item: MemoryItem, transforms: List[Transform]) -> MemoryItem:
        return MemoryItem(
            item_id=string_transform(memory_item.item_id, transforms),
            item_type=string_transform(memory_item.item_type, transforms),
            item_state=memory_item.item_state,
        )


class Constraint(BaseModel):
    constraint: str
    truth_value: Optional[bool] = None

    @classmethod
    def transform(cls, constraint: Constraint, transforms: List[Transform]) -> Constraint:
        return Constraint(
            constraint=string_transform(constraint.constraint, transforms, hashit=True),
            truth_value=constraint.truth_value if constraint.truth_value is not None else True,
        )

    @staticmethod
    def get_variable_references_from_constraint(constraint: str, transforms: List[Transform]) -> List[str]:
        revert_constraint = revert_string_transform(constraint, transforms) if transforms else constraint
        raw_references = findall(r"[^$]*(\$[a-zA-Z\d_]*)*[^$]*", revert_constraint or "")
        references = [r.replace("$", "").strip() for r in raw_references if r]
        return references


class ManifestConstraint(BaseModel):
    manifest: Constraint
    constraint: Constraint

    @classmethod
    def transform(cls, manifest_constraint: ManifestConstraint, transforms: List[Transform]) -> ManifestConstraint:
        return ManifestConstraint(
            manifest=manifest_constraint.manifest.transform(manifest_constraint.manifest, transforms),
            constraint=manifest_constraint.constraint.transform(manifest_constraint.constraint, transforms),
        )


class GoalItem(BaseModel):
    goal_name: Union[str, Step, Constraint]
    goal_type: GoalType = GoalType.OPERATOR

    @classmethod
    def transform(cls, goal_item: GoalItem, transforms: List[Transform]) -> GoalItem:
        goal = goal_item.goal_name
        return GoalItem(
            goal_name=string_transform(goal, transforms) if isinstance(goal, str) else goal.transform(goal, transforms),
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
    parameters: Union[str, Parameter, MemoryItem, List[Union[str, MemoryItem, Parameter]]] = []
    constraints: List[Constraint] = []

    @classmethod
    def transform(cls, signature: SignatureItem, transforms: List[Transform]) -> SignatureItem:
        parameters = signature.parameters if isinstance(signature.parameters, List) else [signature.parameters]
        return SignatureItem(
            parameters=[
                string_transform(param, transforms) if isinstance(param, str) else param.transform(param, transforms)
                for param in parameters
            ],
            constraints=[constraint.transform(constraint, transforms) for constraint in signature.constraints],
        )


class Outcome(BaseModel):
    conditions: List[Any] = []
    constraints: List[Constraint] = []
    outcomes: List[SignatureItem] = []
    probability: Optional[float] = None

    @classmethod
    def transform(cls, outcome: Outcome, transforms: List[Transform]) -> Outcome:
        return Outcome(
            conditions=outcome.conditions,
            constraints=[constraint.transform(constraint, transforms) for constraint in outcome.constraints],
            outcomes=[outcome.transform(outcome, transforms) for outcome in outcome.outcomes],
            probability=outcome.probability,
        )


class PartialOrder(BaseModel):
    antecedent: str
    consequent: str

    @classmethod
    def transform(cls, partial_order: PartialOrder, transforms: List[Transform]) -> PartialOrder:
        return PartialOrder(
            antecedent=string_transform(partial_order.antecedent, transforms),
            consequent=string_transform(partial_order.consequent, transforms),
        )


class TypeItem(BaseModel):
    name: str
    parent: Optional[str] = TypeOptions.ROOT.value
    children: Union[str, Set[str]] = set()

    @classmethod
    def transform(cls, type_item: TypeItem, transforms: List[Transform]) -> TypeItem:
        return TypeItem(
            name=string_transform(type_item.name, transforms),
            parent=string_transform(type_item.parent, transforms),
            children=[string_transform(child, transforms) for child in type_item.children],
        )


class OperatorDefinition(BaseModel):
    name: str
    cost: int = CostOptions.UNIT.value
    max_try: int = RETRY
    inputs: List[SignatureItem] = []
    outputs: Union[Outcome, List[Outcome]] = []

    @classmethod
    def transform(cls, operator: OperatorDefinition, transforms: List[Transform]) -> OperatorDefinition:
        temp = operator.outputs
        if not isinstance(temp, List):
            temp = [temp]

        return OperatorDefinition(
            name=string_transform(operator.name, transforms),
            cost=operator.cost,
            max_try=operator.max_try,
            inputs=[signature.transform(signature, transforms) for signature in operator.inputs],
            outputs=[output.transform(output, transforms) for output in temp],
        )


class SlotProperty(BaseModel):
    slot_name: str
    slot_desirability: float = SLOT_GOODNESS
    propagate_desirability: bool = False
    do_not_last_resort: bool = False

    @classmethod
    def transform(cls, slot_property: SlotProperty, transforms: List[Transform]) -> SlotProperty:
        return SlotProperty(
            slot_name=string_transform(slot_property.slot_name, transforms),
            slot_desirability=slot_property.slot_desirability,
            propagate_desirability=slot_property.propagate_desirability,
            do_not_last_resort=slot_property.do_not_last_resort,
        )

    @field_validator("slot_desirability")
    @classmethod
    def desirability_is_a_probability(cls, value: float) -> float:
        assert 0.0 <= value <= 1.0, "Probability must be between 0 and 1."
        return value


class PDDL(BaseModel):
    domain: str
    problem: str


class ClassicalPlanReference(BaseModel):
    plan: List[Union[Step, Constraint]] = []

    @classmethod
    def transform(cls, reference: ClassicalPlanReference, transforms: List[Transform]) -> ClassicalPlanReference:
        return ClassicalPlanReference(plan=[item.transform(item, transforms) for item in reference.plan])


class FlowDefinition(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    name: str
    type_hierarchy: List[TypeItem] = []
    operators: List[OperatorDefinition] = []
    goal_items: List[GoalItems] = []
    history: List[Step] = []
    constraints: List[Constraint] = []
    memory_items: List[MemoryItem] = []
    slot_properties: List[SlotProperty] = []
    list_of_mappings: List[MappingItem] = []
    partial_orders: List[PartialOrder] = []
    manifest_constraints: List[ManifestConstraint] = []
    starts_with: Optional[str] = None
    ends_with: Optional[str] = None
    reference: Optional[ClassicalPlanReference] = None

    @classmethod
    def transform(cls, flow: FlowDefinition, transforms: List[Transform]) -> FlowDefinition:
        new_flow = FlowDefinition(
            name=string_transform(flow.name, transforms),
            reference=flow.reference.transform(flow.reference, transforms) if flow.reference else None,
        )

        for defn in cls.model_fields.items():
            if defn[0] not in ["name", "starts_with", "ends_with", "reference"]:
                setattr(
                    new_flow,
                    defn[0],
                    [item.transform(item, transforms) for item in getattr(flow, defn[0])],
                )

        new_flow.starts_with = string_transform(flow.starts_with, transforms)
        new_flow.ends_with = string_transform(flow.ends_with, transforms)

        return new_flow

    @field_validator("starts_with", "ends_with")
    @classmethod
    def unknown_operator(cls, operator_name: str, info: FieldValidationInfo) -> str:
        reference_flow_model = FlowDefinition.model_validate(info.data)
        assert operator_name is None or operator_name in map(
            lambda x: str(x.name), reference_flow_model.operators
        ), "Operator name not found!"

        return operator_name

    @model_validator(mode="after")
    def no_duplicate_items(self) -> FlowDefinition:
        check_list_key = ["operators", "type_hierarchy"]
        for key in check_list_key:
            list_of_items = list(
                map(
                    lambda x: str(getattr(x, "name")),
                    getattr(self, key),
                )
            )

            duplicate_list = self.get_duplicates(list_of_items)
            assert len(duplicate_list) == 0, f"Duplicate names for {key=} {', '.join(duplicate_list)}."

        return self

    @model_validator(mode="after")
    def hash_conflicts(self) -> FlowDefinition:
        transforms: List[Transform] = list()

        reference_list_of_objects = self.get_list_of_object_names(self)
        reference_keys = list(reference_list_of_objects.keys())

        check_list_key = {
            "operators": "name",
            "type_hierarchy": "name",
            "constraints": "constraint",
            "history": "name",
        }

        for key in check_list_key:
            list_of_items = list(
                map(
                    lambda x: str(getattr(x, check_list_key[key])),
                    getattr(self, key),
                )
            )

            for item in list_of_items:
                if item and item not in reference_keys:
                    reference_keys.append(item)

        transformed_keys = [string_transform(item, transforms) for item in reference_keys]

        for item in reference_keys:
            transformed_item = string_transform(item, transforms)

            if transformed_item is not None:
                members = [o for o in transformed_keys if transformed_item == o]
                assert len(members) <= 1, f"Conflicting names for {transformed_item}."

        return self

    @model_validator(mode="after")
    def object_type_conflict(self) -> FlowDefinition:
        list_of_object_names = self.get_list_of_object_names(self)
        for item in list_of_object_names:
            type_set = list_of_object_names[item]
            assert len(type_set) <= 1, f"Object {item} has more than one type: {', '.join(type_set)}."

        return self

    @model_validator(mode="after")
    def mappings_are_among_known_memory_items(self) -> FlowDefinition:
        list_of_object_names = self.get_list_of_object_names(self)

        for mapping in self.list_of_mappings:
            for item in [mapping.source_name, mapping.target_name]:
                assert item in list_of_object_names, f"Mapping request with {item} unknown."

        return self

    @model_validator(mode="after")
    def slots_are_among_known_memory_items(self) -> FlowDefinition:
        list_of_object_names = self.get_list_of_object_names(self)

        for slot in self.slot_properties:
            assert slot.slot_name in list_of_object_names, f"Slot request with {slot.slot_name} unknown."

        return self

    @staticmethod
    def get_duplicates(list_item: List[str]) -> List[str]:
        return [i for i, c in Counter(list_item).items() if c > 1]

    @staticmethod
    def update_object_map(
        list_of_objects: Dict[str, Set[str]], object_name: str, object_type: Optional[str] = None
    ) -> None:
        if object_name not in list_of_objects:
            if object_type:
                list_of_objects[object_name] = {object_type}
            else:
                list_of_objects[object_name] = set()
        else:
            if object_type:
                list_of_objects[object_name].add(object_type)

    @classmethod
    def signature_parser(cls, list_of_objects: Dict[str, Set[str]], signature_item: SignatureItem) -> None:
        parameters = (
            signature_item.parameters if isinstance(signature_item.parameters, List) else [signature_item.parameters]
        )

        for parameter in parameters:
            parameter_name = parameter.item_id if isinstance(parameter, Parameter) else parameter
            parameter_type = parameter.item_type if isinstance(parameter, Parameter) else None

            cls.update_object_map(list_of_objects, parameter_name, parameter_type)

        for constraint in signature_item.constraints:
            cls.constraint_parser(list_of_objects, constraint)

    @classmethod
    def constraint_parser(cls, list_of_objects: Dict[str, Set[str]], constraint: Constraint) -> None:
        cls.update_object_map(list_of_objects, constraint.constraint, None)
        constraint_parameters = constraint.get_variable_references_from_constraint(constraint.constraint, [])
        for p in constraint_parameters:
            cls.update_object_map(list_of_objects, p, None)

    @classmethod
    def get_list_of_object_names(cls, flow: FlowDefinition) -> Dict[str, Set[str]]:
        list_of_objects: Dict[str, Set[str]] = dict()
        for item in flow.memory_items:
            cls.update_object_map(list_of_objects, item.item_id, item.item_type)

        for item in flow.goal_items:
            goals: List[GoalItem] = item.goals if isinstance(item.goals, List) else [item.goals]
            for goal in goals:
                if (
                    goal.goal_type != GoalType.OPERATOR
                    and goal.goal_type != GoalType.CONSTRAINT
                    and not isinstance(goal.goal_name, Step)
                    and goal.goal_name not in [t.name for t in flow.type_hierarchy]
                ):
                    cls.update_object_map(list_of_objects, goal.goal_name, None)

                elif goal.goal_type == GoalType.OPERATOR and isinstance(goal.goal_name, Step):
                    for param in goal.goal_name.parameters:
                        cls.update_object_map(
                            list_of_objects,
                            param.item_id if isinstance(param, Parameter) else param,
                            None,
                        )

                elif isinstance(goal.goal_name, Constraint):
                    for param in goal.goal_name.get_variable_references_from_constraint(goal.goal_name.constraint, []):
                        cls.update_object_map(list_of_objects, param)

        for operator in flow.operators:
            for item in operator.inputs:
                cls.signature_parser(list_of_objects, item)

            outputs = operator.outputs
            if not isinstance(outputs, List):
                outputs = [outputs]

            for output in outputs:
                for item in output.constraints:
                    cls.constraint_parser(list_of_objects, item)

                for item in output.outcomes:
                    cls.signature_parser(list_of_objects, item)

        return list_of_objects
