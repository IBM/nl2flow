from __future__ import annotations
from typing import Any, Union, List, Set
from pydantic import BaseModel
from nl2flow.compile.flow import Flow
from nl2flow.printers.driver import Printer
from nl2flow.printers.verbalize import comma_separate, who_need_it
from nl2flow.plan.schemas import Action, ClassicalPlan as Plan
from nl2flow.plan.utils import find_goal, get_all_goals
from nl2flow.compile.schemas import Step, Constraint
from nl2flow.compile.options import GoalType
from nl2flow.compile.options import BasicOperations


class InputExplained(BaseModel):
    explained: bool = False
    name: str


class ConstraintExplanation(Constraint):
    explained: bool = False
    inputs: List[InputExplained] = []

    @classmethod
    def initialize_from_constraint(cls, constraint: Constraint) -> ConstraintExplanation:
        parameters = constraint.get_variable_references_from_constraint(constraint.constraint, transforms=[])

        return ConstraintExplanation(
            constraint=constraint.constraint,
            truth_value=constraint.truth_value,
            inputs=[InputExplained(name=p) for p in parameters],
        )


class ActionExplanation(Action):
    explained: bool = False
    inputs: List[InputExplained] = []

    @classmethod
    def initialize_from_action(cls, action: Action) -> ActionExplanation:
        return ActionExplanation(
            name=action.name,
            parameters=action.parameters,
            inputs=[InputExplained(name=i) for i in action.inputs],
            outputs=action.outputs,
        )


class ClassicalPlanExplanation(BaseModel):
    plan: List[Union[ActionExplanation, ConstraintExplanation]] = []

    @classmethod
    def initialize_from_plan(cls, plan: Plan) -> ClassicalPlanExplanation:
        new_plan = ClassicalPlanExplanation(
            cost=plan.cost,
            length=plan.length,
            metadata=plan.metadata,
            reference=plan.reference,
            plan=[
                ActionExplanation.initialize_from_action(step)
                if isinstance(step, Action)
                else ConstraintExplanation.initialize_from_constraint(step)
                for step in plan.plan
            ],
        )

        new_plan.plan.reverse()
        return new_plan


class ExplainPrint(Printer):
    @classmethod
    def explain_inputs(
        cls,
        action: Union[ConstraintExplanation, ActionExplanation],
        flow_object: Flow,
        index: int,
        plan: List[Union[ActionExplanation, ConstraintExplanation]],
        explained_known: Set[str],
    ) -> List[str]:
        input_string = comma_separate([ip.name for ip in action.inputs])

        if isinstance(action, ConstraintExplanation):
            lead_string = "To evaluate the constraint"
        else:
            lead_string = f"In order to execute {action.name}"

        lead_string = f"{lead_string}, the values of its parameters {input_string} must be known."
        explanation_strings = [lead_string]

        input_set = {ip.name for ip in action.inputs if not ip.explained}
        already_explained_inputs = input_set.intersection(explained_known)

        if already_explained_inputs:
            already_explained_string = comma_separate(sorted(list(already_explained_inputs)))
            explanation_strings.append(
                f"Values of {already_explained_string} have already been acquired by the rest of the plan."
            )

        for i, ip in enumerate(action.inputs):
            if ip.name not in explained_known:
                explanation_strings.extend(cls.explain_object_known(ip, flow_object, index, plan, explained_known))

                explained_known.add(action.inputs[i].name)
                action.inputs[i].explained = True

        return explanation_strings

    @classmethod
    def explain_constraint(
        cls,
        action: ConstraintExplanation,
        flow_object: Flow,
        index: int,
        plan: List[Union[ActionExplanation, ConstraintExplanation]],
        explained_known: Set[str],
    ) -> List[str]:
        constraint_strings = [f"{action.constraint} is required to be {action.truth_value}."]

        postfix = plan[:index]
        postfix.reverse()

        who_need_it_string = comma_separate(who_need_it(action.constraint, flow_object, postfix))

        if who_need_it_string:
            constraint_strings.append(f"This is required by {who_need_it_string}.")

        constraint_strings.extend(cls.explain_inputs(action, flow_object, index, plan, explained_known))
        action.explained = True
        return constraint_strings

    @classmethod
    def explain_action(
        cls,
        action: ActionExplanation,
        flow_object: Flow,
        index: int,
        plan: List[Union[ActionExplanation, ConstraintExplanation]],
        explained_known: Set[str],
    ) -> List[str]:
        explanation_strings = []

        goals_in_output = []
        for op in action.outputs:
            goal_check = find_goal(op, flow_object)

            if goal_check and goal_check.goal_type.OBJECT_KNOWN:
                goals_in_output.append(op)

        output_string = comma_separate(goals_in_output)

        if output_string:
            explanation_strings.append(f"Action {action.name} produces {output_string} which is a goal of the plan.")

        explanation_strings.extend(cls.explain_inputs(action, flow_object, index, plan, explained_known))
        action.explained = True
        return explanation_strings

    @classmethod
    def explain_object_known(
        cls,
        item: InputExplained,
        flow_object: Flow,
        index: int,
        plan: List[Union[ActionExplanation, ConstraintExplanation]],
        explained_known: Set[str],
    ) -> List[str]:
        if item.explained:
            return []
        else:
            for idx in range(index + 1, len(plan)):
                step = plan[idx]
                if isinstance(step, ActionExplanation):
                    if BasicOperations.is_basic(step.name):
                        if step.name == BasicOperations.SLOT_FILLER.value and item.name == step.inputs[0].name:
                            explained_known.add(step.inputs[0].name)
                            step.inputs[0].explained = True

                            return [f"The value of {item.name} is acquired by asking the user."]

                        elif step.name == BasicOperations.MAPPER.value and item.name == step.inputs[1].name:
                            explanation_strings = [
                                f"The value of {item.name} is acquired by mapping from the value of variable {step.inputs[0].name}."
                            ]
                            explanation_strings.extend(
                                cls.explain_object_known(step.inputs[0], flow_object, idx, plan, explained_known)
                            )

                            explained_known.add(step.inputs[1].name)
                            step.inputs[1].explained = True

                            return explanation_strings

                    elif item.name in step.outputs:
                        explanation_strings = [f"The value of {item.name} is acquired from action {step.name}."]
                        explanation_strings.extend(cls.explain_action(step, flow_object, idx, plan, explained_known))
                        return explanation_strings

            return []

    @classmethod
    def pretty_print_plan(cls, plan: Plan, **kwargs: Any) -> str:
        flow_object: Flow = kwargs["flow_object"]
        bulleted: bool = kwargs.get("bulleted", True)

        all_goals = get_all_goals(flow_object)
        goal_strings = []

        for goal_item in all_goals:
            if goal_item.goal_type == GoalType.OPERATOR:
                goal_strings.append(f"execute action {goal_item.goal_name}")
            elif goal_item.goal_type == GoalType.CONSTRAINT:
                goal_strings.append(f"check {goal_item.goal_name}")
            elif goal_item.goal_type == GoalType.OBJECT_USED:
                goal_strings.append(f"operate on the variable {goal_item.goal_name}")
            elif goal_item.goal_type == GoalType.OBJECT_KNOWN:
                goal_strings.append(f"acquire the value of variable {goal_item.goal_name}")

        goal_string = comma_separate(goal_strings)
        goal_string = f"The goal of the plan is to {goal_string}."

        plan_explanation_object = ClassicalPlanExplanation.initialize_from_plan(plan)
        explained_known: Set[str] = set()
        explanations = []

        for step, action in enumerate(plan_explanation_object.plan):
            if action.explained:
                continue

            if isinstance(action, ActionExplanation):
                if BasicOperations.is_basic(action.name):
                    continue

                action_strings = cls.explain_action(
                    action, flow_object, step, plan_explanation_object.plan, explained_known
                )
                explanations.extend(action_strings)

            else:
                constraint_strings = cls.explain_constraint(
                    action, flow_object, step, plan_explanation_object.plan, explained_known
                )
                explanations.extend(constraint_strings)

        explanations = [goal_string] + explanations
        delimiter = "\n" if bulleted else " "
        return delimiter.join(explanations)

    @classmethod
    def parse_token(cls, token: str, **kwargs: Any) -> Union[Step, Constraint, None]:
        raise NotImplementedError
