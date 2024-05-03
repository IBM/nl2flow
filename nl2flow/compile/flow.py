from typing import Set, List, Union, Any, Tuple, Dict, Optional
from nl2flow.plan.schemas import PlannerResponse
from nl2flow.compile.compilations import ClassicPDDL
from nl2flow.compile.operators import Operator
from nl2flow.compile.schemas import TypeItem, FlowDefinition, PDDL, ClassicalPlanReference, Transform
from nl2flow.debug.schemas import SolutionQuality
from nl2flow.compile.options import (
    CompileOptions,
    SlotOptions,
    MappingOptions,
    ConfirmOptions,
    LifeCycleOptions,
    GoalOptions,
    NL2FlowOptions,
    LOOKAHEAD,
)


class Flow:
    def __init__(
        self,
        name: str,
    ):
        self._flow_definition = FlowDefinition(name=name)
        self._mapping_option: Set[MappingOptions] = {MappingOptions.relaxed}
        self._confirm_option: Set[ConfirmOptions] = set()
        self._variable_life_cycle: Set[LifeCycleOptions] = set()
        self._goal_type = GoalOptions.AND_AND
        self._lookahead: int = LOOKAHEAD
        self._optimization_options: Set[NL2FlowOptions] = {NL2FlowOptions.multi_instance, NL2FlowOptions.allow_retries}
        self._slot_options: Set[SlotOptions] = {
            SlotOptions.higher_cost,
            SlotOptions.relaxed,
        }

        self._compilation: ClassicPDDL = ClassicPDDL(self.flow_definition)

    @property
    def compilation(self) -> ClassicPDDL:
        return self._compilation

    @property
    def variable_life_cycle(self) -> Set[LifeCycleOptions]:
        return self._variable_life_cycle

    @variable_life_cycle.setter
    def variable_life_cycle(self, options: Set[LifeCycleOptions]) -> None:
        self._variable_life_cycle = options

    @property
    def confirm_options(self) -> Set[ConfirmOptions]:
        return self._confirm_option

    @confirm_options.setter
    def confirm_options(self, options: Set[ConfirmOptions]) -> None:
        self._confirm_option = options

    @property
    def mapping_options(self) -> Set[MappingOptions]:
        return self._mapping_option

    @mapping_options.setter
    def mapping_options(self, options: Set[MappingOptions]) -> None:
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

    @property
    def goal_type(self) -> GoalOptions:
        return self._goal_type

    @goal_type.setter
    def goal_type(self, goal_type: GoalOptions) -> None:
        self._goal_type = goal_type

    @property
    def lookahead(self) -> int:
        return self._lookahead

    @lookahead.setter
    def lookahead(self, lookahead: int) -> None:
        self._lookahead = lookahead

    @property
    def optimization_options(self) -> Set[NL2FlowOptions]:
        return self._optimization_options

    @optimization_options.setter
    def optimization_options(self, options: Set[NL2FlowOptions]) -> None:
        self._optimization_options = options

    @property
    def flow_definition(self) -> FlowDefinition:
        return self._flow_definition

    @flow_definition.setter
    def flow_definition(self, initialize: Union[FlowDefinition, Dict[str, Any]]) -> None:
        if isinstance(initialize, Dict):
            self._flow_definition = FlowDefinition.model_validate(initialize)

        elif isinstance(initialize, FlowDefinition):
            self._flow_definition = initialize

        else:
            raise TypeError(f"Tried to initialize with unknown object: {initialize}")

    def add(self, new_item: Union[Any, List[Any]]) -> None:
        if not isinstance(new_item, List):
            new_item = [new_item]

        for item in new_item:
            if issubclass(type(item), Operator):
                item = item.definition

            type_of_item = type(item).__name__
            key_name = next(
                (field[0] for field in FlowDefinition.model_fields.items() if type_of_item in str(field[1].annotation)),
                None,
            )

            if key_name:
                current_item_value = getattr(self.flow_definition, key_name)

                if isinstance(current_item_value, List):
                    current_item_value.append(item)
                    setattr(self.flow_definition, key_name, current_item_value)

                    if type_of_item == TypeItem.__name__ and item.children:
                        children = item.children

                        if not isinstance(children, Set):
                            children = {children}

                        for child in children:
                            self.add(TypeItem(name=child, parent=item.name, children=[]))

                elif isinstance(item, ClassicalPlanReference):
                    setattr(self.flow_definition, key_name, item)
            else:
                raise TypeError("Attempted to add unknown type of object to flow.")

    def set_start(self, operator_name: Optional[str]) -> None:
        self.flow_definition.starts_with = operator_name

    def set_end(self, operator_name: Optional[str]) -> None:
        self.flow_definition.ends_with = operator_name

    def plan_it(
        self,
        planner: Any,
        debug_flag: Optional[SolutionQuality] = None,
        compilation_type: CompileOptions = CompileOptions.CLASSICAL,
    ) -> PlannerResponse:
        pddl, transforms = self.compile_to_pddl(debug_flag, compilation_type)
        parsed_plans: PlannerResponse = planner.plan(pddl=pddl, flow=self, transforms=transforms)
        return parsed_plans

    def compile_to_pddl(
        self,
        debug_flag: Optional[SolutionQuality] = None,
        compilation_type: CompileOptions = CompileOptions.CLASSICAL,
    ) -> Tuple[PDDL, List[Transform]]:
        if compilation_type.value != CompileOptions.CLASSICAL.value:
            raise NotImplementedError

        self._compilation = ClassicPDDL(self.flow_definition)
        pddl, transforms = self._compilation.compile(
            slot_options=self.slot_options,
            mapping_options=self.mapping_options,
            confirm_options=self.confirm_options,
            variable_life_cycle=self.variable_life_cycle,
            optimization_options=self.optimization_options,
            goal_type=self.goal_type,
            lookahead=self.lookahead,
            debug_flag=debug_flag,
        )

        return pddl, transforms
