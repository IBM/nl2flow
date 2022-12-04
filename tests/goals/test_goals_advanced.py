from tests.testing import BaseTestAgents
from nl2flow.plan.schemas import Step, Parameter
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.options import (
    MemoryState,
    MappingOptions,
    LifeCycleOptions,
    BasicOperations,
    GoalType,
)
from nl2flow.compile.schemas import (
    MemoryItem,
    SignatureItem,
    MappingItem,
    GoalItems,
    GoalItem,
)

import pytest


class TestGoalsAdvanced(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

    def test_goal_with_operator_and_parameters(self) -> None:
        def check_this_plan() -> None:
            assert plans.list_of_plans, "There should be plans."

            poi = plans.list_of_plans[0]
            assert len(poi.plan) == 6, "Plan of six steps."
            assert (
                poi.plan[0].name == BasicOperations.MAPPER.value
                and len(poi.plan[0].inputs) == 8
                and {poi.plan[0].inputs[i].item_id for i in range(0, 8, 2)}
                == set(desired_goal_parameters)
            ), "A giant mapping action with all the desired mappings ..."
            assert {action.name for action in poi.plan[1:-1]} == {
                BasicOperations.CONFIRM.value
            }, "... followed by four confirms ...."
            assert (
                poi.plan[5].name == "Email Agent"
            ), "... ending the final target agent."

        email_agent = Operator("Email Agent")
        email_agent.max_try = 2
        email_agent.add_input(
            SignatureItem(
                parameters=[
                    Parameter(item_id="from", item_type="Email ID"),
                    Parameter(item_id="to", item_type="Email ID"),
                    Parameter(item_id="body", item_type="Text"),
                    "attachments",
                ]
            )
        )

        desired_goal_parameters = [
            "tchakra2",
            "krtalamad",
            "message",
            "applicant_resume",
        ]

        self.flow.variable_life_cycle.add(LifeCycleOptions.confirm_on_mapping)
        self.flow.mapping_options.add(MappingOptions.group_maps)
        self.flow.add(
            [
                email_agent,
                MemoryItem(
                    item_id="message", item_type="Text", item_state=MemoryState.KNOWN
                ),
                MemoryItem(
                    item_id="applicant_resume",
                    item_type="PDF",
                    item_state=MemoryState.KNOWN,
                ),
                MappingItem(
                    source_name="applicant_resume",
                    target_name="attachments",
                    probability=1.0,
                ),
                MemoryItem(
                    item_id="tchakra2",
                    item_type="Email ID",
                    item_state=MemoryState.KNOWN,
                ),
                MemoryItem(
                    item_id="krtalamad",
                    item_type="Email ID",
                    item_state=MemoryState.KNOWN,
                ),
                GoalItems(
                    goals=GoalItem(
                        goal_name=Step(
                            name="Email Agent",
                            parameters=desired_goal_parameters,
                        ),
                        goal_type=GoalType.OPERATOR,
                    )
                ),
            ]
        )

        plans = self.get_plan()
        check_this_plan()

        self.flow.add(
            Step(
                name="Email Agent",
                parameters=desired_goal_parameters,
            )
        )

        plans = self.get_plan()
        check_this_plan()

        self.flow.add(
            Step(
                name="Email Agent",
                parameters=desired_goal_parameters,
            )
        )

        plans = self.get_plan()
        assert not plans.list_of_plans, "There should be no plans."

    @pytest.mark.skip(reason="Coming soon.")
    def test_and_or_basic(self) -> None:
        raise NotImplementedError

    @pytest.mark.skip(reason="Coming soon.")
    def test_or_and_basic(self) -> None:
        raise NotImplementedError

    @pytest.mark.skip(reason="Coming soon.")
    def test_and_or_with_type(self) -> None:
        raise NotImplementedError

    @pytest.mark.skip(reason="Coming soon.")
    def test_or_and_with_type(self) -> None:
        raise NotImplementedError
