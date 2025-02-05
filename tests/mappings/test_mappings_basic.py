from tests.testing import BaseTestAgents
from nl2flow.plan.schemas import Action, PlannerResponse
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.options import BasicOperations, MappingOptions
from nl2flow.printers.codelike import CodeLikePrint
from nl2flow.compile.schemas import (
    SlotProperty,
    GoalItem,
    GoalItems,
    MappingItem,
    SignatureItem,
    MemoryItem,
)


def check_basic_mapping_plan(plans: PlannerResponse) -> None:
    poi = plans.best_plan

    assert poi, "There should be plans."
    assert len(poi.plan) == 4, "The plan should have 4 steps."

    step_1: Action = poi.plan[0]
    assert step_1.name == "User Info", "Call user info agent to map later."

    step_2: Action = poi.plan[1]
    step_3: Action = poi.plan[2]
    assert all(o == BasicOperations.MAPPER.value for o in [step_2.name, step_3.name]), "Followed by two mappings."

    step_4: Action = poi.plan[3]
    assert step_4.name == "Credit Score API", "Final action should be the goal action."


class TestMappingsBasic(BaseTestAgents):
    def setup_method(self) -> None:
        BaseTestAgents.setup_method(self)

        imposter_agent = Operator("Fake Find Errors")
        imposter_agent.add_output(SignatureItem(parameters=["errors"]))
        self.flow.add(imposter_agent)

        imposter_agent_preferred = Operator("Fake Find Errors Preferred")
        imposter_agent_preferred.add_output(SignatureItem(parameters=["preferred errors"]))
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
        check_basic_mapping_plan(plans)

    def test_mapper_basic_collapsed_print(self) -> None:
        self.flow.add(
            [
                MappingItem(source_name="Username", target_name="Email"),
                MappingItem(source_name="Account Info", target_name="AccountID"),
            ]
        )

        goal = GoalItems(goals=GoalItem(goal_name="Credit Score API"))
        self.flow.add(goal)

        plans = self.get_plan()
        pretty_print = CodeLikePrint.pretty_print_plan(plans.best_plan, collapse_maps=True)
        print(pretty_print)

        assert pretty_print.split("\n") == [
            "[0] Username, Account Info = User Info()",
            "[1] Credit Score = Credit Score API(Account Info, Username)",
        ]

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

        poi = plans.best_plan
        assert len(poi.plan) == 3, "The plan should have 3 steps."

        step_1: Action = poi.plan[0]
        step_2: Action = poi.plan[1]
        assert all(
            o == BasicOperations.SLOT_FILLER.value for o in [step_1.name, step_2.name]
        ), "Followed by two slot fills."

        self.flow.mapping_options.add(MappingOptions.transitive)

        plans = self.get_plan()
        check_basic_mapping_plan(plans)

    def test_mapper_with_slot_last_resort(self) -> None:
        self.flow.add(MappingItem(source_name="errors", target_name="list of errors"))

        goal = GoalItems(goals=GoalItem(goal_name="Fix Errors"))
        self.flow.add(goal)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.best_plan
        assert len(poi.plan) == 3, "The plan should have 3 steps."

        step_1: Action = poi.plan[0]
        assert step_1.name == "Fake Find Errors", "Call fake error finder."

        step_2: Action = poi.plan[1]
        assert step_2.name == BasicOperations.MAPPER.value, "Mapping preferred over filling slot directly."

        step_3: Action = poi.plan[2]
        assert step_3.name == "Fix Errors", "Final goal operator."

    def test_mapper_with_map_preference(self) -> None:
        self.flow.add(MappingItem(source_name="errors", target_name="list of errors", probability=0.5))
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

        poi = plans.best_plan
        assert len(poi.plan) == 3, "The plan should have 3 steps."

        step_2: Action = poi.plan[1]
        assert (
            step_2.name == BasicOperations.MAPPER.value
            and step_2.inputs[0] == "preferred errors"
            and step_2.inputs[1] == "list of errors"
        ), "The high probability mapping is preferred."

    def test_mapper_with_slot_preference(self) -> None:
        self.flow.add(
            [
                MemoryItem(item_id="Name"),
                SlotProperty(slot_name="Name", slot_desirability=1.0),
                MappingItem(source_name="Name", target_name="AccountID"),
            ]
        )

        goal = GoalItems(goals=GoalItem(goal_name="Credit Score API"))
        self.flow.add(goal)

        plans = self.get_plan()
        assert plans.list_of_plans, "There should be plans."

        poi = plans.best_plan
        assert len(poi.plan) == 4, "There should be 4 steps in the plan."

        slot_fill_actions = list(
            filter(
                lambda action: action.name == BasicOperations.SLOT_FILLER.value,
                poi.plan[:2],
            )
        )

        assert len(slot_fill_actions) == 2, "Two slot fill actions."
        assert "Name" in [action.inputs[0] for action in slot_fill_actions], "One slot fill for Name."
        assert "Email" in [action.inputs[0] for action in slot_fill_actions], "One slot fill for Email."

        assert BasicOperations.MAPPER.value in [
            action.name for action in poi.plan[1:3]
        ], "One mapping among 2nd and 3rd step."

        step_4: Action = poi.plan[-1]
        assert step_4.name == "Credit Score API", "Fix Errors using the mapping and alternative slot."
