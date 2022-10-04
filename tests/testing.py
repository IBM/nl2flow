from nl2flow.plan.planners import Michael, Christian
from nl2flow.plan.options import DEFAULT_PLANNER_URL

from nl2flow.compile.flow import Flow
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.schemas import SignatureItem
from nl2flow.plan.schemas import PlannerResponse

import os

planner_url = os.getenv("PLANNER_URL")


class BaseTestAgents:
    flow = Flow(name="NL2Flow Test")
    planner = (
        Michael(url=planner_url)
        if planner_url is not None
        else Christian(url=DEFAULT_PLANNER_URL)
    )

    def setup_method(self) -> None:
        self.flow = Flow(name="NL2Flow Test")
        self.__set_up_default_test_agents()

    def get_plan(self) -> PlannerResponse:
        plans: PlannerResponse = self.flow.plan_it(self.planner)
        print(self.planner.pretty_print(plans))
        return plans

    def __set_up_default_test_agents(self) -> None:

        credit_score_agent = Operator("Credit Score API")
        credit_score_agent.add_input(SignatureItem(parameters=["AccountID", "Email"]))
        credit_score_agent.add_output(SignatureItem(parameters=["Credit Score"]))

        email_agent = Operator("Email Agent")
        email_agent.add_input(
            SignatureItem(parameters=["from", "to", "cc", "bcc", "body", "attachments"])
        )

        find_errors_api = Operator("Find Errors")
        find_errors_api.add_input(SignatureItem(parameters=["database link"]))
        find_errors_api.add_output(SignatureItem(parameters=["list of errors"]))

        fix_errors_api = Operator("Fix Errors")
        fix_errors_api.add_input(SignatureItem(parameters=["list of errors"]))

        self.flow.add(
            [credit_score_agent, email_agent, find_errors_api, fix_errors_api]
        )
