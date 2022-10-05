from nl2flow.compile.schemas import GoalItem, GoalItems, MappingItem, SignatureItem
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.options import BasicOperations, MappingOptions
from nl2flow.plan.schemas import Action, PlannerResponse
from tests.testing import BaseTestAgents


class TestMappingsBasic(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

        imposter_agent = Operator("Fake Find Errors")
        imposter_agent.add_output(SignatureItem(parameters=["errors"]))
        self.flow.add(imposter_agent)

        imposter_agent_preferred = Operator("Fake Find Errors Preferred")
        imposter_agent_preferred.add_output(
            SignatureItem(parameters=["preferred errors"])
        )
        self.flow.add(imposter_agent_preferred)

    def test_mapper_basic(self) -> None:
        self.flow.add(
            [
                MappingItem(source_name="Username", target_name="Email"),
                MappingItem(source_name="Account Info", target_name="AccountID"),
            ]
        )

        goal = GoalItems(goals=GoalItem(goal_name="Credit Score API"))
        self.flow.add(goal)

        plans = self.get_plan()
        self.__test_basic_mapping_plan(plans)

    @staticmethod
    def __test_basic_mapping_plan(plans: PlannerResponse) -> None:
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 4, "The plan should have 4 steps."

        step_1: Action = poi.plan[0]
        assert step_1.name == "User Info", "Call user info agent to map later."

        step_2: Action = poi.plan[1]
        step_3: Action = poi.plan[2]
        assert all(
            o == BasicOperations.MAPPER.value for o in [step_2.name, step_3.name]
        ), "Followed by two mappings."

        step_4: Action = poi.plan[3]
        assert (
            step_4.name == "Credit Score API"
        ), "Final action should be the goal action."

    def test_mapper_is_transitive(self) -> None:
        self.flow.add(
            [
                MappingItem(source_name="Email", target_name="Username"),
                MappingItem(source_name="AccountID", target_name="Account Info"),
            ]
        )

        goal = GoalItems(goals=GoalItem(goal_name="Credit Score API"))
        self.flow.add(goal)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 3, "The plan should have 3 steps."

        step_1: Action = poi.plan[0]
        step_2: Action = poi.plan[1]
        assert all(
            o == BasicOperations.SLOT_FILLER.value for o in [step_1.name, step_2.name]
        ), "Followed by two slot fills."

        self.flow.mapping_options.add(MappingOptions.transitive)

        plans = self.get_plan()
        self.__test_basic_mapping_plan(plans)

    def test_mapper_with_slot_preference(self) -> None:
        self.flow.add(MappingItem(source_name="errors", target_name="list of errors"))

        goal = GoalItems(goals=GoalItem(goal_name="Fix Errors"))
        self.flow.add(goal)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 3, "The plan should have 3 steps."

        step_1: Action = poi.plan[0]
        assert step_1.name == "Fake Find Errors", "Call fake error finder."

        step_2: Action = poi.plan[1]
        assert (
            step_2.name == BasicOperations.MAPPER.value
        ), "Mapping preferred over filling slot directly."

        step_3: Action = poi.plan[2]
        assert step_3.name == "Fix Errors", "Final goal operator."

    def test_mapper_with_map_preference(self) -> None:
        self.flow.add(
            MappingItem(
                source_name="errors", target_name="list of errors", probability=0.5
            )
        )
        self.flow.add(
            MappingItem(
                source_name="preferred errors",
                target_name="list of errors",
                probability=0.7,
            )
        )

        goal = GoalItems(goals=GoalItem(goal_name="Fix Errors"))
        self.flow.add(goal)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.list_of_plans[0]
        assert len(poi.plan) == 3, "The plan should have 3 steps."

        step_2: Action = poi.plan[1]
        assert (
            step_2.name == BasicOperations.MAPPER.value
            and step_2.inputs[0].name == "preferred errors"
            and step_2.inputs[1].name == "list of errors"
        ), "The high probability mapping is preferred."
