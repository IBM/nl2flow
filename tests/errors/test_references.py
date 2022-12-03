from tests.testing import BaseTestAgents
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.schemas import (
    SignatureItem,
    SlotProperty,
    MappingItem,
    MemoryItem,
)

import pytest


class TestReferences(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

    def test_unknown_slot(self) -> None:
        self.flow.add(MappingItem(source_name="x", target_name="y", probability=0.5))
        with pytest.raises(Exception):
            self.flow.validate()

        self.flow.add([MemoryItem(item_id="x"), MemoryItem(item_id="y")])
        assert self.flow.validate()

    def test_unknown_map(self) -> None:
        self.flow.add(SlotProperty(slot_name="x", slot_desirability=1.0))
        with pytest.raises(Exception):
            self.flow.validate()

        operator = Operator("Agent")
        operator.add_input(SignatureItem(parameters=["x"]))

        self.flow.add(operator)
        assert self.flow.validate()
