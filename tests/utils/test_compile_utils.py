from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.schemas import SignatureItem, Parameter, Outcome
from nl2flow.compile.options import TypeOptions
from nl2flow.compile.flow import Flow

from nl2flow.compile.basic_compilations.utils import (
    unpack_list_of_signature_items,
    get_item_source_map,
    get_agent_to_slot_map,
    get_item_requirement_map,
    get_type_of_constant,
    is_this_a_datum_type,
    is_this_a_datum,
    generate_new_objects,
)

import pytest


class TestCompileUtils:
    def setup_method(self) -> None:
        operator_a = Operator("A")

        operator_a.add_input(SignatureItem(parameters="a1"))
        operator_a.add_input(SignatureItem(parameters=["a2", "a3"]))
        operator_a.add_input(SignatureItem(parameters=Parameter(item_id="a4")))
        operator_a.add_input(SignatureItem(parameters=[Parameter(item_id="a5"), Parameter(item_id="a6")]))

        operator_a.add_output(SignatureItem(parameters=Parameter(item_id="ao1")))
        operator_a.add_output(SignatureItem(parameters=Parameter(item_id="ao2")))

        operator_b = Operator("B")

        param_b = Parameter(item_id="b1", item_type="type_B")
        operator_b.add_input(SignatureItem(parameters=param_b))
        operator_b.add_input(SignatureItem(parameters=["a1", "b2"]))

        operator_b.add_output(SignatureItem(parameters="ao2"))

        self.flow = Flow(name="Utils Test")
        self.flow.add([operator_a, operator_b])
        self.flow.compile_to_pddl()

    def test_unpack_nested_signatures(self) -> None:
        operators = self.flow.flow_definition.operators
        operator_a = next(x for x in operators if x.name == "A")
        operator_b = next(x for x in operators if x.name == "B")

        assert unpack_list_of_signature_items(operator_a.inputs) == {"a1", "a2", "a3", "a4", "a5", "a6"}
        assert unpack_list_of_signature_items(operator_b.inputs) == {"a1", "b1", "b2"}

        outputs_a = operator_a.outputs if isinstance(operator_a.outputs, Outcome) else operator_a.outputs[0]
        assert unpack_list_of_signature_items(outputs_a.outcomes) == {"ao1", "ao2"}

        outputs_b = operator_b.outputs if isinstance(operator_b.outputs, Outcome) else operator_b.outputs[0]
        assert unpack_list_of_signature_items(outputs_b.outcomes) == {"ao2"}

    def test_get_item_source_map(self) -> None:
        item_source_map = get_item_source_map(self.flow.compilation)
        assert item_source_map["ao1"] == {"a"}
        assert item_source_map["ao2"] == {"a", "b"}

    def test_get_agent_to_slot_map(self) -> None:
        agent_to_slot_map = get_agent_to_slot_map(self.flow.compilation)
        assert agent_to_slot_map["a"] == {"a1", "a2", "a3", "a4", "a5", "a6"}
        assert agent_to_slot_map["b"] == {"a1", "b1", "b2"}

    def test_get_item_requirement_map(self) -> None:
        item_requirement_map = get_item_requirement_map(self.flow.compilation)
        assert item_requirement_map["a1"] == {"a", "b"}
        assert item_requirement_map["a2"] == {"a"}
        assert item_requirement_map["b1"] == {"b"}

    def test_get_type_of_constant(self) -> None:
        assert get_type_of_constant(self.flow.compilation, constant="a1") == TypeOptions.ROOT.value
        assert get_type_of_constant(self.flow.compilation, constant="b1") == "type_b"

    def test_is_this_a_datum_type(self) -> None:
        assert not is_this_a_datum_type(type_name=TypeOptions.RETRY.value)
        assert is_this_a_datum_type(type_name=TypeOptions.ROOT.value)
        assert is_this_a_datum_type(type_name="type_b")

    def test_is_this_a_datum(self) -> None:
        assert is_this_a_datum(self.flow.compilation, constant="b1")

        with pytest.raises(ValueError):
            is_this_a_datum(self.flow.compilation, constant="type_b")

    def test_generate_new_objects(self) -> None:
        assert generate_new_objects(type_name="type_b", num_lookahead=2) == [
            "new_object_type_b_0",
            "new_object_type_b_1",
        ]
