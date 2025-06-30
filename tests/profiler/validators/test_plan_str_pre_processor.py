from typing import List
from profiler.data_types.agent_info_data_types import AgentInfo, AgentInfoSignature, AgentInfoSignatureItem
from profiler.validators.plan_str_pre_processor import pre_process_plan_str


def test_pre_process_plan_str_re_order_signature_items() -> None:
    llm_response = (
        "PLAN EXPLANATION\n0. Acquire the value of v__24"
        + " by asking the user. v__24 is required later by action a__2.\n1. Acquire the value of v__26"
        + " by asking the user. v__26 is required later by action a__2.\n2."
        + " Execute action a__2 with v__24 and v__26 as inputs. This will result in acquiring v__1 and v__27."
        + " Since executing a__2 was the goal of this plan, return the results of a__2(v__24, v__26) to the user."
        + "\nPLAN\n[0] ask(v__24)\n[1] ask(v__26)\n[2] v__1, v__27 = a__2(v__24, v__26)"
    )
    available_agents: List[AgentInfo] = [
        AgentInfo(
            agent_id="a__2",
            actuator_signature=AgentInfoSignature(
                in_sig_full=[AgentInfoSignatureItem(name="v__26"), AgentInfoSignatureItem(name="v__24")]
            ),
        )
    ]
    action_strs = pre_process_plan_str(response=llm_response, available_agents=available_agents)

    assert len(action_strs) == 3
    assert action_strs[2].index("v__26") < action_strs[2].index("v__24")
