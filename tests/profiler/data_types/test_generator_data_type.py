from profiler.data_types.generator_data_type import AgentInfoGeneratorInputCheck, NameGenerator


class TestGeneratorDataType:
    def test_hash_AgentInfoGeneratorInputCheck(self) -> None:
        setting = AgentInfoGeneratorInputCheck(
            num_agents=1,
            num_var=2,
            should_objects_known_in_memory=True,
            num_input_parameters=2,
            num_samples=2,
            num_goal_agents=2,
            num_coupled_agents=2,
            num_slot_fillable_variables=2,
            num_mappable_variables=2,
            num_var_types=2,
            slot_filler_option=None,
            name_generator=NameGenerator.NUMBER,
            error_message=None,
        )
        hash_int = setting.__hash__()
        assert isinstance(hash_int, int)
