from nl2flow.compile.flow import Flow
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.options import (
    NL2FlowOptions,
    SlotOptions,
    MemoryState,
    BasicOperations,
    ConstraintState,
    LifeCycleOptions,
)

from nl2flow.compile.schemas import GoalItem, GoalItems, SignatureItem, Parameter, MemoryItem, MappingItem, Constraint

from tests.testing import BaseTestAgents


class TestOptionalParameters(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)
        self.flow = Flow("Test Flow")
        self.flow.optimization_options.remove(NL2FlowOptions.multi_instance)
        self.flow.optimization_options.remove(NL2FlowOptions.allow_retries)

    def test_one_optional(self) -> None:
        agent = Operator("Test Agent")
        agent.add_input(
            SignatureItem(
                parameters=[
                    Parameter(item_id="a"),
                    Parameter(item_id="b"),
                    Parameter(item_id="c", required=False),
                    Parameter(item_id="d", required=False),
                ]
            )
        )

        self.flow.add(agent)
        self.flow.add(GoalItems(goals=GoalItem(goal_name=agent.name)))

        plans = self.get_plan()
        assert plans.best_plan
        assert len(plans.best_plan.plan) == 3

    def test_all_optional(self) -> None:
        agent = Operator("Test Agent")
        agent.add_input(
            SignatureItem(
                parameters=[
                    Parameter(item_id="x", required=False),
                    Parameter(item_id="y", required=False),
                    Parameter(item_id="z", required=False),
                ]
            )
        )

        self.flow.add(agent)
        self.flow.add(GoalItems(goals=GoalItem(goal_name=agent.name)))

        plans = self.get_plan()
        assert plans.best_plan
        assert len(plans.best_plan.plan) == 2
        assert len(plans.list_of_plans) == 3

    def test_one_optional_but_with_map(self) -> None:
        agent_0 = Operator("Agent 0")
        agent_0.add_output(
            SignatureItem(
                parameters=[
                    Parameter(item_id="x"),
                    Parameter(item_id="yy", item_type="type_y"),
                    Parameter(item_id="zz"),
                ]
            )
        )

        agent_1 = Operator("Agent 1")
        agent_1.add_input(
            SignatureItem(
                parameters=[
                    Parameter(item_id="x", required=False),
                ]
            )
        )

        agent_2 = Operator("Agent 2")
        agent_2.add_input(
            SignatureItem(
                parameters=[
                    Parameter(item_id="y", item_type="type_y", required=False),
                ]
            )
        )

        agent_3 = Operator("Agent 3")
        agent_3.add_input(
            SignatureItem(
                parameters=[
                    Parameter(item_id="z", required=False),
                ]
            )
        )

        list_of_agents = [agent_0, agent_1, agent_2, agent_3]

        self.flow.slot_options.add(SlotOptions.last_resort)
        self.flow.add(list_of_agents)
        self.flow.add(MappingItem(source_name="zz", target_name="z"))
        self.flow.add(GoalItems(goals=[GoalItem(goal_name=agent.name) for agent in list_of_agents[1:]]))

        plans = self.get_plan()
        assert plans.best_plan
        assert len(plans.best_plan.plan) == 6

        for step in plans.best_plan.plan:
            if step.name == BasicOperations.MAPPER.value:
                assert step.inputs == ["zz", "z"] or step.inputs == ["yy", "y"]

    def test_one_optional_but_with_memory(self) -> None:
        agent = Operator("Test Agent")
        agent.add_input(
            SignatureItem(
                parameters=[
                    Parameter(item_id="x"),
                    Parameter(item_id="y", required=False),
                    Parameter(item_id="z", required=False),
                ]
            )
        )

        self.flow.add(agent)
        self.flow.add(GoalItems(goals=GoalItem(goal_name=agent.name)))
        self.flow.add(MemoryItem(item_id="z", item_state=MemoryState.KNOWN))

        plans = self.get_plan()
        assert plans.best_plan
        assert len(plans.best_plan.plan) == 2
        assert set(plans.best_plan.plan[-1].inputs) == {"x", "z"}

    def test_one_optional_with_defensive_options(self) -> None:
        agent_0 = Operator("Agent 0")
        agent_0.add_input(
            SignatureItem(
                parameters=[
                    Parameter(item_id="x"),
                ]
            )
        )
        agent_0.add_output(
            SignatureItem(
                parameters=[
                    Parameter(item_id="y"),
                    Parameter(item_id="z"),
                ]
            )
        )

        agent_1 = Operator("Agent 1")
        agent_1.add_input(
            SignatureItem(
                parameters=[
                    Parameter(item_id="x"),
                ]
            )
        )

        agent_2 = Operator("Agent 2")
        agent_2.add_input(
            SignatureItem(
                parameters=[
                    Parameter(item_id="y"),
                ]
            )
        )

        agent_3 = Operator("Agent 3")
        agent_3.add_input(
            SignatureItem(
                parameters=[
                    Parameter(item_id="z"),
                ]
            )
        )

        list_of_agents = [agent_0, agent_1, agent_2, agent_3]

        self.flow.slot_options.add(SlotOptions.last_resort)
        self.flow.variable_life_cycle = set(LifeCycleOptions._value2member_map_.values())

        self.flow.add(list_of_agents)
        self.flow.add(GoalItems(goals=[GoalItem(goal_name=agent.name) for agent in list_of_agents[1:]]))
        self.flow.add(MemoryItem(item_id="x", item_state=MemoryState.UNCERTAIN))

        plans = self.get_plan()
        assert plans.best_plan
        assert len(plans.best_plan.plan) == 8
        assert len([step for step in plans.best_plan.plan if step.name == BasicOperations.CONFIRM.value]) == 4

    def test_one_optional_with_multi_instance(self) -> None:
        agent_0 = Operator("Agent 0")
        agent_0.add_input(
            SignatureItem(
                parameters=[
                    Parameter(item_id="x", required=False),
                ]
            )
        )

        agent_1 = Operator("Agent 1")
        agent_1.add_input(
            SignatureItem(
                parameters=[
                    Parameter(item_id="y", required=False),
                    Parameter(item_id="z", required=False),
                ]
            )
        )

        list_of_agents = [agent_0, agent_1]

        self.flow.variable_life_cycle = {LifeCycleOptions.confirm_on_slot}

        self.flow.add(list_of_agents)
        self.flow.add(GoalItems(goals=[GoalItem(goal_name=agent.name) for agent in list_of_agents]))

        self.flow.add(MemoryItem(item_id="item_123", item_state=MemoryState.UNCERTAIN))
        self.flow.add(MappingItem(source_name="item_123", target_name="y"))

        plans = self.get_plan()
        assert plans.best_plan
        assert len(plans.best_plan.plan) == 6

        for step in plans.best_plan.plan:
            if step.name.startswith(BasicOperations.MAPPER.value):
                assert step.inputs == ["item_123", "y"]

    def test_optional_but_in_constraint(self) -> None:
        agent = Operator("Agent 1")
        agent.add_input(
            SignatureItem(
                parameters=[
                    Parameter(item_id="x"),
                    Parameter(item_id="y", required=False),
                ],
                constraints=[Constraint(constraint="assert $x and $y", truth_value=ConstraintState.TRUE.value)],
            )
        )

        self.flow.add(agent)
        self.flow.add(GoalItems(goals=GoalItem(goal_name=agent.name)))

        plans = self.get_plan()
        assert plans.best_plan
        assert len(plans.best_plan.plan) == 4
        assert plans.best_plan.plan[2].constraint

    def test_optional_slot_options(self) -> None:
        agent = Operator("Test Agent")
        agent.add_input(
            SignatureItem(
                parameters=[
                    Parameter(item_id="x"),
                    Parameter(item_id="y", required=False),
                    Parameter(item_id="z", required=False),
                ]
            )
        )

        self.flow.add(agent)
        self.flow.add(GoalItems(goals=GoalItem(goal_name=agent.name)))
        self.flow.slot_options.add(SlotOptions.all_together)

        plans = self.get_plan()
        assert plans.best_plan
        assert len(plans.best_plan.plan) == 2
        assert set(plans.best_plan.plan[0].inputs) == {"x", "y", "z"}
