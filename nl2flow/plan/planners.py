from nl2flow.compile.schemas import PDDL
from nl2flow.plan.schemas import PlannerResponse

from abc import ABC, abstractmethod
from typing import Any, Dict

import requests


class Planner(ABC):
    @abstractmethod
    def plan(self, pddl: PDDL, **kwargs: Dict[str, Any]) -> Any:
        pass

    @abstractmethod
    def parse(self, response: Any, **kwargs: Dict[str, Any]) -> PlannerResponse:
        pass

    @staticmethod
    def pretty_print(planner_response: PlannerResponse) -> str:
        print(planner_response)
        return ""


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
        pass


class Christian(Planner, RemotePlanner):
    def plan(self, pddl: PDDL, **kwargs: Dict[str, Any]) -> requests.models.Response:
        payload = {"domain": pddl.domain, "problem": pddl.problem}
        return self.call_remote_planner(payload=payload)

    def parse(
        self, response: requests.models.Response, **kwargs: Dict[str, Any]
    ) -> PlannerResponse:
        pass
