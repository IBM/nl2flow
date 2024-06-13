from types import ModuleType
from typing import List, Optional
from nl2flow.plan.schemas import PlannerResponse
from profiler.data_types.generator_data_type import AgentInfoGeneratorInput
from profiler.data_types.pddl_generator_datatypes import PddlGeneratorOutput
from profiler.generators.info_generator.agent_info_generator import generate_agent_infos
from profiler.converters.info_2_flow_converter import get_flow_from_agent_infos
from profiler.common_helpers.string_helper import trim_pddl_str
from profiler.test_helpers.profiler_test_helper_variables import (
    pddl_start_key,
)
from nl2flow.plan.planner import Planner
from nl2flow.printers.codelike import CodeLikePrint
from nl2flow.printers.verbalize import VerbalizePrint
from profiler.common_helpers.time_helper import get_current_time_in_millisecond


def generate_dataset_with_info_generator(
    agent_info_generator_input: AgentInfoGeneratorInput, planner: Planner, random: ModuleType, should_plan: bool = True
) -> Optional[List[PddlGeneratorOutput]]:
    samples, is_all_samples_collected = generate_agent_infos(agent_info_generator_input, random)
    if not is_all_samples_collected:
        return None
    pddl_generator_outputs: List[PddlGeneratorOutput] = list()
    for sample in samples:
        flow = get_flow_from_agent_infos(
            available_agents=sample.available_agents,
            mappings=sample.mappings,
            goals=set(sample.goal_agent_ids),
            available_data=sample.available_data,
            slot_filler_option=agent_info_generator_input.slot_filler_option,
        )
        pddl, _ = flow.compile_to_pddl()

        planner_time_start = get_current_time_in_millisecond()
        planner_response = flow.plan_it(planner) if should_plan else PlannerResponse()
        compiler_planner_lag = get_current_time_in_millisecond() - planner_time_start
        pddl_generator_outputs.append(
            PddlGeneratorOutput(
                description=sample.describe(),
                pddl_domain=trim_pddl_str(pddl.domain, pddl_start_key),
                pddl_problem=trim_pddl_str(pddl.problem, pddl_start_key),
                list_of_plans=planner_response.list_of_plans,
                prettified_plans=CodeLikePrint.pretty_print(planner_response, show_output=False) if should_plan else "",
                prettified_optimal_plan_forward=(
                    VerbalizePrint.pretty_print_plan(planner_response.list_of_plans[0], flow_object=flow)
                    if len(planner_response.list_of_plans) > 0
                    else "no plan"
                ),
                sample_hash=sample.get_hash(),
                agent_info_generator_input=agent_info_generator_input.model_copy(deep=True),
                compiler_planner_lag_millisecond=compiler_planner_lag,
                planner_response=planner_response,
                agent_info_generator_output_item=sample,
            )
        )

    return pddl_generator_outputs
