from typing import List, Set, Tuple
from pydantic import BaseModel, root_validator
from profiler.generators.info_generator.agent_info_data_types import AgentInfo
from profiler.generators.info_generator.generator_data_type import (
    AgentInfoGeneratorInput,
)
from profiler.validators.agent_info_generator_test_utils import check_sample
from profiler.generators.description_generator.description_generator import (
    get_sample_description,
)


class AgentInfoGeneratorOutputItem(BaseModel):
    available_agents: List[AgentInfo]
    goal_agent_ids: Set[str]
    mappings: List[Tuple[str, str, float]]
    available_data: List[str]
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
