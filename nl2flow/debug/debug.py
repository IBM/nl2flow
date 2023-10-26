from nl2flow.compile.schemas import FlowDefinition
from nl2flow.compile.flow import Flow
from nl2flow.debug.schemas import StoryBoard, Report
from abc import ABC, abstractmethod


class Debugger(ABC):
    def __init__(self, flow: FlowDefinition) -> None:
        self.flow = Flow(name=flow.name)
        self.flow_definition = flow

    @abstractmethod
    def debug(self, storyboard: StoryBoard) -> Report:
        pass


class BasicDebugger(Debugger):
    def debug(self, storyboard: StoryBoard) -> Report:
        report: Report = Report(id=storyboard.id)
        return report


class NoisyDebugger(Debugger):
    def debug(self, storyboard: StoryBoard) -> Report:
        raise NotImplementedError
