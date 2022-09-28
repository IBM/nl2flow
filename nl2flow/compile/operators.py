from typing import List, Optional, Union
from abc import ABC, abstractmethod

from nl2flow.compile.options import CostOptions
from nl2flow.compile.schemas import OperatorDefinition, SignatureItem, Outcome


class Operator(ABC):
    def __init__(self, name: str):
        self.operator_definition = OperatorDefinition(name=name)

    @property
    def name(self) -> str:
        return str(self.operator_definition.name)

    @property
    def definition(self) -> OperatorDefinition:
        return self.operator_definition

    @property
    def cost(self) -> float:
        return float(self.operator_definition.cost)

    @cost.setter
    def cost(self, cost: Union[int, CostOptions]) -> None:
        if isinstance(cost, int):
            self.operator_definition.cost = cost

        elif isinstance(cost, CostOptions):
            self.operator_definition.cost = cost.value

        else:
            raise TypeError(
                "Operator costs must be integers or off-the-shelf CostOptions"
            )

    def add_input(self, new_input: Union[SignatureItem, List[SignatureItem]]) -> None:

        if type(new_input) != List:
            new_input = [new_input]

        for item in new_input:
            assert isinstance(
                new_input, SignatureItem
            ), "Tried to add a non-signature item to an operator."
            self.operator_definition.inputs.append(item)

    @abstractmethod
    def add_outcome(self, outcome: Union[Outcome, List[Outcome]]) -> None:
        pass

    @abstractmethod
    def add_output(self, output: Union[SignatureItem, List[SignatureItem]]) -> None:
        pass


class ClassicalOperator(Operator):
    """
    A classical operator takes in as inputs a list of conditions that must be
    true for the operator to execute and a list of outputs that become true
    after the operator executes. The list of inputs and outputs are independent.
    """

    def add_outcome(self, outcome: Outcome) -> None:
        assert isinstance(
            outcome, Outcome
        ), "Tried to add something else to the outcome list."
        assert (
            outcome.probability is None
        ), "Cannot assign probability to a classical outcome."
        assert not len(
            outcome.conditions
        ), "Cannot assign conditions to a classical outcome."

        self.operator_definition.outputs = outcome

    def add_output(self, new_output: Union[SignatureItem, List[SignatureItem]]) -> None:

        if type(new_output) != List:
            new_output = [new_output]

        for item in new_output:
            assert isinstance(
                item, SignatureItem
            ), "Tried to add a non-signature item to an operator."

            if not self.operator_definition.outputs:
                self.operator_definition.outputs = Outcome

            self.operator_definition.outputs.outcomes.append(item)


class ContingentOperator(Operator):
    """
    A contingent operator takes in as inputs a list of conditions with each condition
    associated with a list of outputs that become true if the input condition holds. If
    multiple input conditions hold, then multiple output conditions are enforced. It can
    also admit global conditions that must hold true for all output conditions.
    """

    def add_outcome(self, outcome: Union[Outcome, List[Outcome]]) -> None:

        if type(outcome) != List:
            outcome = [outcome]

        for item in outcome:
            assert isinstance(
                item, Outcome
            ), "Tried to add something else to an outcome list."
            assert (
                item.probability is None
            ), "Cannot assign probability to a contingent outcome."

            self.operator_definition.outputs.append(item)

    def add_output(self, output: Union[SignatureItem, List[SignatureItem]]) -> None:

        if type(output) != List:
            output = [output]

        new_outcome = Outcome(outcomes=output)
        self.operator_definition.outputs.append(new_outcome)


class NonDeterministicOperator(Operator):
    """
    A non-deterministic operator, like a contingent operator, admits a list of output
    conditions but any one of those output conditions will actually hold once the operator
    has been executed. Like a classical operator though, the list of input conditions must
    be true globally for any of them to occur. You can assign a probability to an outcome.
    """

    def add_outcome(self, outcome: Union[Outcome, List[Outcome]]) -> None:

        if type(outcome) != List:
            outcome = [outcome]

        for item in outcome:
            assert isinstance(
                item, Outcome
            ), "Tried to add something else to an outcome list."
            self.operator_definition.outputs.append(item)

        assert self.__validate_probabilities__(), "JAARL. Probabilities"

    def add_output(
        self,
        output: Union[SignatureItem, List[SignatureItem]],
        probability: Optional[float] = None,
    ) -> None:

        if type(output) != List:
            output = [output]

        new_outcome = Outcome(outcomes=output, probability=probability)
        self.operator_definition.outputs.append(new_outcome)

        assert self.__validate_probabilities__(), "JAARL. Probabilities"

    def __validate_probabilities__(self) -> bool:

        probabilities = [op.probability for op in self.operator_definition.outputs]
        assert all([isinstance(p, float) for p in probabilities]) or all(
            [p is None for p in probabilities]
        ), "Some probabilities are defined, some are not."

        probabilities = [p if p else 0.0 for p in probabilities]
        assert all(
            [0.0 <= p <= 1.0 for p in probabilities]
        ), "Outcome probabilities must be between 0 and 1."

        return True
