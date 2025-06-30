from typing import Dict, List, Optional

from profiler.data_types.agent_info_data_types import AgentInfo

NO_PLAN = "no plan"
PLAN_HEADER = "PLAN"

def get_action_str(input_str:str, action_name_input_parameters_dict: Dict[str, List[str]]) -> Optional[str]:
    action_str = input_str[:]
    if len(action_str) > 0:
        if "]" in action_str:
            action_str = action_str.split("]")[1].strip()
            if ")" in action_str:
                idx = action_str.find(")")
                action_str = action_str[: idx + 1].strip()
                try:
                    pre_action_string = ""
                    tmp_action_str = action_str[:]
                    if "=" in action_str:
                        action_parts = action_str.split("=")
                        pre_action_string = action_parts[0].strip()
                        tmp_action_str = action_parts[1].strip()
                    if "(" in tmp_action_str and ")" in tmp_action_str:
                        idx_start = tmp_action_str.find("(")
                        idx_end = tmp_action_str.find(")")
                        if idx_end > (idx_start + 1):  # parameter exists
                            action_name = tmp_action_str[:idx_start].strip()
                            if (
                                action_name != "ask"
                                and action_name != "map"
                                and action_name in action_name_input_parameters_dict
                            ):
                                generated_parameters_set = set(
                                    filter(
                                        lambda ele: len(ele) > 0,
                                        map(
                                            lambda param: param.strip(),
                                            tmp_action_str[idx_start + 1 : idx_end].split(","),  # noqa: E203
                                        ),
                                    )
                                )

                                if len(generated_parameters_set) > 0:
                                    sorted_parameters = []
                                    true_parameters = action_name_input_parameters_dict[action_name]
                                    for true_parameter in true_parameters:
                                        if true_parameter in generated_parameters_set:
                                            sorted_parameters.append(true_parameter[:])
                                            generated_parameters_set.remove(true_parameter)

                                    sorted_parameters += list(
                                        generated_parameters_set
                                    )  # append hallucinated parameters

                                    action_str = action_name + "(" + ", ".join(sorted_parameters) + ")"

                    if len(pre_action_string) > 0:
                        action_str = pre_action_string.strip() + " = " + action_str.strip()
                except Exception as e:
                    print(e)

                return action_str
            
    return None

def pre_process_plan_str(response: str, available_agents: List[AgentInfo]) -> Optional[List[str]]:
    if NO_PLAN in response:
        return []

    split_text = PLAN_HEADER + "\n"
    plan_start_idx = response.rfind(split_text)
    if plan_start_idx == -1:
        return None

    if (plan_start_idx + len(split_text)) > (len(response) - 1):
        return []

    plan_response = response[(plan_start_idx + len(split_text)) :]  # noqa: E203

    if len(plan_response) == 0:
        return []

    plan: List[str] = []
    action_name_input_parameters_dict: Dict[str, List[str]] = {}

    for available_agent in available_agents:
        action_name_input_parameters_dict[available_agent.agent_id.strip()] = list(
            map(lambda signature: signature.name.strip(), available_agent.actuator_signature.in_sig_full)
        )

    for action_str in plan_response.split("\n"):
        new_action_str = get_action_str(input_str=action_str, action_name_input_parameters_dict=action_name_input_parameters_dict)
        if new_action_str is not None:
            plan.append(new_action_str)

    return plan
