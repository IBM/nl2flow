import unittest
from profiler.validators.validator_executer import (
    execute_Val,
    validate_pddl,
    domain_file_name,
    problem_file_name,
    plan_file_name,
)


class TestValidatorExecutor(unittest.TestCase):
    @unittest.skip("file not found")
    def test_execute_Val(self) -> None:
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
        self.assertEqual(0, len(err))
        self.assertIsNotNone(return_code)

    @unittest.skip("file not found")
    def test_validate_pddl(self) -> None:
        pddl_domain = ""
        pddl_problem = ""
        pddl_plan = ""

        with open(f"./tests/profiler/data/pddl/{domain_file_name}", "r") as f:
            pddl_domain = f.read()
        with open(f"./tests/profiler/data/pddl/{problem_file_name}", "r") as f:
            pddl_problem = f.read()
        with open(f"./tests/profiler/data/pddl/{plan_file_name}", "r") as f:
            pddl_plan = f.read()
        validator_output = validate_pddl(pddl_domain, pddl_problem, pddl_plan)
        self.assertTrue(validator_output.is_executable_plan)
        self.assertTrue(validator_output.is_valid_plan)
        self.assertEqual(7, validator_output.total_cost)
