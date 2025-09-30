from nl2flow.plan.schemas import PlannerResponse, ClassicalPlan as Plan
from nl2flow.compile.schemas import ClassicalPlanReference, Step, Constraint
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from profiler.data_types.agent_info_data_types import AgentInfo


def get_action_str(input_str: str, action_name_input_parameters_dict: Dict[str, List[str]]) -> Optional[str]:
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


def pre_process_plan_str(
    tokens_str: str, available_agents: List[AgentInfo], no_plan_str: str, plan_header: str
) -> Optional[List[str]]:
    if no_plan_str in tokens_str:
        return []

    split_text = plan_header + "\n"
    plan_start_idx = tokens_str.rfind(split_text)
    if plan_start_idx == -1:
        return None

    if (plan_start_idx + len(split_text)) > (len(tokens_str) - 1):
        return []

    plan_response = tokens_str[(plan_start_idx + len(split_text)) :]  # noqa: E203

    if len(plan_response) == 0:
        return []

    plan: List[str] = []
    action_name_input_parameters_dict: Dict[str, List[str]] = {}

    for available_agent in available_agents:
        action_name_input_parameters_dict[available_agent.agent_id.strip()] = list(
            map(lambda signature: signature.name.strip(), available_agent.actuator_signature.in_sig_full)
        )

    for action_str in plan_response.split("\n"):
        new_action_str = get_action_str(
            input_str=action_str, action_name_input_parameters_dict=action_name_input_parameters_dict
        )
        if new_action_str is not None:
            plan.append(new_action_str)

    return plan


class Printer(ABC):
    @classmethod
    @abstractmethod
    def parse_token(cls, token: str, **kwargs: Any) -> Union[Step, Constraint, None]:
        pass

    @classmethod
    def parse_tokens(cls, list_of_tokens: List[str], **kwargs: Any) -> ClassicalPlanReference:
        parsed_plan = ClassicalPlanReference()

        for index, token in enumerate(list_of_tokens):
            new_action = cls.parse_token(token, **kwargs)

            if new_action:
                parsed_plan.plan.append(new_action)
            else:
                continue

        return parsed_plan

    @classmethod
    def parse_string(cls, tokens_str: str, **kwargs: Any) -> ClassicalPlanReference:
        available_agents: List[AgentInfo] = kwargs.get("available_agents", [])
        no_plan_string: str = kwargs.get("no_plan_string", "no plan")
        plan_header: str = kwargs.get("plan_header", "PLAN")

        if len(available_agents) == 0:
            raise Exception("available-agents should include AgentInfo")

        list_of_tokens = pre_process_plan_str(
            tokens_str=tokens_str,
            available_agents=available_agents,
            no_plan_str=no_plan_string,
            plan_header=plan_header,
        )

        return cls.parse_tokens(list_of_tokens, **kwargs)

    @classmethod
    @abstractmethod
    def pretty_print_plan(cls, plan: Plan, **kwargs: Any) -> str:
        pass

    @classmethod
    def pretty_print(cls, planner_response: PlannerResponse, **kwargs: Any) -> str:
        pretty = ""

        for index, plan in enumerate(planner_response.list_of_plans):
            pretty += f"\n\n---- Plan #{index} ----\n"
            pretty += f"Cost: {plan.cost}, Length: {plan.length}\n\n"
            pretty += cls.pretty_print_plan(plan, **kwargs)

        return pretty
