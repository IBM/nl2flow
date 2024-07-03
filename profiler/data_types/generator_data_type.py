from enum import Enum
from math import ceil
from typing import List, Optional
from pydantic import BaseModel, field_validator, model_validator
from nl2flow.compile.options import SlotOptions


class PlanningInputDescriptionMode(str, Enum):
    VERBOSE = "VERBOSE"
    CONCISE = "CONCISE"
    JSON = "JSON"


class NameGenerator(str, Enum):
    NUMBER = "NUMBER"
    HAIKUNATOR = "HAIKUNATOR"
    DATASET = "DATASET"


class VariableInfo(BaseModel):
    variable_name: str
    mappable: bool
    slot_fillable: bool
    variable_type: Optional[str] = None


class AgentInfoGeneratorInputCheck(BaseModel):
    # The number of available agents
    num_agents: int
    # The number of variables
    num_var: int
    # The number of input parameters for an agent (action)
    # The number of output parameters for an agent is equal to The number of input parameters for an agent
    num_input_parameters: int
    # The number of input data sets to a planner
    num_samples: int
    # The number of goal agents in available agents
    num_goal_agents: int
    # The number of coupled agents
    num_coupled_agents: int
    # The number of slot-fillable variables
    num_slot_fillable_variables: int
    # The number of mappable variables
    num_mappable_variables: int
    # the number of types for variables
    num_var_types: int = 0
    # slot-filler type
    slot_filler_option: Optional[SlotOptions] = None
    # Name generator
    name_generator: NameGenerator = NameGenerator.NUMBER
    # error_message
    error_message: Optional[str] = None

    def __hash__(self) -> int:
        return hash((type(self),) + tuple(self.__dict__.values()))


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
    # The number of goal agents in available agents
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

    @field_validator("num_agents")
    def check_num_agents_greater_than_zero(cls, v):  # type: ignore
        if v <= 0:
            raise ValueError("num_agents should be greater than 0")
        return v

    @model_validator(mode="after")
    def check_num_variable_types_less_than_equal_to_num_var(self):  # type: ignore
        if self.num_var_types < 0:
            raise ValueError("num_var_types should be greater than or equal to 0")
        if self.num_var_types > self.num_var:
            raise ValueError("num_var_types should be less than or equal to num_var")
        if self.num_var_types > 15:
            raise ValueError("num_var_types should be less than or equal to 15")
        return self

    @model_validator(mode="after")
    def check_num_var_greater_than_zero(self):  # type: ignore
        if self.num_var <= 0:
            raise ValueError("num_variables should be greater than 0")
        if self.num_var < self.num_input_parameters * 2:
            raise ValueError("num_variables should be greater than 2 * num_input_parameters")
        if (
            self.proportion_coupled_agents > 0.0
            and self.num_agents > 2
            and (self.num_var < self.num_input_parameters * 2 + 1)
        ):
            raise ValueError(
                """num_variables should be greater
                  than (2 * num_input_parameters + 1) when proportion_coupled_agents is greater
                    than 0.0 when there are more than two agents"""
            )
        return self

    @field_validator("num_input_parameters")
    def check_num_input_parameters_greater_than_zero(cls, v):  # type: ignore
        if v <= 0:
            raise ValueError("num_input_parameters should be greater than 0")
        return v

    @field_validator("num_samples")
    def check_num_samples_greater_than_zero(cls, v):  # type: ignore
        if v <= 0:
            raise ValueError("num_samples should be greater than 0")
        return v

    @model_validator(mode="after")
    def check_num_goal_agents_less_than_or_equal_to_num_agents(self):  # type: ignore
        if self.num_goal_agents > self.num_agents:
            raise ValueError("num_goal_agents should be less than or equal to num_agents")
        elif self.num_goal_agents <= 0:
            raise ValueError("num_goal_agents should be greater than 0")
        return self

    @model_validator(mode="after")
    def check_proportion_coupled_agents_greater_than_equal_to_zero_and_less_than_equal_to_one(self):  # type: ignore
        if self.proportion_coupled_agents < 0 or self.proportion_coupled_agents > 1:
            raise ValueError("proportion_coupled_agents should be between 0 (inclusive) and 1 (inclusive)")
        if ceil(self.num_agents * self.proportion_coupled_agents) == 1:
            raise ValueError("proportion_coupled_agents should make the number of coupled agents not 1")
        return self

    @model_validator(mode="after")
    def check_proportion_slot_fillable_variable_greater_than_equal_zero_and_less_than_equal_one(self):  # type: ignore
        if self.proportion_slot_fillable_variables < 0 or self.proportion_slot_fillable_variables > 1:
            raise ValueError("proportion_slot_fillable_variables should be between 0 (inclusive) and 1 (inclusive)")
        return self

    @model_validator(mode="after")
    def check_proportion_mappable_variables_greater_than_equal_to_zero_and_less_than_equal_one(self):  # type: ignore
        if self.proportion_mappable_variables < 0 or self.proportion_mappable_variables > 1:
            raise ValueError("proportion_mappable_variables should be between 0 (inclusive) and 1 (inclusive)")
        if ceil(self.num_var * self.proportion_mappable_variables) == 1:
            raise ValueError("proportion_mappable_variables should make the number of mappable variables not 1")
        return self


class AgentInfoGeneratorInputBatch(BaseModel):
    # The number of available agents
    num_agents: List[int] = [3]
    # The number of variables
    num_var: List[int] = [6]
    # The number of input parameters for an agent (action)
    # The number of output parameters for an agent is equal to The number of input parameters for an agent
    num_input_parameters: List[int] = [2]
    # The number of input data sets to a planner
    num_samples: List[int] = [2]
    # The proportion of goal agents in available agents
    num_goal_agents: List[int] = [1]
    # The proportion of coupled agents
    proportion_coupled_agents: List[float] = [0.5]
    # The proportion of slot-fillable variables
    proportion_slot_fillable_variables: List[float] = [1.0]
    # The proportion of mappable variables
    proportion_mappable_variables: List[float] = [0.5]
    # the number of types for variables
    num_var_types: List[int] = [0]
    # slot-filler type
    slot_filler_option: List[Optional[SlotOptions]] = [None]
    # Name generator
    name_generator: List[NameGenerator] = [NameGenerator.NUMBER]
    # error_message
    error_message: List[Optional[str]] = [None]
