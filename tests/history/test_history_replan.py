from tests.testing import BaseTestAgents
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.options import (
    MemoryState,
    MappingOptions,
    LifeCycleOptions,
    BasicOperations,
)
from nl2flow.compile.schemas import (
    Step,
    Parameter,
    MemoryItem,
    SignatureItem,
    SlotProperty,
    MappingItem,
    GoalItems,
    GoalItem,
)


class TestHistoryReplan(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

        # Email service require from, to, cc, bcc, body and attachments
        email_agent = Operator("Email Agent")
        email_agent.add_input(
            SignatureItem(
                parameters=[
                    Parameter(item_id="from", item_type="Email ID"),
                    Parameter(item_id="to", item_type="Email ID"),
                    "body",
                    "attachments",
                ]
            )
        )

        self.flow.mapping_options.add(MappingOptions.transitive)
        self.flow.add(
            [
                email_agent,
                SlotProperty(slot_name="from", slot_desirability=0.0),
                SlotProperty(slot_name="to", slot_desirability=0.0),
                MappingItem(source_name="from", target_name="to", probability=0.0),
            ]
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

    def test_history_block(self) -> None:
        goal = GoalItems(goals=GoalItem(goal_name="Email Agent"))
        self.flow.add(goal)

        plans = self.get_plan()
        assert not plans.list_of_plans, "There should be no plans."

        self.flow.mapping_options.add(MappingOptions.prohibit_direct)
        self.flow.add(self.emails_in_memory[:2])

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        forbidden_parameters = [
            self.emails_in_memory[0],
            self.emails_in_memory[1],
            "body",
            "attachments",
        ]

        self.flow.add(
            [
                MappingItem(source_name="item14311", target_name="from", probability=0.0),
                Step(
                    name="Email Agent",
                    parameters=forbidden_parameters,
                ),
            ]
        )

        plans = self.get_plan()
        assert not plans.list_of_plans, "There should be no plans."

    def test_history_replan(self) -> None:
        goal = GoalItems(goals=GoalItem(goal_name="Email Agent"))
        self.flow.add(goal)

        self.flow.variable_life_cycle.add(LifeCycleOptions.uncertain_on_use)
        self.flow.mapping_options.add(MappingOptions.prohibit_direct)
        self.flow.add(self.emails_in_memory)

        forbidden_parameters = [
            self.emails_in_memory[0],
            self.emails_in_memory[1],
            "body",
            "attachments",
        ]

        self.flow.add(
            [
                MappingItem(source_name="item14311", target_name="from", probability=0.0),
                Step(
                    name="Email Agent",
                    parameters=forbidden_parameters,
                ),
            ]
        )

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        for poi in plans.list_of_plans:
            cached_params = set()
            for action in poi.plan:
                if action.name == BasicOperations.MAPPER.value:
                    cached_params.add(action.inputs[0])

            assert cached_params != {"item14311", "item12321"}, "Use different emails."
