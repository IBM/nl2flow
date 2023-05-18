import unittest
from profiler.common_helpers.time_helper import get_current_time_in_millisecond


class TestTimeHelper(unittest.TestCase):
    def test_get_current_time_in_millisecond(self):
        millisecond_since_epoch = get_current_time_in_millisecond()
        self.assertGreater(millisecond_since_epoch, 1684438494922.379)
