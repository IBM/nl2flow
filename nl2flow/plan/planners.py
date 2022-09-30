from nl2flow.compile.schemas import PDDL
from nl2flow.plan.schemas import PlannerResponse, ClassicalPlan, Action

from abc import ABC, abstractmethod
from typing import Any, Dict

import requests
import re


class Planner(ABC):
    @abstractmethod
    def plan(self, pddl: PDDL, **kwargs: Dict[str, Any]) -> Any:
        pass

    @abstractmethod
    def parse(self, response: Any, **kwargs: Dict[str, Any]) -> PlannerResponse:
        pass

    @staticmethod
    def pretty_print(planner_response: PlannerResponse) -> str:
        pretty = ""

        for index, plan in enumerate(planner_response.list_of_plans):
            pretty += f"\n\n---- Plan #{index} ----\n"
            pretty += f"Cost: {plan.cost}, Length: {plan.length}\n\n"

            for step, action in enumerate(plan.plan):
                inputs = ",".join(
                    [f"{item.name} ({item.type})" for item in action.inputs]
                )
                outputs = ",".join(
                    [f"{item.name} ({item.type})" for item in action.outputs]
                )

                pretty += f"Step {step}: {action.name}, Inputs: {inputs if action.inputs else None}, Outputs: {outputs if action.outputs else None}\n"

        return pretty


class RemotePlanner(ABC):
    def __init__(self, url: str, timeout: int = 5):
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

            for plan in response.get("plans", []):

                actions = plan.get("actions", [])
                length = len(actions)

                new_plan = ClassicalPlan(cost=plan.get("cost", length), length=length)

                for action in actions:
                    action = action.split()
                    new_plan.plan.append(Action(name=action[0], inputs=[], outputs=[]))

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

            for action in actions:
                action = re.search(r"\((.*?)\)", action["name"])

                assert action is not None
                action = action.group(1)

                action = action.split()
                new_plan.plan.append(Action(name=action[0], inputs=[], outputs=[]))

            planner_response.list_of_plans.append(new_plan)
            return planner_response

        else:
            return PlannerResponse(metadata=response)
