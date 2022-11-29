from tests.testing import BaseTestAgents

# NOTE: This is part of dev dependencies
# noinspection PyPackageRequirements
import pytest


class TestReferences(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

    @pytest.mark.skip(reason="Coming soon.")
    def test_unknown_slot(self) -> None:
        raise NotImplementedError

    @pytest.mark.skip(reason="Coming soon.")
    def test_unknown_map(self) -> None:
        raise NotImplementedError
