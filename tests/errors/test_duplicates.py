from tests.testing import BaseTestAgents
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.schemas import TypeItem

import pytest


class TestDuplicates(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

    def test_duplicate_operators(self) -> None:
        agent_1 = Operator("CASE CONFLICT")
        agent_2 = Operator("case conflict")
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
