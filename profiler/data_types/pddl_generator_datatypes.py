from pydantic import BaseModel
from typing import List
from nl2flow.plan.schemas import ClassicalPlan


class PddlGeneratorOutput(BaseModel):
    description: str  # the description of generated PDDL domain and problem
    pddl_domain: str  # PDDL domain
    pddl_problem: str  # PDDL problem
    list_of_plans: List[ClassicalPlan] = []  # Response from a planner
    sample_hash: str  # hash for PDDL domain and problem
