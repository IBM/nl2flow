import time


def get_current_time_in_millisecond():
    """
    return milliseconds since epoch
    """
    return time.time() * 1000
