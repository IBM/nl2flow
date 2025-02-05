from nl2flow.plan.planners.kstar import Kstar
from nl2flow.compile.schemas import GoalItems, GoalItem, MappingItem, MemoryItem, Constraint
from nl2flow.compile.options import GoalType, MemoryState
from nl2flow.printers.verbalize import VerbalizePrint, comma_separate
from tests.planner.formatting.test_codelike_print import generate_problem_for_testing_printers

PLANNER = Kstar()


class TestVerbalizePrint:
    def setup_method(self) -> None:
        self.flow = generate_problem_for_testing_printers()

    def test_prettified_plan_verbalize(self) -> None:
        self.flow.add(GoalItems(goals=[GoalItem(goal_name="Agent B"), GoalItem(goal_name="Agent A")]))
        planner_response = self.flow.plan_it(PLANNER)
        pretty = VerbalizePrint.pretty_print_plan(planner_response.best_plan, flow_object=self.flow)
        print(pretty)

        pretty_split = pretty.split("\n")

        assert pretty_split[1] in [
            "1. Execute action Agent 1 with b as input. This will result in acquiring a.",
            "1. Execute action Agent 0 with b as input. This will result in acquiring a.",
        ]

        assert pretty_split[:1] + pretty_split[2:] == [
            "0. Acquire the value of b by asking the user.",
            "2. Check that check_if_agent_0_is_done($a, $b) is True.",
            "3. Execute action Agent A with a and b as inputs. This will result in acquiring c. Since executing Agent A was a goal of this plan, return the results of Agent A(a, b) to the user.",
            "4. Get the value of x from c which is already known.",
            "5. Execute action Agent B with a, b, and x as inputs. Since executing Agent B was a goal of this plan, return the results of Agent B(a, b, x) to the user.",
        ]

    def test_verbalize_single_goal(self) -> None:
        self.flow.add(GoalItems(goals=[GoalItem(goal_name="Agent B")]))
        planner_response = self.flow.plan_it(PLANNER)
        pretty = VerbalizePrint.pretty_print_plan(planner_response.best_plan, flow_object=self.flow)
        print(pretty)

        pretty_split = pretty.split("\n")

        assert pretty_split[1] in [
            "1. Execute action Agent 0 with b as input. This will result in acquiring a.",
            "1. Execute action Agent 1 with b as input. This will result in acquiring a.",
        ]

        assert pretty_split[:1] + pretty_split[2:] == [
            "0. Acquire the value of b by asking the user.",
            "2. Check that check_if_agent_0_is_done($a, $b) is True.",
            "3. Execute action Agent A with a and b as inputs. This will result in acquiring c.",
            "4. Get the value of x from c which is already known.",
            "5. Execute action Agent B with a, b, and x as inputs. Since executing Agent B was the goal of this plan, return the results of Agent B(a, b, x) to the user.",
        ]

    def test_verbalize_object_acquired_as_goal(self) -> None:
        self.flow.add(
            GoalItems(goals=[GoalItem(goal_name="Agent B"), GoalItem(goal_name="c", goal_type=GoalType.OBJECT_KNOWN)])
        )

        planner_response = self.flow.plan_it(PLANNER)
        pretty = VerbalizePrint.pretty_print_plan(planner_response.best_plan, flow_object=self.flow)
        print(pretty)

        pretty_split = pretty.split("\n")

        assert pretty_split[3:] == [
            "3. Execute action Agent A with a and b as inputs. This will result in acquiring c. Since acquiring c was a goal of this plan, return c to the user.",
            "4. Get the value of x from c which is already known.",
            "5. Execute action Agent B with a, b, and x as inputs. Since executing Agent B was a goal of this plan, return the results of Agent B(a, b, x) to the user.",
        ]

    def test_verbalize_object_used_as_goal(self) -> None:
        self.flow.add(
            [
                MemoryItem(item_id="id123", item_state=MemoryState.KNOWN),
                MemoryItem(item_id="id345", item_state=MemoryState.KNOWN),
                MappingItem(source_name="id123", target_name="a"),
                MappingItem(source_name="id345", target_name="b"),
                GoalItems(
                    goals=[
                        GoalItem(goal_name="id123", goal_type=GoalType.OBJECT_USED),
                        GoalItem(goal_name="id345", goal_type=GoalType.OBJECT_USED),
                    ]
                ),
            ]
        )

        planner_response = self.flow.plan_it(PLANNER)
        pretty = VerbalizePrint.pretty_print_plan(planner_response.best_plan, flow_object=self.flow)
        print(pretty)

        pretty_split = pretty.split("\n")

        assert pretty_split == [
            "0. Get the value of b from id345 which is already known.",
            "1. Get the value of a from id123 which is already known.",
            "2. Check that check_if_agent_0_is_done($a, $b) is True.",
            "3. Execute action Agent A with a and b as inputs. This will result in acquiring c. The goal of using id123 and id345 is now complete.",
        ]

    def test_verbalize_constraint_as_goal(self) -> None:
        self.flow.add(
            GoalItems(
                goals=[
                    GoalItem(
                        goal_name=Constraint(constraint="check_if_agent_0_is_done($a, $b)"),
                        goal_type=GoalType.CONSTRAINT,
                    )
                ]
            )
        )

        planner_response = self.flow.plan_it(PLANNER)
        pretty = VerbalizePrint.pretty_print_plan(planner_response.best_plan, flow_object=self.flow)
        print(pretty)

        pretty_split = pretty.split("\n")
        assert pretty_split == [
            "0. Acquire the value of b by asking the user.",
            "1. Execute action Agent 1 with b as input. This will result in acquiring a.",
            "2. Check that check_if_agent_0_is_done($a, $b) is True. This was the goal of the plan.",
        ]

    def test_prettified_plan_verbalize_with_lookahead(self) -> None:
        self.flow.add(GoalItems(goals=[GoalItem(goal_name="Agent B"), GoalItem(goal_name="Agent A")]))
        planner_response = self.flow.plan_it(PLANNER)
        pretty = VerbalizePrint.pretty_print_plan(planner_response.best_plan, flow_object=self.flow, lookahead=True)

        print(pretty)
        pretty_split = pretty.split("\n")

        assert pretty_split[:2] == [
            "0. Acquire the value of b by asking the user. b is required later by action Agent 0, action Agent A, action Agent B, and constraint check_if_agent_0_is_done($a, $b).",
            "1. Execute action Agent 0 with b as input. This will result in acquiring a. a is required later by action Agent A, action Agent B, and constraint check_if_agent_0_is_done($a, $b).",
        ] or pretty_split[:2] == [
            "0. Acquire the value of b by asking the user. b is required later by action Agent 1, action Agent A, action Agent B, and constraint check_if_agent_0_is_done($a, $b).",
            "1. Execute action Agent 1 with b as input. This will result in acquiring a. a is required later by action Agent A, action Agent B, and constraint check_if_agent_0_is_done($a, $b).",
        ]

        assert pretty_split[2:] == [
            "2. Check that check_if_agent_0_is_done($a, $b) is True. This is needed to execute Agent A.",
            "3. Execute action Agent A with a and b as inputs. This will result in acquiring c. c is required later by action map to produce x (x is required later by action Agent B). Since executing Agent A was a goal of this plan, return the results of Agent A(a, b) to the user.",
            "4. Get the value of x from c which is already known. x is required later by action Agent B.",
            "5. Execute action Agent B with a, b, and x as inputs. Since executing Agent B was a goal of this plan, return the results of Agent B(a, b, x) to the user.",
        ]

    def test_comma_separation(self) -> None:
        assert comma_separate([]) == ""
        assert comma_separate(["a"]) == "a"
        assert comma_separate(["a", "b"]) == "a and b"
        assert comma_separate(["a", "b", "c"]) == "a, b, and c"
        assert comma_separate(["a", "b", "c", "d"]) == "a, b, c, and d"
