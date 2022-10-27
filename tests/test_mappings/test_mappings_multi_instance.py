from nl2flow.compile.options import BasicOperations
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.options import (
    MemoryState,
    MappingOptions,
    LifeCycleOptions,
)
from nl2flow.compile.schemas import (
    SignatureItem,
    MemoryItem,
    GoalItem,
    GoalItems,
    MappingItem,
    SlotProperty,
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

        # Some emails to play around with
        self.emails_in_memory = [
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

    def test_multi_instance_same_item(self) -> None:
        self.flow.add(self.emails_in_memory)
        self.flow.add(
            [
                MappingItem(source_name="from", target_name="to", probability=0.0),
                MappingItem(source_name="item12321", target_name="to", probability=1.0),
                MappingItem(
                    source_name="item12321", target_name="from", probability=1.0
                ),
            ]
        )

        goal = GoalItems(goals=GoalItem(goal_name="Email Agent"))
        self.flow.add(goal)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        for action in poi.plan:
            if action.name == BasicOperations.MAPPER.value:
                assert (
                    action.inputs[0].name == "item12321"
                ), "Item item12321 mapped twice"

    def test_multi_instance_from_memory_with_same_skill_no_preference(self) -> None:
        self.flow.add(self.emails_in_memory)

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

    def test_multi_instance_from_memory_with_same_skill_with_preference(self) -> None:
        self.flow.add(self.emails_in_memory)
        self.flow.add(
            [
                MappingItem(source_name="item55132", target_name="to", probability=1.0),
                MappingItem(
                    source_name="item12321", target_name="from", probability=1.0
                ),
            ]
        )

        goal = GoalItems(goals=GoalItem(goal_name="Email Agent"))
        self.flow.add(goal)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 5, "A plan of length 5."

        first_four_action_names = [action.name for action in poi.plan]
        assert (
            first_four_action_names.count(BasicOperations.SLOT_FILLER.value) == 2
            and first_four_action_names.count(BasicOperations.MAPPER.value) == 2
        ), "A plan of length 5 with 2 slot fills and 2 maps."

        for action in poi.plan[: len(poi.plan) - 1]:
            assert action.name in [
                BasicOperations.MAPPER.value,
                BasicOperations.SLOT_FILLER.value,
            ], "Either mapping or slot fill."

            if action.name == BasicOperations.MAPPER.value:
                assert [i.name for i in action.inputs] in [
                    ["item55132", "to"],
                    ["item12321", "from"],
                ], "Preferred mappings only."

    @pytest.mark.skip(reason="Coming soon.")
    def test_multi_instance_from_memory_with_multi_skill(self) -> None:
        """(x,y); x->A, y->A"""
        raise NotImplementedError

    @pytest.mark.skip(reason="Coming soon.")
    def test_multi_instance_with_iteration(self) -> None:
        """A->x, B->y, (x,y)-> C"""
        raise NotImplementedError

    def test_multi_instance_to_produce_with_multi_skill(self) -> None:
        goal = GoalItems(goals=GoalItem(goal_name="Copy Agent"))
        self.flow.add(goal)

        self.flow.mapping_options.add(MappingOptions.transitive)
        self.flow.add(
            MappingItem(source_name="source", target_name="target", probability=0.0)
        )

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 4, "A plan of length 4."
        assert all(
            action.name == BasicOperations.SLOT_FILLER.value
            for action in poi.plan[: len(poi.plan) - 1]
        ), "Three slot fills."

        # Testing multi-instance producer pattern with an agent instaed
        filename_producer_agent = Operator("Filename Producer Agent")
        filename_producer_agent.add_output(
            SignatureItem(
                parameters=[
                    MemoryItem(item_id="file", item_type="filename"),
                ]
            )
        )

        self.flow.add(filename_producer_agent)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 6, "A plan of length 6."
        assert [action.name for action in poi.plan[: len(poi.plan) - 1]].count(
            "Filename Producer Agent"
        ) == 2, "Two instances of the new agent."

        for action in poi.plan:
            if action.name == BasicOperations.MAPPER.value:
                assert action.inputs[0].name == "file", "... map file item twice ..."
                assert action.inputs[1].name in [
                    "source",
                    "target",
                ], "... and map to the target agent inputs."

    def test_multi_instance_with_multi_skill_and_confirmation(self) -> None:
        goal = GoalItems(goals=GoalItem(goal_name="Copy Agent"))
        self.flow.add(goal)

        filename_producer_agent = Operator("Filename Producer Agent")
        filename_producer_agent.add_input(
            SignatureItem(
                parameters=[
                    MemoryItem(item_id="something random", item_type="random"),
                ]
            )
        )
        filename_producer_agent.add_output(
            SignatureItem(
                parameters=[
                    MemoryItem(item_id="file", item_type="filename"),
                ]
            )
        )

        self.flow.add(filename_producer_agent)
        self.flow.add(
            [
                SlotProperty(
                    slot_name="source", slot_desirability=0, propagate_desirability=True
                ),
                MappingItem(
                    source_name="source", target_name="target", probability=0.0
                ),
            ]
        )

        self.flow.variable_life_cycle.add(LifeCycleOptions.uncertain_on_use)
        self.flow.mapping_options.add(MappingOptions.transitive)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 8, "A plan of length 8."
        assert [action.name for action in poi.plan[: len(poi.plan) - 1]].count(
            "Filename Producer Agent"
        ) == 2, "Two instances of the new agent."
        assert BasicOperations.CONFIRM.value in [
            action.name for action in poi.plan[: len(poi.plan) - 1]
        ], "A confirmation step."

        for action in poi.plan:
            if action.name == BasicOperations.MAPPER.value:
                assert action.inputs[0].name == "file", "... map file item twice ..."
                assert action.inputs[1].name in [
                    "source",
                    "target",
                ], "... and map to the target agent inputs."
