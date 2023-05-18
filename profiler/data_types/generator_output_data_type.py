from copy import deepcopy
from typing import List, Optional, Set, Tuple
from pydantic import BaseModel, root_validator
from profiler.data_types.agent_info_data_types import AgentInfo
from profiler.data_types.generator_data_type import (
    AgentInfoGeneratorInput,
)
from profiler.validators.agent_info_generator_test_utils import check_sample
from profiler.generators.description_generator.description_generator import (
    get_sample_description,
)
from profiler.common_helpers.hash_helper import get_hash


class AgentInfoGeneratorOutputItemCore(BaseModel):
    available_agents: List[AgentInfo]
    goal_agent_ids: Set[str]
    mappings: List[Tuple[str, str, float]]
    available_data: List[Tuple[str, Optional[str]]]


class AgentInfoGeneratorOutputItem(BaseModel):
    available_agents: List[AgentInfo]
    goal_agent_ids: Set[str]
    mappings: List[Tuple[str, str, float]]
    available_data: List[Tuple[str, Optional[str]]]  # variable name, variable type
    agent_info_generator_input: AgentInfoGeneratorInput

    @root_validator()
    def check_data_integrity(cls, v):
        check_sample(
            v["agent_info_generator_input"],
            v["available_agents"],
            v["available_data"],
            v["goal_agent_ids"],
            v["mappings"],
        )
        return v

    def describe(self) -> str:
        return get_sample_description(
            self.available_agents,
            self.goal_agent_ids,
            self.mappings,
            self.available_data,
        )

    def get_core_fields(self) -> AgentInfoGeneratorOutputItemCore:
        return AgentInfoGeneratorOutputItemCore(
            available_agents=deepcopy(self.available_agents),
            goal_agent_ids=deepcopy(self.goal_agent_ids),
            mappings=deepcopy(self.mappings),
            available_data=deepcopy(self.available_data),
        )

    def get_hash(self) -> str:
        core_info = AgentInfoGeneratorOutputItemCore(
            available_agents=deepcopy(self.available_agents),
            goal_agent_ids=deepcopy(self.goal_agent_ids),
            mappings=deepcopy(self.mappings),
            available_data=deepcopy(self.available_data),
        )
        return get_hash(core_info.json())
