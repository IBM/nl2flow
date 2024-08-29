from profiler.data_types.agent_info_data_types import (
    AgentInfo,
    AgentInfoSignature,
    AgentInfoSignatureItem,
    AgentInfoUnitModel,
)


def test_get_simple_planning_model_json_str() -> None:
    available_agents = [
        AgentInfo(
            agent_id="a",
            actuator_signature=AgentInfoSignature(
                in_sig_full=[
                    AgentInfoSignatureItem(name="b", slot_fillable=True),
                    AgentInfoSignatureItem(name="x", slot_fillable=False),
                ],
                out_sig_full=[
                    AgentInfoSignatureItem(name="c", slot_fillable=False, data_type="sample_type"),
                    AgentInfoSignatureItem(name="k", slot_fillable=True),
                ],
            ),
        )
    ]
    goal_agent_ids = [available_agents[0].agent_id]
    mappings = [("x", "k", 1.0)]
    available_data = [("b", None)]
    agent_info_unit_model = AgentInfoUnitModel(
        available_agents=available_agents,
        goal_agent_ids=goal_agent_ids,
        mappings=mappings,
        available_data=available_data,
        should_objects_known_in_memory=True,
    )
    json_str = agent_info_unit_model.get_simple_planning_model_json_str()
    expected_json_str = (
        '{"actions":[{"id":"a","input":["b","x"],"output":["c","k"]}],'
        + '"mappings":[["x","k"]],"available_data":["b"],"askable_parameters":["b","k"],'
        + '"unaskable_parameters":["x","c"],"goal_action_ids":["a"]}'
    )
    assert json_str == expected_json_str
