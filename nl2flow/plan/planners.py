from nl2flow.compile.flow import Flow
from nl2flow.compile.utils import revert_string_transform
from nl2flow.plan.schemas import PlannerResponse, ClassicalPlan, Action, Parameter
from nl2flow.plan.options import TIMEOUT
from nl2flow.compile.options import (
    BasicOperations,
    TypeOptions,
    SlotOptions,
    MappingOptions,
    ConfirmOptions,
)
from nl2flow.compile.schemas import (
    PDDL,
    OperatorDefinition,
    MemoryItem,
    SignatureItem,
)

from abc import ABC, abstractmethod
from typing import Any, List, Set, Dict, Union

import requests
import re


def parse_action(
    action_name: str,
    parameters: List[str],
    **kwargs: Dict[str, Any],
) -> Action:
    def __add_parameters(signatures: List[SignatureItem]) -> List[SignatureItem]:
        list_of_parameters: List[SignatureItem] = list()

        for signature_item in signatures:
            for parameter in signature_item.parameters:

                if isinstance(parameter, MemoryItem):
                    list_of_parameters.append(
                        Parameter(
                            name=parameter.item_id,
                            type=parameter.item_type or TypeOptions.ROOT.value,
                        )
                    )

                elif isinstance(parameter, str):

                    find_in_memory = list(
                        filter(
                            lambda x: x.item_id == parameter,
                            flow.flow_definition.memory_items,
                        )
                    )

                    if find_in_memory:
                        memory_item: MemoryItem = find_in_memory[0]
                        list_of_parameters.append(
                            Parameter(
                                name=memory_item.item_id, type=memory_item.item_type
                            )
                        )

                    else:
                        list_of_parameters.append(
                            Parameter(name=parameter, type=TypeOptions.ROOT.value)
                        )

        return list_of_parameters

    new_action = Action(name=action_name)
    flow: Flow = kwargs["flow"]

    if any([action_name.startswith(item.value) for item in BasicOperations]):

        if action_name.startswith(
            BasicOperations.SLOT_FILLER.value
        ) or action_name.startswith(BasicOperations.MAPPER.value):

            temp = action_name.split("----")
            new_action.name = temp[0]

            if temp[1:] and not parameters:
                parameters = temp[1:]

        new_action.inputs = [
            Parameter(
                name=revert_string_transform(param, kwargs["transforms"]),
                type=TypeOptions.ROOT.value,
            )
            for param in parameters
        ]

    else:
        operator: OperatorDefinition = list(
            filter(lambda x: x.name == action_name, flow.flow_definition.operators)
        )[0]

        new_action.inputs = __add_parameters(operator.inputs)
        new_action.outputs = __add_parameters(operator.outputs.outcomes)

    return new_action


class Planner(ABC):
    @abstractmethod
    def plan(self, pddl: PDDL, **kwargs: Dict[str, Any]) -> Any:
        pass

    @abstractmethod
    def parse(self, response: Any, **kwargs: Dict[str, Any]) -> PlannerResponse:
        pass

    @staticmethod
    def group_items(
        plan: ClassicalPlan,
        flow: Flow,
        option: Union[SlotOptions, MappingOptions, ConfirmOptions],
    ) -> ClassicalPlan:

        if option == SlotOptions.group_slots:
            action_name = BasicOperations.SLOT_FILLER.value

        elif option == MappingOptions.group_maps:
            action_name = BasicOperations.MAPPER.value

        elif option == ConfirmOptions.group_confirms:
            action_name = BasicOperations.CONFIRM.value

        else:
            raise TypeError("Unknown grouping option.")

        new_action = Action(name=action_name)
        new_plan = ClassicalPlan(
            cost=plan.cost,
            length=plan.length,
            metadata=plan.metadata,
        )

        new_start_of_plan = 0
        for index, action in enumerate(plan.plan):

            if action.name == action_name:
                new_action.inputs.extend(action.inputs)

            else:
                new_start_of_plan = index
                break

        new_plan.plan = (
            [new_action] + plan.plan[new_start_of_plan:]
            if new_start_of_plan
            else plan.plan
        )
        return new_plan

    @staticmethod
    def pretty_print(planner_response: PlannerResponse) -> str:
        pretty = ""

        for index, plan in enumerate(planner_response.list_of_plans):
            pretty += f"\n\n---- Plan #{index} ----\n"
            pretty += f"Cost: {plan.cost}, Length: {plan.length}\n\n"

            for step, action in enumerate(plan.plan):
                inputs = ", ".join(
                    [f"{item.name} ({item.type})" for item in action.inputs]
                )
                outputs = ", ".join(
                    [f"{item.name} ({item.type})" for item in action.outputs]
                )

                pretty += (
                    f"Step {step}: {action.name}, "
                    f"Inputs: {inputs if action.inputs else None}, "
                    f"Outputs: {outputs if action.outputs else None}\n"
                )

        return pretty


class RemotePlanner(ABC):
    def __init__(self, url: str, timeout: int = TIMEOUT):
        self.url = url
        self.timeout = timeout

    def call_remote_planner(self, payload: Dict[str, Any]) -> requests.models.Response:
        return requests.post(self.url, json=payload, timeout=self.timeout, verify=False)


class Michael(Planner, RemotePlanner):
    def plan(self, pddl: PDDL, **kwargs: Dict[str, Any]) -> requests.models.Response:
        payload = {
            "domain": pddl.domain,
            "problem": pddl.problem,
            "numplans": 1,
            "qualitybound": 1,
        }
        return self.call_remote_planner(payload=payload)

    def parse(
        self, response: requests.models.Response, **kwargs: Dict[str, Any]
    ) -> PlannerResponse:

        if response.status_code == 200:
            response = response.json()
            planner_response = PlannerResponse(metadata=response["raw_output"])

            flow: Flow = kwargs["flow"]
            slot_options: Set[SlotOptions] = flow.slot_options
            mapping_options: Set[MappingOptions] = flow.mapping_options
            confirm_options: Set[ConfirmOptions] = flow.confirm_options

            for plan in response.get("plans", []):

                actions = plan.get("actions", [])
                length = len(actions)

                new_plan = ClassicalPlan(cost=plan.get("cost", length), length=length)

                for action in actions:
                    action = action.split()
                    action_name = revert_string_transform(
                        action[0], kwargs["transforms"]
                    )

                    new_action: Action = parse_action(
                        action_name=action_name, parameters=action[1:], **kwargs
                    )
                    new_plan.plan.append(new_action)

                if SlotOptions.group_slots in slot_options:
                    new_plan = self.group_items(new_plan, flow, SlotOptions.group_slots)

                if MappingOptions.group_maps in mapping_options:
                    new_plan = self.group_items(
                        new_plan, flow, MappingOptions.group_maps
                    )

                if ConfirmOptions.group_confirms in confirm_options:
                    new_plan = self.group_items(
                        new_plan, flow, ConfirmOptions.group_confirms
                    )

                planner_response.list_of_plans.append(new_plan)

            return planner_response

        else:
            return PlannerResponse(metadata=response)


class Christian(Planner, RemotePlanner):
    def plan(self, pddl: PDDL, **kwargs: Dict[str, Any]) -> requests.models.Response:
        payload = {"domain": pddl.domain, "problem": pddl.problem}
        return self.call_remote_planner(payload=payload)

    def parse(
        self, response: requests.models.Response, **kwargs: Dict[str, Any]
    ) -> PlannerResponse:

        if response.status_code == 200:
            response = response.json()
            response = response["result"]
            planner_response = PlannerResponse(metadata=response["output"])

            actions = response.get("plan", [])
            length = len(actions)

            new_plan = ClassicalPlan(cost=response.get("cost", length), length=length)

            flow: Flow = kwargs["flow"]
            slot_options: Set[SlotOptions] = flow.slot_options
            mapping_options: Set[MappingOptions] = flow.mapping_options
            confirm_options: Set[ConfirmOptions] = flow.confirm_options

            for action in actions:
                action = re.search(r"\((.*?)\)", action["name"])

                assert action is not None
                action = action.group(1)

                action = action.split()
                action_name = revert_string_transform(action[0], kwargs["transforms"])

                new_action: Action = parse_action(
                    action_name=action_name, parameters=action[1:], **kwargs
                )
                new_plan.plan.append(new_action)

            if SlotOptions.group_slots in slot_options:
                new_plan = self.group_items(new_plan, flow, SlotOptions.group_slots)

            if MappingOptions.group_maps in mapping_options:
                new_plan = self.group_items(new_plan, flow, MappingOptions.group_maps)

            if ConfirmOptions.group_confirms in confirm_options:
                new_plan = self.group_items(
                    new_plan, flow, ConfirmOptions.group_confirms
                )

            planner_response.list_of_plans.append(new_plan)
            return planner_response

        else:
            return PlannerResponse(metadata=response)
