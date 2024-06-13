from __future__ import annotations
from copy import deepcopy
from typing import List, Optional, Tuple
from pydantic import BaseModel, model_validator
from profiler.data_types.agent_info_data_types import AgentInfo, AgentInfoUnitModel
from profiler.data_types.generator_data_type import (
    AgentInfoGeneratorInput,
    PlanningInputDescriptionMode,
)
from profiler.generators.description_generator.description_generator_helper import get_concise_description
from profiler.validators.agent_info_generator_test_utils import check_sample
from profiler.generators.description_generator.description_generator import (
    get_sample_description,
)
from profiler.common_helpers.hash_helper import get_hash


class AgentInfoGeneratorOutputItemCore(BaseModel):
    available_agents: List[AgentInfo]
    goal_agent_ids: List[str]
    mappings: List[Tuple[str, str, float]]
    available_data: List[Tuple[str, Optional[str]]]


class AgentInfoGeneratorOutputItem(BaseModel):
    available_agents: List[AgentInfo]
    goal_agent_ids: List[str]
    mappings: List[Tuple[str, str, float]]
    available_data: List[Tuple[str, Optional[str]]]  # variable name, variable type
    agent_info_generator_input: AgentInfoGeneratorInput

    @model_validator(mode="after")
    def check_data_integrity(self) -> AgentInfoGeneratorOutputItem:
        check_sample(
            self.agent_info_generator_input,
            self.available_agents,
            self.available_data,
            self.goal_agent_ids,
            self.mappings,
        )
        return self

    def describe(
        self, planning_input_description_mode: PlanningInputDescriptionMode = PlanningInputDescriptionMode.VERBOSE
    ) -> str:
        agent_info_unit_model = AgentInfoUnitModel(
            available_agents=self.available_agents,
            goal_agent_ids=self.goal_agent_ids,
            mappings=self.mappings,
            available_data=self.available_data,
        )

        if planning_input_description_mode == PlanningInputDescriptionMode.JSON:
            return agent_info_unit_model.get_simple_planning_model_json_str()

        if planning_input_description_mode == PlanningInputDescriptionMode.CONCISE:
            return get_concise_description(simple_planning_model=agent_info_unit_model.get_simple_planning_model())

        # VERBOSE
        return get_sample_description(  # type: ignore
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
        return get_hash(core_info.model_dump_json())  # type: ignore
