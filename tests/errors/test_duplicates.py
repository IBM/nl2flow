from tests.testing import BaseTestAgents
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.options import GoalType
from nl2flow.compile.flow import Flow
from nl2flow.compile.schemas import (
    TypeItem,
    MemoryItem,
    SignatureItem,
    GoalItems,
    GoalItem,
    Step,
)

import pytest


class TestDuplicates(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

    def test_duplicate_operators(self) -> None:
        agent_1 = Operator("Agent")
        agent_2 = Operator("Agent")

        with pytest.raises(Exception):
            self.flow.add([agent_1, agent_2])

    def test_relaxed_assignment(self) -> None:
        agent_1 = Operator("Agent")
        agent_2 = Operator("Agent")

        flow_definition = self.flow.flow_definition

        new_flow = Flow(name="Test Validated Assignment")
        new_flow.flow_definition = flow_definition

        with pytest.raises(Exception):
            self.flow.add([agent_1, agent_2])

        new_flow = Flow(name="Test Relaxed Assignment", validate=False)
        new_flow.flow_definition = flow_definition
        new_flow.add([agent_1, agent_2])

    def test_duplicate_types(self) -> None:
        with pytest.raises(Exception):
            self.flow.add(
                [
                    TypeItem(name="Contact"),
                    TypeItem(name="Contact"),
                ]
            )

    def test_operator_hash_conflict(self) -> None:
        agent_1 = Operator("CASE CONFLICT")
        agent_2 = Operator("case conflict")

        with pytest.raises(Exception):
            self.flow.add([agent_1, agent_2])

    def test_typing_hash_conflict(self) -> None:
        with pytest.raises(Exception):
            self.flow.add(
                [
                    TypeItem(name="Contact_Name"),
                    TypeItem(name="Contact Name"),
                ]
            )

    def test_object_hash_conflict(self) -> None:
        with pytest.raises(Exception):
            self.flow.add(
                [
                    MemoryItem(item_id="Object Name"),
                    MemoryItem(item_id="object name"),
                ]
            )

    def test_object_hash_conflict_distributed_in_goal(self) -> None:
        with pytest.raises(Exception):
            self.flow.add(
                [
                    MemoryItem(item_id="Object Name"),
                    GoalItems(goals=GoalItem(goal_name="object_name", goal_type=GoalType.OBJECT_USED)),
                ]
            )

    def test_object_hash_conflict_distributed_in_operator(self) -> None:
        agent_1 = Operator("Agent")
        agent_1.add_input(SignatureItem(parameters=["x"]))

        with pytest.raises(Exception):
            self.flow.add([agent_1, MemoryItem(item_id="X")])

    def test_signature_hash_conflict(self) -> None:
        agent_1 = Operator("Agent")
        agent_1.add_input(SignatureItem(parameters=["x"]))
        agent_1.add_output(SignatureItem(parameters=["X"]))

        with pytest.raises(Exception):
            self.flow.add(agent_1)

    def test_step_hash_conflict_history(self) -> None:
        with pytest.raises(Exception):
            self.flow.add([Step(name="x"), Step(name="X")])

    def test_step_name_hash_conflict_history(self) -> None:
        agent_1 = Operator("Agent")
        agent_1.add_input(SignatureItem(parameters=["x"]))

        self.flow.add(agent_1)

        with pytest.raises(Exception):
            self.flow.add(Step(name="X"))
