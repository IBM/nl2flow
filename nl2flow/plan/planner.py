from nl2flow.compile.flow import Flow
from nl2flow.compile.utils import Transform, revert_string_transform, revert_string_transforms
from nl2flow.plan.schemas import RawPlan, PlannerResponse, ClassicalPlan as Plan, Action
from nl2flow.plan.options import TIMEOUT
from nl2flow.plan.utils import parse_action, group_items
from nl2flow.compile.schemas import PDDL
from nl2flow.debug.schemas import DebugFlag
from nl2flow.compile.options import (
    PARAMETER_DELIMITER,
    RestrictedOperations,
    SlotOptions,
    MappingOptions,
    ConfirmOptions,
    MemoryState,
    BasicOperations,
    LifeCycleOptions,
)

from abc import ABC, abstractmethod
from typing import Any, List, Set, Optional
from copy import deepcopy


class Planner(ABC):
    def __init__(self) -> None:
        self._timeout: int = TIMEOUT

    @property
    def timeout(self) -> int:
        return self._timeout

    @timeout.setter
    def timeout(self, set_timeout: int) -> None:
        self._timeout = int(set_timeout)

    @abstractmethod
    def plan(self, pddl: PDDL, **kwargs: Any) -> PlannerResponse:
        pass

    @classmethod
    def post_process(cls, planner_response: PlannerResponse, **kwargs: Any) -> PlannerResponse:
        flow_object: Flow = kwargs["flow"]

        slot_options: Set[SlotOptions] = flow_object.slot_options
        mapping_options: Set[MappingOptions] = flow_object.mapping_options
        confirm_options: Set[ConfirmOptions] = flow_object.confirm_options

        for index, plan in enumerate(planner_response.list_of_plans):
            new_plan = deepcopy(plan)

            if SlotOptions.group_slots in slot_options:
                new_plan = group_items(new_plan, SlotOptions.group_slots)

            if MappingOptions.group_maps in mapping_options:
                new_plan = group_items(new_plan, MappingOptions.group_maps)

            if ConfirmOptions.group_confirms in confirm_options:
                new_plan = group_items(new_plan, ConfirmOptions.group_confirms)

            new_plan.length = len(new_plan.plan)
            planner_response.list_of_plans[index] = new_plan

        return planner_response


class FDDerivedPlanner(ABC):
    @classmethod
    def parse(cls, raw_plans: List[RawPlan], **kwargs: Any) -> List[Plan]:
        list_of_plans = list()

        flow_object: Flow = kwargs["flow"]
        debug_flag: Optional[DebugFlag] = kwargs.get("debug_flag", None)
        transforms: List[Transform] = kwargs.get("transforms", [])

        for plan in raw_plans:
            new_plan = Plan(cost=plan.cost, reference=plan.actions)
            actions = plan.actions

            # TODO: Temporary till state tracking, ISS134
            cached_items = []
            for memory_item in flow_object.flow_definition.memory_items:
                if memory_item.item_state == MemoryState.KNOWN:
                    cached_items.append(memory_item.item_id)

            for action in actions:
                action_split = action.split()
                name_token = action_split[0]

                if PARAMETER_DELIMITER in name_token:
                    temp_split = name_token.split(PARAMETER_DELIMITER)
                    name_token = temp_split[0]
                    parameters = temp_split[1:]

                else:
                    parameters = action_split[1:]

                if debug_flag == DebugFlag.DIRECT:
                    if name_token.startswith(RestrictedOperations.TOKENIZE.value):
                        name_token = name_token.split("//")[-1]

                action_name = revert_string_transform(name_token, transforms)

                if action_name is not None:
                    new_action = parse_action(
                        action_name=action_name,
                        parameters=revert_string_transforms(parameters, transforms),
                        flow_object=flow_object,
                        transforms=transforms,
                        debug_flag=debug_flag,
                    )
                else:
                    raise ValueError("Could not parse action name.")

                if new_action:
                    # TODO: Temporary till state tracking, ISS134
                    if isinstance(new_action, Action):
                        cache_known_items(new_action, cached_items, **kwargs)

                    new_plan.plan.append(new_action)

            new_plan.length = len(new_plan.plan)
            list_of_plans.append(new_plan)

        return list_of_plans


def cache_known_items(new_action: Action, cached_items: List[str], **kwargs: Any) -> None:
    flow_object: Flow = kwargs["flow"]
    debug_flag: Optional[DebugFlag] = kwargs.get("debug_flag", None)

    if BasicOperations.is_basic(new_action.name):
        if new_action.name.startswith(BasicOperations.SLOT_FILLER.value):
            if LifeCycleOptions.confirm_on_slot not in flow_object.variable_life_cycle:
                cached_items.extend(new_action.inputs)

        elif new_action.name.startswith(BasicOperations.CONFIRM.value):
            cached_items.extend(new_action.inputs)

        elif new_action.name.startswith(BasicOperations.MAPPER.value):
            if LifeCycleOptions.confirm_on_mapping not in flow_object.variable_life_cycle:
                cached_items.extend(new_action.inputs)

    else:
        new_inputs = []
        new_parameters = []

        for index, item in enumerate(new_action.inputs):
            if item in cached_items:
                new_inputs.append(item)

                if new_action.parameters and debug_flag == DebugFlag.DIRECT:
                    new_parameters.append(new_action.parameters[index])

        new_action.parameters = new_parameters or new_action.parameters
        new_action.inputs = new_inputs

        if LifeCycleOptions.confirm_on_determination not in flow_object.variable_life_cycle:
            cached_items.extend(new_action.outputs)

        if LifeCycleOptions.uncertain_on_use in flow_object.variable_life_cycle:
            for item in new_action.inputs:
                cached_items = [ci for ci in cached_items if ci != item]
