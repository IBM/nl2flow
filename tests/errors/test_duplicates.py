from tests.testing import BaseTestAgents
from nl2flow.plan.schemas import Step
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.options import GoalType
from nl2flow.compile.schemas import (
    TypeItem,
    Constraint,
    MemoryItem,
    SignatureItem,
    GoalItems,
    GoalItem,
)

import pytest


class TestDuplicates(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

    def test_duplicate_operators(self) -> None:
        agent_1 = Operator("Agent")
        agent_2 = Operator("Agent")
        self.flow.add([agent_1, agent_2])

        with pytest.raises(Exception):
            self.flow.validate()

    def test_duplicate_types(self) -> None:
        self.flow.add(
            [
                TypeItem(name="Contact"),
                TypeItem(name="Contact"),
            ]
        )

        with pytest.raises(Exception):
            self.flow.validate()

    def test_operator_hash_conflict(self) -> None:
        agent_1 = Operator("CASE CONFLICT")
        agent_2 = Operator("case conflict")
        self.flow.add([agent_1, agent_2])

        with pytest.raises(Exception):
            self.flow.validate()

    def test_typing_hash_conflict(self) -> None:
        self.flow.add(
            [
                TypeItem(name="Contact_Name"),
                TypeItem(name="Contact Name"),
            ]
        )

        with pytest.raises(Exception):
            self.flow.validate()

    def test_object_hash_conflict(self) -> None:
        self.flow.add(
            [
                MemoryItem(item_id="Object Name"),
                MemoryItem(item_id="object name"),
            ]
        )

        with pytest.raises(Exception):
            self.flow.validate()

    def test_object_hash_conflict_distributed_in_goal(self) -> None:
        self.flow.add(
            [
                MemoryItem(item_id="Object Name"),
                GoalItems(
                    goals=GoalItem(
                        goal_name="object_name", goal_type=GoalType.OBJECT_USED
                    )
                ),
            ]
        )

        with pytest.raises(Exception):
            self.flow.validate()

    def test_object_hash_conflict_distributed_in_operator(self) -> None:
        agent_1 = Operator("Agent")
        agent_1.add_input(SignatureItem(parameters=["x"]))

        self.flow.add([agent_1, MemoryItem(item_id="X")])

        with pytest.raises(Exception):
            self.flow.validate()

    def test_signature_hash_conflict(self) -> None:
        agent_1 = Operator("Agent")
        agent_1.add_input(SignatureItem(parameters=["x"]))
        agent_1.add_output(SignatureItem(parameters=["X"]))

        self.flow.add(agent_1)

        with pytest.raises(Exception):
            self.flow.validate()

    def test_constraint_operator_hash_conflict(self) -> None:
        agent_1 = Operator("Agent")
        agent_1.add_input(
            SignatureItem(
                parameters=["x"],
                constraints=[
                    Constraint(constraint_id="case conflict", parameters=["X"])
                ],
            )
        )
        self.flow.add(agent_1)

        with pytest.raises(Exception):
            self.flow.validate()

    def test_constraint_id_hash_conflict(self) -> None:
        agent_1 = Operator("Agent")
        agent_1.add_input(
            SignatureItem(
                parameters=["param"],
                constraints=[
                    Constraint(constraint_id="case conflict", parameters=["X"]),
                    Constraint(constraint_id="case_conflict", parameters=["Y"]),
                ],
            )
        )
        self.flow.add(agent_1)

        with pytest.raises(Exception):
            self.flow.validate()

    def test_constraint_id_hash_conflict_history(self) -> None:
        agent_1 = Operator("Agent")
        agent_1.add_input(
            SignatureItem(
                parameters=["param"],
                constraints=[
                    Constraint(constraint_id="case conflict", parameters=["X"]),
                ],
            )
        )
        self.flow.add(
            [
                agent_1,
                Constraint(
                    constraint_id="case_conflict", parameters=["Y"], truth_value=False
                ),
            ]
        )

        with pytest.raises(Exception):
            self.flow.validate()

    def test_step_hash_conflict_history(self) -> None:
        self.flow.add([Step(name="x"), Step(name="X")])

        with pytest.raises(Exception):
            self.flow.validate()

    def test_step_name_hash_conflict_history(self) -> None:
        agent_1 = Operator("Agent")
        agent_1.add_input(SignatureItem(parameters=["x"]))

        self.flow.add(agent_1)
        self.flow.add(Step(name="X"))

        with pytest.raises(Exception):
            self.flow.validate()
