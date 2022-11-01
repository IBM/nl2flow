from tests.testing import BaseTestAgents

# NOTE: This is part of dev dependencies
# noinspection PyPackageRequirements
import pytest


class TestGoalsAdvanced(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

    @pytest.mark.skip(reason="Coming soon.")
    def test_goal_with_operator_and_parameters(self) -> None:
        raise NotImplementedError

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
