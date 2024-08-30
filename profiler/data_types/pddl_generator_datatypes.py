from pydantic import BaseModel
from typing import List, Optional
from nl2flow.plan.schemas import ClassicalPlan, PlannerResponse
from profiler.data_types.generator_data_type import AgentInfoGeneratorInput
from profiler.data_types.generator_output_data_type import AgentInfoGeneratorOutputItem


class PlanningDatumTag(BaseModel):
    number_of_agents: int = -1
    number_of_variables: int = -1
    input_parameters_per_agent: int = -1
    coupling_of_agents: float = -1.0
    parameterized: bool = False
    enable_slots: bool = False
    enable_slotting_cost: bool = False
    enable_maps: bool = False
    enable_mapping_cost: bool = False
    multiple_goals: bool = False
    operators_as_goal: bool = True
    objects_as_goal: bool = False
    or_goals: bool = False
    constraints_in_memory: bool = False
    constraints_in_spec: bool = False
    constraints_in_goal: bool = False
    constraints_in_input: bool = False
    constraints_in_output: bool = False
    enable_typing: bool = False
    flat_type_hierarchy: bool = False
    number_of_types: int = -1
    tristate_variables: bool = False
    objects_in_memory: bool = False
    history_in_memory: bool = False
    failure_in_history: bool = False
    length_of_sequence: int = -1


class PddlGeneratorOutput(BaseModel):
    description: str  # the description of generated PDDL domain and problem
    pddl_domain: str  # PDDL domain
    pddl_problem: str  # PDDL problem
    list_of_plans: List[ClassicalPlan] = []  # Response from a planner
    prettified_plans: str  # prettified plans
    prettified_optimal_plan_forward: str  # prettified optimal plan (forward explanation)
    sample_hash: str  # hash for PDDL domain and problem
    agent_info_generator_input: AgentInfoGeneratorInput  # input to generator
    compiler_planner_lag_millisecond: float  # lag in millisecond
    planner_response: PlannerResponse  # planner response
    agent_info_generator_output_item: AgentInfoGeneratorOutputItem  # seed for flow object
    planning_datum_tag: Optional[PlanningDatumTag] = None

    def set_tags(self) -> None:
        num_agents = len(self.agent_info_generator_output_item.available_agents)
        self.planning_datum_tag = PlanningDatumTag(
            number_of_agents=num_agents,
            number_of_variables=self.agent_info_generator_input.num_var,
            input_parameters_per_agent=(self.agent_info_generator_input.num_input_parameters * 2),
            coupling_of_agents=(self.agent_info_generator_input.proportion_coupled_agents * 100.0),
            enable_slots=(
                True
                if int(
                    round(
                        self.agent_info_generator_input.num_var
                        * self.agent_info_generator_input.proportion_slot_fillable_variables
                    )
                )
                > 0
                else False
            ),
            enable_maps=(True if len(self.agent_info_generator_output_item.mappings) > 0 else False),
            multiple_goals=(True if len(self.agent_info_generator_output_item.goal_agent_ids) > 1 else False),
            objects_in_memory=(
                True
                if (
                    len(self.agent_info_generator_output_item.available_data) > 0
                    and self.agent_info_generator_input.should_objects_known_in_memory
                )
                else False
            ),
            length_of_sequence=(len(self.list_of_plans[0].plan) if len(self.list_of_plans) > 0 else 0),
        )
