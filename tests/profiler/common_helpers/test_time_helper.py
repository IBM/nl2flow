from profiler.common_helpers.time_helper import get_current_time_in_millisecond


class TestTimeHelper:
    def test_get_current_time_in_millisecond(self) -> None:
        millisecond_since_epoch = get_current_time_in_millisecond()
        assert millisecond_since_epoch > 1684438494922.379
