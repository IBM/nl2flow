from nl2flow.compile.flow import Flow
from nl2flow.compile.schemas import MemoryItem


def test_basic() -> None:
    new_flow = Flow("Basic Test")
    new_flow.add(MemoryItem(item_id="id123", item_type="generic"))

    assert new_flow is not None, "JAARL"
