from tests.testing import BaseTestAgents
from tests.mappings.test_mappings_basic import TestMappingsBasic

from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.schemas import (
    GoalItem,
    GoalItems,
    MemoryItem,
    TypeItem,
    SignatureItem,
)

import pytest


class TestTypingBasic(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

    def test_typing_with_concept_tags(self) -> None:
        self.flow.add(
            [
                MemoryItem(item_id="Username", item_type="contact-info"),
                MemoryItem(item_id="Account Info", item_type="id"),
                MemoryItem(item_id="Email", item_type="contact-info"),
                MemoryItem(item_id="AccountID", item_type="id"),
            ]
        )

        goal = GoalItems(goals=GoalItem(goal_name="Credit Score API"))
        self.flow.add(goal)

        plans = self.get_plan()
        TestMappingsBasic.check_basic_mapping_plan(plans)

    def test_typing_with_hierarchy(self) -> None:
        self.flow.add(TypeItem(name="Contact", parent="Person"))
        self.flow.add(
            [
                MemoryItem(item_id="Username", item_type="Person"),
                MemoryItem(item_id="Account Info", item_type="id"),
                MemoryItem(item_id="Email", item_type="Contact"),
                MemoryItem(item_id="AccountID", item_type="id"),
            ]
        )

        goal = GoalItems(goals=GoalItem(goal_name="Credit Score API"))
        self.flow.add(goal)

        plans = self.get_plan()
        TestMappingsBasic.check_basic_mapping_plan(plans)

    @pytest.mark.skip(reason="This is not supposed to pass. Illustration.")
    def test_typing_with_costly_hierarchy(self) -> None:
        self.flow.add(
            [
                TypeItem(name="HigherPerson", children=["Person"]),
                TypeItem(name="Contact", parent="Person"),
            ]
        )
        self.flow.add(
            [
                MemoryItem(item_id="Username", item_type="Person"),
                MemoryItem(item_id="HigherUsername", item_type="HigherPerson"),
                MemoryItem(item_id="Account Info", item_type="id"),
                MemoryItem(item_id="Email", item_type="Contact"),
                MemoryItem(item_id="AccountID", item_type="id"),
            ]
        )

        imposter_user_info_agent = Operator("Imposter User Info")
        imposter_user_info_agent.add_output(
            [
                SignatureItem(parameters=["HigherUsername"]),
                SignatureItem(parameters=["Account Info"]),
            ]
        )
        self.flow.add(imposter_user_info_agent)

        goal = GoalItems(goals=GoalItem(goal_name="Credit Score API"))
        self.flow.add(goal)

        plans = self.get_plan()
        TestMappingsBasic.check_basic_mapping_plan(plans)

        poi = plans.list_of_plans[0]
        assert "Username" in [step.inputs[0].item_id for step in poi.plan[1:3]], "Make sure Username is used."
