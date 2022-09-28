from typing import Set, List, Union, Any
from nl2flow.compile.compilations import ClassicPDDL
from nl2flow.compile.schemas import TypeItem, FlowDefinition, PDDL
from nl2flow.compile.validators.flow_validator import FlowValidator
from nl2flow.compile.options import (
    CompileOptions,
    SlotOptions,
    MappingOptions,
    LifeCycleOptions,
    GoalOptions,
    LOOKAHEAD,
)


class Flow:
    def __init__(self, name: str):
        self.flow_definition = FlowDefinition(name=name)
        self._slot_options = {SlotOptions.higher_cost}
        self._mapping_option = MappingOptions.relaxed
        self._variable_life_cycle = LifeCycleOptions.bistate

    @property
    def variable_life_cycle(self) -> LifeCycleOptions:
        return self._variable_life_cycle

    @variable_life_cycle.setter
    def variable_life_cycle(self, option: LifeCycleOptions) -> None:
        assert isinstance(
            option, LifeCycleOptions
        ), "Tried to set unknown variable lifecycle type."
        self._variable_life_cycle = option

    @property
    def mapping_option(self) -> MappingOptions:
        return self._mapping_option

    @mapping_option.setter
    def mapping_option(self, option: MappingOptions) -> None:
        assert isinstance(
            option, MappingOptions
        ), "Tried to set unknown mapping option."
        self._mapping_option = option

    @property
    def slot_options(self) -> Set[SlotOptions]:
        return self._slot_options

    @slot_options.setter
    def slot_options(self, options: Set[SlotOptions]) -> None:
        assert all(
            [isinstance(option, SlotOptions) for option in options]
        ), "Tried to set unknown slot option."

        inclusive_set = {SlotOptions.higher_cost, SlotOptions.last_resort}
        assert (
            len(inclusive_set & options) >= 1
        ), f"Must have at least one of {', '.join([e.value for e in inclusive_set])} among slot options."

        exclusive_set = {
            SlotOptions.relaxed,
            SlotOptions.immediate,
            SlotOptions.eventual,
        }
        assert (
            len(exclusive_set & options) == 1
        ), f"Cannot have more than one of {', '.join([e.value for e in exclusive_set])} among slot options."

        self._slot_options = options

    def validate(self) -> bool:
        validate: bool = FlowValidator.test_all(self.flow_definition)
        return validate

    def add(self, new_item: Union[Any, List[Any]]) -> None:

        if not isinstance(new_item, List):
            new_item = [new_item]

        for item in new_item:
            type_of_item = type(item).__name__
            key_name = next(
                (
                    defn[0]
                    for defn in FlowDefinition.__fields__.items()
                    if defn[1].type_.__name__ == type_of_item
                ),
                None,
            )

            if type_of_item == TypeItem and item.children:
                children = item.children

                if not isinstance(children, Set):
                    children = {children}

                for child in children:
                    self.add(TypeItem(name=child, parent=item.name, children=[]))

            if key_name:
                eval(f"self.flow_definition.{key_name}.append(item)")
            else:
                raise TypeError("Attempted to add unknown type of object to flow.")

    def set_start(self, operator_name: str) -> None:
        assert operator_name in map(
            lambda x: str(x.name), self.flow_definition.operators
        ), "Operator name not found!"
        self.flow_definition.starts_with = operator_name

    def set_end(self, operator_name: str) -> None:
        assert operator_name in map(
            lambda x: str(x.name), self.flow_definition.operators
        ), "Operator name not found!"
        self.flow_definition.ends_with = operator_name

    def get_flow_definition(self) -> FlowDefinition:
        return self.flow_definition

    def compile_to_pddl(
        self,
        goal_type: GoalOptions,
        lookahead: int = LOOKAHEAD,
        compilation_type: CompileOptions = CompileOptions.CLASSICAL,
    ) -> PDDL:

        assert isinstance(
            goal_type, GoalOptions
        ), "Goals are either AND-ORs or OR-ANDs."

        assert isinstance(
            compilation_type, CompileOptions
        ), "Encountered unknown compilation option."

        assert type(lookahead) == int, "Length of lookahead must be an integer."

        if compilation_type.value != CompileOptions.CLASSICAL:
            raise NotImplementedError

        assert self.validate(), "Invalid Flow definition!"

        compilation = ClassicPDDL(self.flow_definition)
        return compilation.compile(
            slot_options=self.slot_options,
            mapping_option=self.mapping_option,
            variable_life_cycle=self.variable_life_cycle,
            goal_type=goal_type,
            lookahead=lookahead,
        )
