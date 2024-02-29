from __future__ import annotations
from copy import deepcopy
from typing import Dict, Optional
from pydantic import BaseModel
from profiler.common_helpers.hash_helper import get_hash

quadruple_fields = ["code", "description", "pddl_domain", "pddl_problem", "plan"]


class Quadruple(BaseModel):
    # descrption: python test method docstring
    # python code: python test method without assertion
    # PDDL: compiled PDDL
    # PLAN: plan from an automated planner
    code: str
    description: str
    pddl_doamin: str
    pddl_problem: str
    plan: str

    @staticmethod
    def get_quadruple_from_dict(data: Dict[str, str]) -> Optional[Quadruple]:
        if all(field in data for field in quadruple_fields):
            return Quadruple(
                code=data["code"],
                description=data["description"],
                pddl_doamin=data["pddl_domain"],
                pddl_problem=data["pddl_problem"],
                plan=data["plan"],
            )
        return None

    def get_hash(self) -> str:
        quadruple = Quadruple(
            code=deepcopy(self.code),
            description=deepcopy(self.description),
            pddl_doamin=deepcopy(self.pddl_doamin),
            pddl_problem=deepcopy(self.pddl_problem),
            plan=deepcopy(self.plan),
        )
        return get_hash(quadruple.json())
