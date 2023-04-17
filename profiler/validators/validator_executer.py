import subprocess
from typing import List, Tuple
from profiler.generators.info_generator.agent_info_data_types import Plan


domain_file_name = "domain.pddl"
problem_file_name = "problem.pddl"
plan_file_name = "plan.pddl"

VAL = "validate"


def get_plan_str(plan: Plan) -> str:
    action_strs: List[str] = list()
    for plan_action in plan["plan"]:
        action_name = plan_action["action_name"]
        parameters_str = ",".join(plan_action["parameters"])
        action_strs.append(f"{action_name}: [{parameters_str}]")

    return "\n".join(action_strs)


def execute_Val(
    pddl_domain: str, pddl_problem: str, pddl_plan: str
) -> Tuple[int, str, str]:
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

    return result.returncode, result.stderr, result.stdout
