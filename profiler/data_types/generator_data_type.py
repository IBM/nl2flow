from enum import Enum
from math import ceil
from typing import Optional
from pydantic import BaseModel, model_validator, validator
from nl2flow.compile.options import SlotOptions


class NameGenerator(Enum):
    NUMBER = 1
    HAIKUNATOR = 2
    DATASET = 3


class VariableInfo(BaseModel):
    variable_name: str
    mappable: bool
    slot_fillable: bool
    variable_type: Optional[str]


class AgentInfoGeneratorInput(BaseModel):
    # The number of available agents
    num_agents: int
    # The number of variables
    num_var: int
    # The number of input parameters for an agent (action)
    # The number of output parameters for an agent is equal to The number of input parameters for an agent
    num_input_parameters: int
    # The number of input data sets to a planner
    num_samples: int
    # The proportion of goal agents in available agents
    num_goal_agents: int
    # The proportion of coupled agents
    proportion_coupled_agents: float
    # The proportion of slot-fillable variables
    proportion_slot_fillable_variables: float
    # The proportion of mappable variables
    proportion_mappable_variables: float
    # the number of types for variables
    num_var_types: int = 0
    # slot-filler type
    slot_filler_option: Optional[SlotOptions] = None
    # Name generator
    name_generator: NameGenerator = NameGenerator.NUMBER
    # error_message
    error_message: Optional[str] = None

    @validator("num_agents")
    def check_num_agents_greater_than_zero(cls, v):
        if v <= 0:
            raise ValueError("num_agents should be greater than 0")
        return v

    @model_validator(mode="after")
    def check_num_variable_types_less_than_equal_to_num_var(cls, v):
        if v["num_var_types"] < 0:
            raise ValueError("num_var_types should be greater than or equal to 0")
        if v["num_var_types"] > v["num_var"]:
            raise ValueError("num_var_types should be less than or equal to num_var")
        if v["num_var_types"] > 15:
            raise ValueError("num_var_types should be less than or equal to 15")
        return v

    @model_validator(mode="after")
    def check_num_var_greater_than_zero(cls, v):
        if v["num_var"] <= 0:
            raise ValueError("num_variables should be greater than 0")
        if v["num_var"] < v["num_input_parameters"] * 2:
            raise ValueError("num_variables should be greater than 2 * num_input_parameters")
        if (
            v["proportion_coupled_agents"] > 0.0
            and v["num_agents"] > 2
            and (v["num_var"] < v["num_input_parameters"] * 2 + 1)
        ):
            raise ValueError(
                """num_variables should be greater
                  than (2 * num_input_parameters + 1) when proportion_coupled_agents is greater
                    than 0.0 when there are more than two agents"""
            )
        return v

    @validator("num_input_parameters")
    def check_num_input_parameters_greater_than_zero(cls, v):
        if v <= 0:
            raise ValueError("num_input_parameters should be greater than 0")
        return v

    @validator("num_samples")
    def check_num_samples_greater_than_zero(cls, v):
        if v <= 0:
            raise ValueError("num_samples should be greater than 0")
        return v

    @model_validator(mode="after")
    def check_num_goal_agents_less_than_or_equal_to_num_agents(cls, v):
        if v["num_goal_agents"] > v["num_agents"]:
            raise ValueError("num_goal_agents should be less than or equal to num_agents")
        elif v["num_goal_agents"] <= 0:
            raise ValueError("num_goal_agents should be greater than 0")
        return v

    @model_validator(mode="after")
    def check_proportion_coupled_agents_greater_than_equal_to_zero_and_less_than_equal_to_one(cls, v):
        if v["proportion_coupled_agents"] < 0 or v["proportion_coupled_agents"] > 1:
            raise ValueError("proportion_coupled_agents should be between 0 (inclusive) and 1 (inclusive)")
        if ceil(v["num_agents"] * v["proportion_coupled_agents"]) == 1:
            raise ValueError("proportion_coupled_agents should make the number of coupled agents not 1")
        return v

    @model_validator(mode="after")
    def check_proportion_slot_fillable_variables_greater_than_equal_to_zero_and_less_than_equal_to_one(cls, v):
        num_agents_coupled = ceil(v["num_agents"] * v["proportion_coupled_agents"])
        max_num_variables_in_agents = (
            ((v["num_input_parameters"] * 2) * (v["num_agents"] - num_agents_coupled))
            + ((v["num_input_parameters"] * 2 - 1) * num_agents_coupled)
            + ((num_agents_coupled + 1) * ceil(v["proportion_coupled_agents"]))
        )
        if v["proportion_slot_fillable_variables"] < 0 or v["proportion_slot_fillable_variables"] > 1:
            raise ValueError("proportion_slot_fillable_variables should be between 0 (inclusive) and 1 (inclusive)")
        if ceil(v["num_var"] * v["proportion_slot_fillable_variables"]) > max_num_variables_in_agents:
            raise ValueError(
                """proportion_slot_fillable_variables should less than
                  or equal to (num_agents * num_input_parameters * 2 - (the number of coupled agents -1))"""
            )
        return v

    @model_validator(mode="after")
    def check_proportion_mappable_variables_greater_than_equal_to_zero_and_less_than_equal_to_one(cls, v):
        if v["proportion_mappable_variables"] < 0 or v["proportion_mappable_variables"] > 1:
            raise ValueError("proportion_mappable_variables should be between 0 (inclusive) and 1 (inclusive)")
        if ceil(v["num_var"] * v["proportion_mappable_variables"]) == 1:
            raise ValueError("proportion_mappable_variables should make the number of mappable variables not 1")
        return v
