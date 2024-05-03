from abc import ABC, abstractmethod
from typing import Union, List
from difflib import Differ
from re import match
from warnings import warn

from nl2flow.plan.schemas import RawPlan
from nl2flow.plan.planners import Kstar
from nl2flow.plan.options import TIMEOUT
from nl2flow.compile.flow import Flow
from nl2flow.compile.options import BasicOperations
from nl2flow.compile.schemas import ClassicalPlanReference, Step, Constraint
from nl2flow.debug.schemas import Report, SolutionQuality, StepDiff, DiffAction

PLANNER = Kstar()
DIFFER = Differ()


class Debugger(ABC):
    def __init__(self, instance: Flow) -> None:
        self.flow = instance

    @abstractmethod
    def debug_raw_plan(self, raw_plan: RawPlan) -> None:
        pass

    @abstractmethod
    def debug(self, list_of_tokens: List[str], debug: SolutionQuality, timeout: int = TIMEOUT) -> Report:
        pass


class BasicDebugger(Debugger):
    def debug_raw_plan(self, raw_plan: RawPlan) -> None:
        raise NotImplementedError

    @staticmethod
    def parse_parameters(prefix: str, signature: str) -> List[str]:
        m = match(rf"{prefix}\((?P<parameters>.*)\)", signature)

        if m is not None:
            re_found = m.groupdict()
            p = re_found.get("parameters", None)

            if not p:
                raise ValueError(f"Could not parse parameter of {prefix} operation: {signature}")
            else:
                p_list = p.split(",")
                return [p.strip() for p in p_list]
        else:
            raise ValueError(f"Could not parse {prefix} operation: {signature}")

    def parse_token(self, token: str) -> Union[Step, Constraint, None]:
        # noinspection PyBroadException
        try:
            new_action = None

            for operation in BasicOperations:
                action_name = operation.value

                if token.startswith(action_name):
                    if token.startswith(BasicOperations.CONSTRAINT.value):
                        new_action = Constraint(
                            constraint=token.replace(f"{BasicOperations.CONSTRAINT.value} ", "")
                            .replace("not ", "")
                            .strip(),
                            truth_value=not token.startswith(f"{BasicOperations.CONSTRAINT.value} not"),
                        )
                    else:
                        new_action = Step(
                            name=action_name,
                            parameters=self.parse_parameters(action_name, token),
                        )

            if new_action is None:
                action_split = token.split(" = ")
                agent_signature = action_split[0] if len(action_split) == 1 else action_split[1]

                agent_signature_split = agent_signature.split("(")
                action_name = agent_signature_split[0]
                parameters = (
                    [] if agent_signature_split[1] == ")" else self.parse_parameters(action_name, agent_signature)
                )

                new_action = Step(
                    name=action_name,
                    parameters=parameters,
                )

            if new_action:
                return new_action
            else:
                warn(f"Unrecognized token: {token}", SyntaxWarning)
                return None

        except Exception as e:
            warn(f"Unrecognized token: {token}, {e}")
            return None

    def parse_tokens(self, list_of_tokens: List[str]) -> ClassicalPlanReference:
        parsed_plan = ClassicalPlanReference()

        for index, token in enumerate(list_of_tokens):
            token = token.replace(f"[{index}]", "", 1)
            token = token.strip()

            new_action = self.parse_token(token)

            if new_action:
                parsed_plan.plan.append(new_action)
            else:
                continue

        return parsed_plan

    def plan_diff_str2obj(self, diff_str: List[str]) -> List[StepDiff]:
        diff_obj = []
        for item in diff_str:
            item = item.strip()
            new_action = None
            for diff_action in DiffAction:
                if item.startswith(diff_action.value):
                    item = item.replace(f"{diff_action.value} ", "")
                    parsed_token = self.parse_token(item) or item
                    new_action = StepDiff(
                        diff_type=diff_action,
                        step=parsed_token,
                    )

            if not new_action:
                parsed_token = self.parse_token(item) or item
                new_action = StepDiff(
                    step=parsed_token,
                )

            diff_obj.append(new_action)

        return diff_obj

    def debug(self, list_of_tokens: List[str], debug: SolutionQuality, timeout: int = TIMEOUT) -> Report:
        PLANNER.timeout = timeout

        reference_plan: ClassicalPlanReference = self.parse_tokens(list_of_tokens)
        self.flow.add(reference_plan)

        planner_response = self.flow.plan_it(PLANNER, debug_flag=debug)
        new_report = Report(
            report_type=SolutionQuality.SOUND,
            planner_response=planner_response,
            reference=reference_plan,
        )

        if len(planner_response.list_of_plans) > 0:
            first_plan = planner_response.list_of_plans[0]
            first_plan_stringify = PLANNER.pretty_print_plan(first_plan, line_numbers=False).split("\n")

            new_report.plan_diff_str = list(DIFFER.compare(list_of_tokens, first_plan_stringify))
            new_report.plan_diff_obj = self.plan_diff_str2obj(new_report.plan_diff_str)

            new_report.determination = len([d for d in new_report.plan_diff_obj if d.diff_type is not None]) == 0

        return new_report
