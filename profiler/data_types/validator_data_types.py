from pydantic import BaseModel


class PddlPlanValidatorOutput(BaseModel):
    is_executable_plan: bool = False
    is_valid_plan: bool = False
    total_cost: int = -1
