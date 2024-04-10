import re
from abc import ABC, abstractmethod
from typing import Union, List

from nl2flow.plan.schemas import RawPlan

# from nl2flow.plan.options import TIMEOUT
from nl2flow.compile.schemas import PDDL, Step, Constraint
from nl2flow.compile.options import BasicOperations
from nl2flow.compile.flow import Flow
from nl2flow.debug.schemas import ClassicalPlanReference

# , Report, SolutionQuality


class Debugger(ABC):
    def __init__(self, instance: Union[Flow, PDDL]) -> None:
        if isinstance(instance, Flow):
            self.flow = instance
            self.pddl = instance.compile_to_pddl(debug_flag=True)

        elif isinstance(instance, PDDL):
            # self.flow = None
            self.pddl = instance

        else:
            raise ValueError(f"Debugger must initiated with a Flow or PDDL object, found {type(instance)} instead.")

    @abstractmethod
    def debug_raw_plan(self, raw_plan: RawPlan) -> None:
        pass

    # @abstractmethod
    # def debug(self, plan: ClassicalPlanReference) -> None:
    #     pass


class BasicDebugger(Debugger):
    def debug_raw_plan(self, raw_plan: RawPlan) -> None:
        raise NotImplementedError

    @staticmethod
    def parse_tokens(list_of_tokens: List[str]) -> ClassicalPlanReference:
        def parse_parameters(prefix: str, signature: str) -> List[str]:
            m = re.match(rf"{prefix}\((?P<parameters>.*)\)", signature)

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

        parsed_plan = ClassicalPlanReference()

        for index, token in enumerate(list_of_tokens):
            token = token.replace(f"[{index}]", "", 1)
            token = token.strip()
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
                            parameters=parse_parameters(action_name, token),
                        )

            if new_action is None:
                action_split = token.split(" = ")
                agent_signature = action_split[0] if len(action_split) == 1 else action_split[1]

                agent_signature_split = agent_signature.split("(")
                action_name = agent_signature_split[0]
                parameters = [] if len(agent_signature_split) == 1 else parse_parameters(action_name, agent_signature)

                new_action = Step(
                    name=action_name,
                    parameters=parameters,
                )

            if new_action:
                parsed_plan.plan.append(new_action)
            else:
                raise ValueError(f"Unrecognized token: {token}")

        return parsed_plan

    # def check_soundness(self, reference: ClassicalPlanReference, timeout: int = TIMEOUT) -> Report:
    #     new_report = Report(report_type=SolutionQuality.SOUND)
    #     return new_report
    #
    # def check_validity(self, reference: ClassicalPlanReference, timeout: int = TIMEOUT) -> Report:
    #     new_report = Report(report_type=SolutionQuality.VALID)
    #     return new_report
    #
    # def check_optimality(self, reference: ClassicalPlanReference, timeout: int = TIMEOUT) -> Report:
    #     new_report = Report(report_type=SolutionQuality.OPTIMAL)
    #     return new_report

    # def debug(self, reference: ClassicalPlanReference, timeout: int = TIMEOUT) -> List[Report]:
    #     return [
    #         self.check_soundness(reference, timeout),
    #         self.check_validity(reference, timeout),
    #         self.check_optimality(reference, timeout),
    #     ]
