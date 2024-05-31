import os
import subprocess
from typing import Tuple
from nl2flow.compile.schemas import PDDL
from nl2flow.plan.schemas import PlannerResponse
from nl2flow.printers.codelike import CodeLikePrint
from profiler.test_helpers.profiler_test_helper_variables import (
    domain_file_name,
    problem_file_name,
    plan_file_name,
    pddl_start_key,
)
from profiler.common_helpers.string_helper import trim_pddl_str


def write_pddl_plan(pddl: PDDL, plans: PlannerResponse) -> None:
    current_directory = os.getenv("PYTEST_CURRENT_TEST", "")
    current_directory_list = current_directory.split("/")[:-1]
    with open("/".join(current_directory_list + [domain_file_name]), "w") as f:
        f.write(pddl.domain)
    with open("/".join(current_directory_list + [problem_file_name]), "w") as f:
        f.write(pddl.problem)
    with open("/".join(current_directory_list + [plan_file_name]), "w") as f:
        f.write(CodeLikePrint.pretty_print(plans))


def get_str_from_file(path: str) -> str:
    with open(path, "r") as f:
        content = f.read()

    return content


def read_remove_pddl_plan(file_path: str) -> Tuple[str, str, str]:
    test_directory_list = file_path.split("/")[:-1]
    domain_file_path = "/".join(test_directory_list + [domain_file_name])
    problem_file_path = "/".join(test_directory_list + [problem_file_name])
    plan_file_path = "/".join(test_directory_list + [plan_file_name])

    domain_pddl_str = trim_pddl_str(get_str_from_file(domain_file_path), pddl_start_key)
    problem_pddl_str = trim_pddl_str(get_str_from_file(problem_file_path), pddl_start_key)

    application_command = ["rm"]
    files = [domain_file_path, problem_file_path, plan_file_path]
    _ = subprocess.run(application_command + files, capture_output=False)

    return domain_pddl_str, problem_pddl_str, get_str_from_file(plan_file_path)
