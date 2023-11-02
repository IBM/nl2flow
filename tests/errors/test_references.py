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

    def test_unknown_map(self) -> None:
        with pytest.raises(Exception):
            self.flow.add(MappingItem(source_name="x", target_name="y", probability=0.5))

        with pytest.raises(Exception):
            self.flow.add([MemoryItem(item_id="x"), MemoryItem(item_id="y")])
            self.flow.add(MappingItem(source_name="x", target_name="y", probability=0.5))

        operator = Operator("Agent")
        operator.add_input(SignatureItem(parameters=["x", "y"]))

        self.flow.add(operator)
        self.flow.add([MemoryItem(item_id="x"), MemoryItem(item_id="y")])
        self.flow.add(MappingItem(source_name="x", target_name="y", probability=0.5))

    def test_unknown_slot(self) -> None:
        with pytest.raises(Exception):
            self.flow.add(SlotProperty(slot_name="x", slot_desirability=1.0))

        operator = Operator("Agent")
        operator.add_input(SignatureItem(parameters=["x"]))

        self.flow.add(operator)
        self.flow.add(SlotProperty(slot_name="x", slot_desirability=1.0))

    def test_unknown_start_and_end(self) -> None:
        self.flow.set_start(None)
        self.flow.set_end(None)

        with pytest.raises(Exception):
            self.flow.set_start("Agent X")

        with pytest.raises(Exception):
            self.flow.set_end("Agent X")
