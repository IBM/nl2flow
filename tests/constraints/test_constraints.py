from tests.testing import BaseTestAgents
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.options import (
    MemoryState,
    ConstraintState,
    BasicOperations,
    GoalType,
)
from nl2flow.plan.schemas import Parameter
from nl2flow.compile.schemas import (
    Constraint,
    ManifestConstraint,
    MemoryItem,
    SignatureItem,
    GoalItems,
    GoalItem,
)


class TestConstraints(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

        twitter_agent = Operator("Twitter")
        twitter_agent.add_input(
            SignatureItem(
                parameters=[Parameter(item_id="tweet", item_type="Text")],
                constraints=[Constraint(constraint="len($tweet) <= 240")],
            )
        )

        bitly_agent = Operator("Bitly")
        bitly_agent.add_input(SignatureItem(parameters=[Parameter(item_id="url", item_type="Text")]))
        bitly_agent.add_output(SignatureItem(parameters=[Parameter(item_id="url", item_type="Text")]))

        self.flow.add([twitter_agent, bitly_agent])

    def test_constraints_basic(self) -> None:
        goal = GoalItems(goals=GoalItem(goal_name="Twitter"))
        self.flow.add(goal)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 3, "There should be 3 step plan."

        step_2 = poi.plan[1]
        assert step_2.name.startswith(BasicOperations.CONSTRAINT.value), "With a constraint check."

    def test_constraints_with_replan(self) -> None:
        goal = GoalItems(goals=GoalItem(goal_name="Twitter"))
        self.flow.add(goal)
        self.flow.add(
            [
                MemoryItem(item_id="tweet", item_type="Text", item_state=MemoryState.KNOWN),
                Constraint(
                    constraint="len($tweet) <= 240",
                    truth_value=ConstraintState.FALSE.value,
                ),
            ]
        )

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 5, "There should be 5 step plan."
        assert poi.plan[1].name == "Bitly", "Use Bitly to redo constraint check."
        assert {poi.plan[0].name, poi.plan[2].name} == {BasicOperations.MAPPER.value}, "Surrounded by two mappings."
        assert poi.plan[3].name.startswith(BasicOperations.CONSTRAINT.value), "Redo constraint check."

    def test_constraints_in_output(self) -> None:
        tweet_generator_agent = Operator("TweetGen")
        tweet_generator_agent.add_output(
            SignatureItem(
                parameters=[Parameter(item_id="tweet", item_type="Text")],
                constraints=[
                    Constraint(
                        constraint="len($tweet) <= 240",
                    )
                ],
            )
        )

        goal = GoalItems(goals=GoalItem(goal_name="Twitter"))
        self.flow.add([goal, tweet_generator_agent])

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 2, "There should be 2 step plan."
        assert poi.plan[0].name == "TweetGen", "No extra constraint check."

    def test_constraints_in_goal(self) -> None:
        goal = GoalItems(
            goals=GoalItem(
                goal_name=Constraint(
                    constraint="len($tweet) <= 240",
                ),
                goal_type=GoalType.CONSTRAINT,
            )
        )
        self.flow.add(goal)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        for plan in plans.list_of_plans:
            assert len(plan.plan) == 2
            assert plan.plan[0].name == BasicOperations.SLOT_FILLER.value and plan.plan[0].inputs[0].item_id == "tweet"
            assert plan.plan[1].name.startswith(BasicOperations.CONSTRAINT.value)

        self.flow.add(
            [
                MemoryItem(item_id="tweet", item_type="Text", item_state=MemoryState.KNOWN),
                Constraint(
                    constraint="len($tweet) <= 240",
                    truth_value=ConstraintState.FALSE.value,
                ),
            ]
        )

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        for plan in plans.list_of_plans:
            assert len(plan.plan) == 4
            assert "Bitly" in [step.name for step in plan.plan], "There must be a Bitly now."
            assert plan.plan[-1].name.startswith(
                BasicOperations.CONSTRAINT.value
            ), "Check it again against your list and see consistency."

    def test_manifest_constraint(self) -> None:
        self.flow.add(
            ManifestConstraint(
                manifest=Constraint(
                    constraint="len($tweet) <= 240",
                    truth_value=ConstraintState.TRUE.value,
                ),
                constraint=Constraint(
                    constraint="is_tweet_proper($tweet)",
                    truth_value=ConstraintState.TRUE.value,
                ),
            )
        )

        self.flow.add(
            [
                MemoryItem(item_id="tweet", item_type="Text", item_state=MemoryState.KNOWN),
                GoalItems(goals=GoalItem(goal_name="Twitter")),
                Constraint(
                    constraint="is_tweet_proper($tweet)",
                    truth_value=ConstraintState.TRUE.value,
                ),
            ]
        )

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        for plan in plans.list_of_plans:
            assert len(plan.plan) == 1 and plan.plan[0].name == "Twitter", "Just one direct Tweet operation."
