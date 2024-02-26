from nl2flow.compile.flow import Flow
from nl2flow.compile.utils import revert_string_transform
from nl2flow.plan.schemas import RawPlannerResult, RawPlan, PlannerResponse, ClassicalPlan
from nl2flow.plan.options import QUALITY_BOUND, NUM_PLANS
from nl2flow.plan.utils import parse_action, group_items
from nl2flow.compile.options import (
    SlotOptions,
    MappingOptions,
    ConfirmOptions,
)
from nl2flow.compile.schemas import PDDL

from abc import ABC, abstractmethod
from typing import Any, List, Set, Dict
from pathlib import Path
from kstar_planner import planners

import tempfile


class Planner(ABC):
    @abstractmethod
    def plan(self, pddl: PDDL, **kwargs: Dict[str, Any]) -> Any:
        pass

    @abstractmethod
    def parse(self, raw_plans: List[RawPlan], **kwargs: Any) -> PlannerResponse:
        pass

    @staticmethod
    def pretty_print(planner_response: PlannerResponse) -> str:
        pretty = ""

        for index, plan in enumerate(planner_response.list_of_plans):
            pretty += f"\n\n---- Plan #{index} ----\n"
            pretty += f"Cost: {plan.cost}, Length: {plan.length}\n\n"

            for step, action in enumerate(plan.plan):
                inputs = ", ".join([f"{item.item_id} ({item.item_type})" for item in action.inputs])
                outputs = ", ".join([f"{item.item_id} ({item.item_type})" for item in action.outputs])

                pretty += (
                    f"Step {step}: {action.name}, "
                    f"Inputs: {inputs if action.inputs else None}, "
                    f"Outputs: {outputs if action.outputs else None}\n"
                )

        return pretty


class Kstar(Planner):
    def plan(self, pddl: PDDL, **kwargs: Any) -> PlannerResponse:
        with (
            tempfile.NamedTemporaryFile() as domain_temp,
            tempfile.NamedTemporaryFile() as problem_temp,
        ):
            domain_file = Path(tempfile.gettempdir()) / domain_temp.name
            problem_file = Path(tempfile.gettempdir()) / problem_temp.name

            domain_file.write_text(pddl.domain)
            problem_file.write_text(pddl.problem)

            result = planners.plan_unordered_topq(
                domain_file=domain_file,
                problem_file=problem_file,
                quality_bound=QUALITY_BOUND,
                number_of_plans_bound=NUM_PLANS,
            )

            raw_planner_result = RawPlannerResult.model_validate(result)
            return self.parse(raw_planner_result.plans, **kwargs)

    def parse(self, raw_plans: List[RawPlan], **kwargs: Any) -> PlannerResponse:
        planner_response = PlannerResponse()

        flow: Flow = kwargs["flow"]
        slot_options: Set[SlotOptions] = flow.slot_options
        mapping_options: Set[MappingOptions] = flow.mapping_options
        confirm_options: Set[ConfirmOptions] = flow.confirm_options

        for plan in raw_plans:
            actions = plan.actions
            length = len(actions)

            new_plan = ClassicalPlan(cost=plan.cost, length=length)

            for action in actions:
                action_split = action.split()
                action_name = revert_string_transform(action_split[0], kwargs["transforms"])

                if action_name is not None:
                    new_action = parse_action(action_name=action_name, parameters=action_split[1:], **kwargs)

                else:
                    raise ValueError("Could not parse action name.")

                if new_action:
                    new_plan.plan.append(new_action)

            if SlotOptions.group_slots in slot_options:
                new_plan = group_items(new_plan, SlotOptions.group_slots)

            if MappingOptions.group_maps in mapping_options:
                new_plan = group_items(new_plan, MappingOptions.group_maps)

            if ConfirmOptions.group_confirms in confirm_options:
                new_plan = group_items(new_plan, ConfirmOptions.group_confirms)

            if new_plan.length:
                planner_response.list_of_plans.append(new_plan)

        return planner_response
