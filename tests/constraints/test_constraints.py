from tests.testing import BaseTestAgents
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.options import (
    MemoryState,
    ConstraintState,
    BasicOperations,
)
from nl2flow.plan.schemas import Parameter
from nl2flow.compile.schemas import (
    Constraint,
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
                constraints=[
                    Constraint(
                        constraint_id="Char limit for a tweet",
                        constraint="len(tweet) <= 240",
                        parameters=["tweet"],
                    )
                ],
            )
        )

        bitly_agent = Operator("Bitly")
        bitly_agent.add_input(
            SignatureItem(parameters=[Parameter(item_id="url", item_type="Text")])
        )
        bitly_agent.add_output(
            SignatureItem(parameters=[Parameter(item_id="url", item_type="Text")])
        )

        self.flow.add([twitter_agent, bitly_agent])

    def test_constraints_basic(self) -> None:
        goal = GoalItems(goals=GoalItem(goal_name="Twitter"))
        self.flow.add(goal)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 3, "There should be 3 step plan."

        step_2 = poi.plan[1]
        assert step_2.name.startswith(
            BasicOperations.CONSTRAINT.value
        ), "With a constraint check."

    def test_constraints_with_replan(self) -> None:
        goal = GoalItems(goals=GoalItem(goal_name="Twitter"))
        self.flow.add(goal)
        self.flow.add(
            [
                MemoryItem(
                    item_id="tweet", item_type="Text", item_state=MemoryState.KNOWN
                ),
                Constraint(
                    constraint_id="Char limit for a tweet",
                    constraint="len(tweet) <= 240",
                    parameters=["tweet"],
                    truth_value=ConstraintState.FALSE.value,
                ),
            ]
        )

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 5, "There should be 5 step plan."
        assert poi.plan[1].name == "Bitly", "Use Bitly to redo constraint check."
        assert {poi.plan[0].name, poi.plan[2].name} == {
            BasicOperations.MAPPER.value
        }, "Surrounded by two mappings."
        assert poi.plan[3].name.startswith(
            BasicOperations.CONSTRAINT.value
        ), "Redo constraint check."

    def test_constraints_in_output(self) -> None:
        tweet_generator_agent = Operator("TweetGen")
        tweet_generator_agent.add_output(
            SignatureItem(
                parameters=[Parameter(item_id="tweet", item_type="Text")],
                constraints=[
                    Constraint(
                        constraint_id="Char limit for a tweet",
                        constraint="len(tweet) <= 240",
                        parameters=["tweet"],
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
