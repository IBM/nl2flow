import unittest
from profiler.converters.info_2_flow_converter import get_pddl_plan_str
from profiler.generators.info_generator.agent_info_data_types import Plan


class TestInfo2FlowConverter(unittest.TestCase):
    def test_get_pddl_plan_str(self):
        plan: Plan = {"plan": [{"action_name": "a", "parameters": ["b", "c"]}]}
        res = get_pddl_plan_str(plan)
        self.assertEqual("(a b c)", res)
