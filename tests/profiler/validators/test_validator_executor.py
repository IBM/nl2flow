import unittest
from profiler.validators.validator_executer import (
    execute_Val,
    domain_file_name,
    problem_file_name,
    plan_file_name,
)


class TestValidatorExecutor(unittest.TestCase):
    def test_execute_Val(self):
        pddl_domain = ""
        pddl_problem = ""
        pddl_plan = ""

        with open(f"./tests/profiler/data/pddl/{domain_file_name}", "r") as f:
            pddl_domain = f.read()
        with open(f"./tests/profiler/data/pddl/{problem_file_name}", "r") as f:
            pddl_problem = f.read()
        with open(f"./tests/profiler/data/pddl/{plan_file_name}", "r") as f:
            pddl_plan = f.read()
        return_code, err, out = execute_Val(pddl_domain, pddl_problem, pddl_plan)
        self.assertIsNotNone(out)
        self.assertIsNotNone(err)
        self.assertIsNotNone(return_code)
