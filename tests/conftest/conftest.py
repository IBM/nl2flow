from typing import Any, Generator
import pytest
import inspect


@pytest.mark.trylast
def pytest_configure(config: Any) -> None:
    terminal_reporter = config.pluginmanager.getplugin("terminalreporter")
    config.pluginmanager.register(TestDescriptionPlugin(terminal_reporter), "testdescription")  # type: ignore


class TestDescriptionPlugin:
    def __init__(self, terminal_reporter):  # type: ignore
        self.terminal_reporter = terminal_reporter
        self.desc = None

    def pytest_runtest_protocol(self, item: Any) -> None:
        self.desc = inspect.getdoc(item.obj)

    @pytest.mark.skip("Need only for PyTest Reflection")
    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_runtest_logstart(self, nodeid: Any, location: Any) -> Generator[Any]:  # type: ignore
        if self.terminal_reporter.verbosity == 0:
            yield
        else:
            self.terminal_reporter.write("\n")
            yield
            if self.desc:
                self.terminal_reporter.write(f"\n{self.desc} ")
