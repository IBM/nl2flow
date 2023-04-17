from typing import List, Tuple
from profiler.generators.info_generator.agent_info_data_types import AgentInfo
from profiler.generators.info_generator.generator_data_type import (
    AgentInfoGeneratorInput,
    VariableInfo,
)
from profiler.generators.info_generator.generator_output_data_type import (
    AgentInfoGeneratorOutputItem,
)
from profiler.generators.info_generator.agent_info_generator_helper import (
    get_agent_variable_names,
    get_agents,
    get_variables,
    get_goals,
    get_agents_with_variables,
    get_mappings,
)


def generate_agent_infos(
    input: AgentInfoGeneratorInput,
) -> Tuple[List[AgentInfoGeneratorOutputItem], bool]:
    """
    This function returns all samples and the status of collecting all samples
    """
    samples: List[AgentInfoGeneratorOutputItem] = list()
    num_samples = 0
    max_try = 20
    count_try = 0
    while num_samples < input.num_samples and count_try < max_try:
        # generate names here
        agent_names, variable_names = get_agent_variable_names(
            input.name_generator, input.num_agents, input.num_var
        )
        agent_infos: List[AgentInfo] = get_agents(
            agent_names, input.num_input_parameters
        )
        goals = get_goals(input.num_goal_agents, agent_infos)
        variables: List[VariableInfo] = get_variables(
            variable_names,
            input.proportion_slot_fillable_variables,
            input.proportion_mappable_variables,
        )
        mappings: List[Tuple[str, str, float]] = get_mappings(variables)
        agent_infos_with_variables, available_data = get_agents_with_variables(
            agent_infos, variables, input.proportion_coupled_agents
        )

        if len(agent_infos_with_variables) == 0:
            # input setting issues
            break
        try:
            samples.append(
                AgentInfoGeneratorOutputItem(
                    available_agents=agent_infos_with_variables,
                    goal_agent_ids=goals,
                    mappings=mappings,
                    available_data=available_data,
                    agent_info_generator_input=input.copy(deep=True),
                )
            )
        except Exception as e:
            count_try += 1
            continue
        num_samples += 1
        count_try = 0
    # if there is no sample, input parameters result in slot-fillable variables remaining
    return samples, len(samples) == input.num_samples
