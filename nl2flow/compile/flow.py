from typing import Set, List, Union, Any, Tuple
from nl2flow.plan.schemas import PlannerResponse
from nl2flow.compile.compilations import ClassicPDDL
from nl2flow.compile.operators import Operator
from nl2flow.compile.schemas import TypeItem, FlowDefinition, PDDL, Transform
from nl2flow.compile.validators.flow_validator import FlowValidator
from nl2flow.compile.options import (
    CompileOptions,
    SlotOptions,
    MappingOptions,
    LifeCycleOptions,
    GoalOptions,
    LOOKAHEAD,
    RETRY,
)


class Flow:
    def __init__(self, name: str):
        self.flow_definition = FlowDefinition(name=name)
        self._mapping_option: Set[MappingOptions] = {MappingOptions.relaxed}
        self._variable_life_cycle: Set[LifeCycleOptions] = set()
        self._slot_options: Set[SlotOptions] = {
            SlotOptions.higher_cost,
            SlotOptions.relaxed,
        }

    @property
    def variable_life_cycle(self) -> Set[LifeCycleOptions]:
        return self._variable_life_cycle

    @variable_life_cycle.setter
    def variable_life_cycle(self, options: Set[LifeCycleOptions]) -> None:
        assert all(
            [isinstance(option, LifeCycleOptions) for option in options]
        ), "Tried to set unknown lifecycle option."

        self._variable_life_cycle = options

    @property
    def mapping_options(self) -> Set[MappingOptions]:
        return self._mapping_option

    @mapping_options.setter
    def mapping_options(self, options: Set[MappingOptions]) -> None:
        assert all(
            [isinstance(option, SlotOptions) for option in options]
        ), "Tried to set unknown mapping option."

        exclusive_set = {
            MappingOptions.relaxed,
            MappingOptions.immediate,
            MappingOptions.eventual,
        }
        assert (
            len(exclusive_set & options) == 1
        ), f"Cannot have more than one of {', '.join([e.value for e in exclusive_set])} among mapping options."

        self._mapping_option = options

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
            if issubclass(type(item), Operator):
                item = item.definition

            type_of_item = type(item).__name__
            key_name = next(
                (
                    defn[0]
                    for defn in FlowDefinition.__fields__.items()
                    if defn[1].type_.__name__ == type_of_item
                ),
                None,
            )

            if type_of_item == TypeItem.__name__ and item.children:
                children = item.children

                if not isinstance(children, Set):
                    children = {children}

                for child in children:
                    self.add(TypeItem(name=child, parent=item.name, children=[]))

            if key_name:

                temp = getattr(self.flow_definition, key_name)
                temp.append(item)
                setattr(self.flow_definition, key_name, temp)

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

    def plan_it(
        self,
        planner: Any,
        goal_type: GoalOptions = GoalOptions.AND,
        lookahead: int = LOOKAHEAD,
        compilation_type: CompileOptions = CompileOptions.CLASSICAL,
    ) -> PlannerResponse:

        pddl, transforms = self.compile_to_pddl(goal_type, lookahead, compilation_type)

        raw_plans = planner.plan(pddl=pddl)
        parsed_plans: PlannerResponse = planner.parse(
            response=raw_plans, flow=self, transforms=transforms
        )

        return parsed_plans

    def compile_to_pddl(
        self,
        goal_type: GoalOptions = GoalOptions.AND,
        lookahead: int = LOOKAHEAD,
        retry: int = RETRY,
        multi_instance: bool = True,
        compilation_type: CompileOptions = CompileOptions.CLASSICAL,
    ) -> Tuple[PDDL, List[Transform]]:

        assert isinstance(
            goal_type, GoalOptions
        ), "Goals are either AND-ORs or OR-ANDs."

        assert isinstance(
            compilation_type, CompileOptions
        ), "Encountered unknown compilation option."

        assert type(lookahead) == int, "Length of lookahead must be an integer."

        if compilation_type.value != CompileOptions.CLASSICAL.value:
            raise NotImplementedError

        # assert self.validate(), "Invalid Flow definition!"
        compilation = ClassicPDDL(self.flow_definition)
        pddl, transforms = compilation.compile(
            slot_options=self.slot_options,
            mapping_options=self.mapping_options,
            variable_life_cycle=self.variable_life_cycle,
            goal_type=goal_type,
            lookahead=lookahead,
            retry=retry,
            multi_instance=multi_instance,
        )

        return pddl, transforms
