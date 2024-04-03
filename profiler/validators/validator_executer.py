import subprocess
from typing import List, Tuple
from profiler.data_types.agent_info_data_types import Plan
from profiler.data_types.validator_data_types import PddlPlanValidatorOutput
import re

domain_file_name = "domain.pddl"
problem_file_name = "problem.pddl"
plan_file_name = "plan.pddl"
VAL = "validate"


def get_plan_str(plan: Plan) -> str:
    action_strs: List[str] = list()
    for plan_action in plan.plan:
        action_name = plan_action.action_name
        parameters_str = ",".join(plan_action.parameters)
        action_strs.append(f"{action_name}: [{parameters_str}]")

    return "\n".join(action_strs)


def execute_Val(pddl_domain: str, pddl_problem: str, pddl_plan: str) -> Tuple[int, str, str]:
    """
    returns if a given plan is valid
    VAL is used for the validation
    """
    with open(domain_file_name, "w") as f:
        f.write(pddl_domain)
    with open(problem_file_name, "w") as f:
        f.write(pddl_problem)
    with open(plan_file_name, "w") as f:
        f.write(pddl_plan)

    # write a pddl file here
    result = subprocess.run(
        [VAL, domain_file_name, problem_file_name, plan_file_name],
        capture_output=True,
        text=True,
    )

    application_command = ["rm"]
    files = [domain_file_name, problem_file_name, plan_file_name]
    _ = subprocess.run(application_command + files, capture_output=False)

    return result.returncode, result.stderr, result.stdout


def validate_pddl(pddl_domain: str, pddl_problem: str, pddl_plan: str) -> PddlPlanValidatorOutput:
    """
    returns if PDDL domain, problem, and plans are executable and valid
    """
    return_code, err, out = execute_Val(pddl_domain, pddl_problem, pddl_plan)
    is_executable = False
    is_vaild = False
    total_cost = -1
    if return_code == 0:
        if "Plan executed successfully" in out:
            is_executable = True
            if "Plan valid" in out:
                is_vaild = True
                obj = re.search(r"Value: (.*?)(\r\n?|\n)+", out)
                if obj is not None:
                    total_cost = int(obj.group(1), 10)

    return PddlPlanValidatorOutput(is_executable_plan=is_executable, is_valid_plan=is_vaild, total_cost=total_cost)
