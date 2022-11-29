from tests.testing import BaseTestAgents

# NOTE: This is part of dev dependencies
# noinspection PyPackageRequirements
import pytest


class TestDuplicates(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

    @pytest.mark.skip(reason="Coming soon.")
    def test_duplicate_operators(self) -> None:
        raise NotImplementedError

    @pytest.mark.skip(reason="Coming soon.")
    def test_duplicate_memory_items(self) -> None:
        raise NotImplementedError

    @pytest.mark.skip(reason="Coming soon.")
    def test_duplicate_types(self) -> None:
        raise NotImplementedError

    @pytest.mark.skip(reason="Coming soon.")
    def test_duplicate_signature_names(self) -> None:
        raise NotImplementedError
