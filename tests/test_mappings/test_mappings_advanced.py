from nl2flow.compile.schemas import GoalItem, GoalItems, MappingItem
from nl2flow.compile.options import BasicOperations, LifeCycleOptions
from nl2flow.plan.schemas import Action
from tests.testing import BaseTestAgents

from collections import Counter

# NOTE: This is part of dev dependencies
# noinspection PyPackageRequirements
import pytest


class TestMappingsAdvanced(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

    def test_mapper_basic_with_confirm(self) -> None:
        self.flow.add(
            [
                MappingItem(source_name="Username", target_name="Email"),
                MappingItem(source_name="Account Info", target_name="AccountID"),
            ]
        )

        goal = GoalItems(goals=GoalItem(goal_name="Credit Score API"))
        self.flow.add(goal)

        self.flow.variable_life_cycle.add(LifeCycleOptions.confirm_on_mapping)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 6, "The plan should have 6 steps."

        step_1: Action = poi.plan[0]
        assert step_1.name == "User Info", "Call user info agent to map later."

        assert Counter(
            2 * [BasicOperations.MAPPER.value, BasicOperations.CONFIRM.value]
        ) == Counter(
            [step.name for step in poi.plan[1 : len(poi.plan) - 1]]
        ), "Followed by two mappings and two confirms."

        step_6: Action = poi.plan[5]
        assert (
            step_6.name == "Credit Score API"
        ), "Final action should be the goal action."

    @pytest.mark.skip(reason="Coming soon.")
    def test_mapper_with_multi_instance_without_typing(self) -> None:
        raise NotImplementedError

    @pytest.mark.skip(reason="Coming soon.")
    def test_mapper_with_multi_instance_and_typing(self) -> None:
        raise NotImplementedError
