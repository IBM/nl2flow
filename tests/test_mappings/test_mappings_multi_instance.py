from nl2flow.compile.options import BasicOperations
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.options import MemoryState, MappingOptions
from nl2flow.compile.schemas import (
    SignatureItem,
    MemoryItem,
    GoalItem,
    GoalItems,
    MappingItem,
)

from tests.testing import BaseTestAgents
from collections import Counter

# NOTE: This is part of dev dependencies
# noinspection PyPackageRequirements
import pytest


class TestMappingsMultiInstance(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

        # Email service require from, to, cc, bcc, body and attachments
        email_agent = Operator("Email Agent")
        email_agent.add_input(
            SignatureItem(
                parameters=[
                    MemoryItem(item_id="from", item_type="Email ID"),
                    MemoryItem(item_id="to", item_type="Email ID"),
                    "body",
                    "attachments",
                ]
            )
        )

        # Copy agent copies a file from
        copy_agent = Operator("Copy Agent")
        copy_agent.add_input(
            SignatureItem(
                parameters=[
                    MemoryItem(item_id="source", item_type="filename"),
                    MemoryItem(item_id="target", item_type="filename"),
                    MemoryItem(item_id="destination", item_type="directory"),
                ]
            )
        )

        self.flow.add(
            [
                email_agent,
                copy_agent,
            ]
        )

    @pytest.mark.skip(reason="Coming soon.")
    def test_multi_instance_same_item(self) -> None:
        raise NotImplementedError

    def test_multi_instance_pitfall(self) -> None:
        goal = GoalItems(goals=GoalItem(goal_name="Email Agent"))
        self.flow.add(goal)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        index_of_map = [action.name for action in poi.plan].index(
            BasicOperations.MAPPER.value
        )

        assert index_of_map > 0, "There should be a rogue mapping action"
        assert Counter([o.name for o in poi.plan[index_of_map].inputs]) == Counter(
            ["to", "from"]
        ), "A rogue to-from mapping."

        self.flow.add(
            MappingItem(source_name="to", target_name="from", probability=0.0)
        )
        self.flow.mapping_options.add(MappingOptions.transitive)

        pddl, _ = self.flow.compile_to_pddl()

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert (
            len(poi.plan) == 5
        ), "A plan of length 5 full of slot fills and no mapping."

        first_four_action_names = [
            action.name for action in poi.plan[: len(poi.plan) - 1]
        ]
        assert all(
            [o == BasicOperations.SLOT_FILLER.value for o in first_four_action_names]
        ), "A plan of length 5 full of slot fills and no mapping."

    def test_multi_instance_from_memory_with_same_skill_no_preference(self) -> None:
        self.flow.add(
            [
                MemoryItem(
                    item_id="item12321",
                    item_type="Email ID",
                    item_state=MemoryState.KNOWN,
                ),
                MemoryItem(
                    item_id="item14311",
                    item_type="Email ID",
                    item_state=MemoryState.KNOWN,
                ),
                MemoryItem(
                    item_id="item55132",
                    item_type="Email ID",
                    item_state=MemoryState.KNOWN,
                ),
            ]
        )

        goal = GoalItems(goals=GoalItem(goal_name="Email Agent"))
        self.flow.add(goal)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 5, "A plan of length 5."

        first_four_action_names = [
            action.name for action in poi.plan[: len(poi.plan) - 1]
        ]
        assert (
            first_four_action_names.count(BasicOperations.SLOT_FILLER.value) == 2
            and first_four_action_names.count(BasicOperations.MAPPER.value) == 2
        ), "A plan of length 5 with 2 slot fills and 2 maps."

    @pytest.mark.skip(reason="Coming soon.")
    def test_multi_instance_from_memory_with_same_skill_with_preference(self) -> None:
        """(x,y); x,y->A"""
        raise NotImplementedError

    @pytest.mark.skip(reason="Coming soon.")
    def test_multi_instance_from_memory_with_multi_skill(self) -> None:
        """(x,y); x->A, y->A"""
        raise NotImplementedError

    @pytest.mark.skip(reason="Coming soon.")
    def test_multi_instance_to_produce_with_multi_skill(self) -> None:
        """A->x, B->y, (x,y)-> C"""
        raise NotImplementedError

    @pytest.mark.skip(reason="Coming soon.")
    def test_multi_instance_with_multi_skill_and_confirmation(self) -> None:
        """A->x, B->y, (x,y)-> C"""
        raise NotImplementedError

    @pytest.mark.skip(reason="Coming soon.")
    def test_multi_instance_with_iteration(self) -> None:
        """A->x, B->y, (x,y)-> C"""
        raise NotImplementedError
