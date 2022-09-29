from nl2flow.compile.schemas import FlowDefinition, PDDL, Transform, GoalItem, Constraint
from nl2flow.compile.options import TypeOptions, GoalType
from abc import ABC, abstractmethod
from typing import List, Set, Dict, Any

import re

import tarski
import tarski.fstrips as fs
from tarski.theories import Theory
from tarski.io import fstrips as iofs
from tarski.io import FstripsWriter
from tarski.syntax import land, neg


class Compilation(ABC):
    def __init__(self, flow_definition: FlowDefinition):
        self.flow_definition = flow_definition
        self.cached_transforms = list()

    def transform(self, item: str) -> str:
        transformed_item = re.sub(r"\s+", '_', item.lower())
        self.cached_transforms.append(Transform(source=item, target=transformed_item))
        return transformed_item

    def revert_transform(self, item: str) -> str:
        og_items = list(filter(lambda x: item == x.target, self.cached_transforms))
        assert len(og_items) == 1, "There cannot be more than one mapping, something terrible has happened."
        return og_items[0].source

    @abstractmethod
    def compile(self, **kwargs: Dict[str, Any]) -> PDDL:
        pass


class ClassicPDDL(Compilation):

    def compile(self, **kwargs: Dict[str, Any]) -> PDDL:

        def __compile_goals(goal_items) -> Set:
            goal_predicates = set()

            for goal_item in goal_items:
                goals = goal_item.goals

                if not isinstance(goals, List):
                    goals = [goals]

                    for goal in goals:

                        if isinstance(goal, GoalItem):

                            if goal.goal_type == GoalType.OPERATOR.value:
                                goal_predicates.add(has_done(constant_map[self.transform(goal.goal_name)]))

                        elif isinstance(goal, Constraint):
                            pass

                        else:
                            raise TypeError("Unrecognized goal type.")

            return goal_predicates

        name = self.transform(self.flow_definition.name)
        lang = fs.language(name, theories=[Theory.ARITHMETIC])
        cost = lang.function("total-cost", lang.Real)

        problem = fs.create_fstrips_problem(domain_name=f"{name}-domain", problem_name=f"{name}-problem", language=lang)
        problem.metric(cost(), fs.OptimizationType.MINIMIZE)

        # noinspection PyUnresolvedReferences
        init = tarski.model.create(lang)

        type_map = dict()
        constant_map = dict()

        type_map[TypeOptions.ROOT.value] = lang.sort(TypeOptions.ROOT.value)
        type_map[TypeOptions.AGENT.value] = lang.sort(TypeOptions.AGENT.value)

        has_done = lang.predicate("has_done", type_map[TypeOptions.AGENT.value])

        for type_item in self.flow_definition.type_hierarchy:
            type_map[self.transform(type_item.name)] = lang.sort(self.transform(type_item.name), self.transform(type_item.parent))

        for memory_item in self.flow_definition.memory_items:
            constant_map[self.transform(memory_item.item_id)] = lang.constant(self.transform(memory_item.item_id), self.transform(memory_item.item_type) if memory_item.item_type else TypeOptions.ROOT.value)

        for operator in self.flow_definition.operators:
            constant_map[self.transform(operator.name)] = lang.constant(self.transform(operator.name), TypeOptions.AGENT.value)

            problem.action(
                operator.name,
                parameters=list(),
                precondition=land(*[]),
                effects=[],
                cost=iofs.AdditiveActionCost(
                    problem.language.constant(operator.cost, problem.language.get_sort("Integer"))),
            )

        init.set(cost(), 0)
        problem.init = init

        goal_set = __compile_goals(self.flow_definition.goal_items)
        problem.goal = land(*goal_set, flat=True)

        writer = FstripsWriter(problem)
        domain = writer.print_domain().replace(" :numeric-fluents", "")
        problem = writer.print_instance()

        return PDDL(domain=domain, problem=problem)
