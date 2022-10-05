# from nl2flow.compile.schemas import GoalItem, GoalItems
# from nl2flow.compile.options import BasicOperations, SlotOptions
# from nl2flow.plan.schemas import Action
from tests.testing import BaseTestAgents

# from collections import Counter

# NOTE: This is part of dev dependencies
# noinspection PyPackageRequirements
import pytest


class TestMappingsAdvanced(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

    @pytest.mark.skip(reason="Coming soon.")
    def test_mapper_with_multi_instance(self) -> None:
        raise NotImplementedError
