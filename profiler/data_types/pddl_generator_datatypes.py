from pydantic import BaseModel
from typing import List
from nl2flow.plan.schemas import ClassicalPlan
from profiler.data_types.generator_data_type import AgentInfoGeneratorInput


class PddlGeneratorOutput(BaseModel):
    description: str  # the description of generated PDDL domain and problem
    pddl_domain: str  # PDDL domain
    pddl_problem: str  # PDDL problem
    list_of_plans: List[ClassicalPlan] = []  # Response from a planner
    prettified_plans: str  # prettified plans
    sample_hash: str  # hash for PDDL domain and problem
    agent_info_generator_input: AgentInfoGeneratorInput  # input to generator
    compiler_planner_lag_millisecond: float  # lag in millisecond
