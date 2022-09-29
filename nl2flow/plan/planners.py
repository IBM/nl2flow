from nl2flow.compile.schemas import PDDL
from nl2flow.plan.schemas import PlannerResponse

from abc import ABC, abstractmethod
from typing import Any, Dict
from requests.models import Response
from requests import post


class Planner(ABC):

    @abstractmethod
    def plan(self, pddl: PDDL, **kwargs) -> Any:
        pass

    @abstractmethod
    def parse(self, **kwargs) -> PlannerResponse:
        pass

    @staticmethod
    def pretty_print(planner_response: PlannerResponse):
        print(planner_response)


class RemotePlanner(ABC):

    def __init__(self, url: str, timeout: int = 5):
        self.url = url
        self.timeout = timeout

    def call_remote_planner(self, payload: Dict) -> Response:
        return post(self.url, json=payload, timeout=self.timeout, verify=False)


class Michael(Planner, RemotePlanner):

    def plan(self, pddl: PDDL, **kwargs) -> Response:
        payload = {"domain": pddl.domain, "problem": pddl.problem, "numplans": 1, "qualitybound": 1}
        return self.call_remote_planner(payload=payload)

    def parse(self, response: Response, **kwargs) -> PlannerResponse:
        pass


class Christian(Planner, RemotePlanner):

    def plan(self, pddl: PDDL, **kwargs) -> Response:
        payload = {"domain": pddl.domain, "problem": pddl.problem}
        return self.call_remote_planner(payload=payload)

    def parse(self, response: Response,  **kwargs) -> PlannerResponse:
        pass
