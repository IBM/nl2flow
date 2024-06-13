from copy import deepcopy
from types import ModuleType
from typing import Any, Dict, Generator, List, Set
from nl2flow.plan.planner import Planner
from profiler.data_types.generator_data_type import (
    AgentInfoGeneratorInput,
    AgentInfoGeneratorInputBatch,
    AgentInfoGeneratorInputCheck,
)
from profiler.data_types.pddl_generator_datatypes import PddlGeneratorOutput
from profiler.generators.dataset_generator.dataset_generator import generate_dataset_with_info_generator


def get_config_itr(
    field_names: List[str],
    entries: List[List[Any]],
    field_idx: int,
    unit_config: Dict[Any, Any],
    config_list: List[AgentInfoGeneratorInput],
) -> None:
    for entry in entries[field_idx]:
        unit_config[field_names[field_idx]] = entry
        if field_idx == len(field_names) - 1:
            try:
                config_list.append(AgentInfoGeneratorInput.model_validate(deepcopy(unit_config)))
            except Exception as e:
                print(e)
        else:
            get_config_itr(field_names, entries, field_idx + 1, unit_config, config_list)
    return


def get_agent_info_generator_inputs(
    config: AgentInfoGeneratorInputBatch,
) -> List[AgentInfoGeneratorInput]:
    config_dict = config.model_dump()
    field_names: List[str] = list(config_dict.keys())
    entries: List[List[Any]] = list(config_dict.values())
    config_list: List[AgentInfoGeneratorInput] = list()
    get_config_itr(field_names, entries, 0, dict(), config_list)
    return config_list


def get_pddl_generator_output_batch(
    batch_input: AgentInfoGeneratorInputBatch, planner: Planner, random: ModuleType, should_plan: bool = True
) -> Generator[List[PddlGeneratorOutput], None, None]:
    used_settings: Set[int] = set()
    for agent_info_generator_input in get_agent_info_generator_inputs(batch_input):
        generator_input_setting_hash = AgentInfoGeneratorInputCheck(
            num_agents=agent_info_generator_input.num_agents,
            num_var=agent_info_generator_input.num_var,
            num_input_parameters=agent_info_generator_input.num_input_parameters,
            num_samples=agent_info_generator_input.num_samples,
            num_goal_agents=agent_info_generator_input.num_goal_agents,
            num_coupled_agents=int(
                agent_info_generator_input.num_agents * agent_info_generator_input.proportion_coupled_agents
            ),
            num_slot_fillable_variables=int(
                agent_info_generator_input.num_var * agent_info_generator_input.proportion_slot_fillable_variables
            ),
            num_mappable_variables=int(
                agent_info_generator_input.num_var * agent_info_generator_input.proportion_mappable_variables
            ),
            num_var_types=agent_info_generator_input.num_var_types,
            slot_filler_option=agent_info_generator_input.slot_filler_option,
            name_generator=agent_info_generator_input.name_generator,
            error_message=agent_info_generator_input.error_message,
        ).__hash__()
        if generator_input_setting_hash in used_settings:
            continue
        used_settings.add(generator_input_setting_hash)
        try:
            pddl_generator_outputs = generate_dataset_with_info_generator(
                agent_info_generator_input=agent_info_generator_input,
                planner=planner,
                random=random,
                should_plan=should_plan,
            )
            if pddl_generator_outputs is not None:
                yield pddl_generator_outputs
        except Exception as e:
            print(e)
