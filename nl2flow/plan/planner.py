from nl2flow.compile.flow import Flow
from nl2flow.compile.utils import Transform, revert_string_transform, revert_string_transforms
from nl2flow.plan.schemas import RawPlan, PlannerResponse, ClassicalPlan as Plan
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
                    new_plan.plan.append(new_action)

            new_plan.length = len(new_plan.plan)
            list_of_plans.append(new_plan)

        return list_of_plans
