from tests.testing import BaseTestAgents
from nl2flow.compile.schemas import (
    SlotProperty,
    MappingItem,
    MemoryItem,
)

import pytest


class TestForbidden(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

    def test_probabilities(self) -> None:
        with pytest.raises(Exception):
            self.flow.add(SlotProperty(slot_name="slot", slot_desirability=1.5))

        with pytest.raises(Exception):
            self.flow.add(SlotProperty(slot_name="slot", slot_desirability=-2))

        with pytest.raises(Exception):
            self.flow.add(MappingItem(source_name="x", target_name="y", probability=-2))

        with pytest.raises(Exception):
            self.flow.add(MappingItem(source_name="x", target_name="y", probability=1.5))

    def test_conflicting_types(self) -> None:
        self.flow.add(
            [
                MemoryItem(item_id="zipcode"),
                MemoryItem(item_id="zipcode", item_type="address"),
            ]
        )

        with pytest.raises(Exception):
            self.flow.add(
                [
                    MemoryItem(item_id="zipcode", item_type="location"),
                ]
            )
