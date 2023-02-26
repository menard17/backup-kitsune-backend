import time
import unittest
import structlog
from structlog.typing import EventDict

from structlog.testing import capture_logs
from flask.wrappers import Response

from utils.metric import (
    after_request_log_endpoint_metric,
    before_request_add_start_time,
    teardown_request_log_endpoint_metric,
)

log = structlog.get_logger()


class FakeRequest:
    pass


class FakeRequestWithStartTime:
    def __init__(self, endpoint: str) -> None:
        self.start_time = time.time()
        self.endpoint = endpoint


class TestBeforeRequestAddStartTime(unittest.TestCase):
    def test_should_add_start_time(self):
        request = FakeRequest()
        before_request_add_start_time(request)
        assert request.start_time <= time.time()


class TestTeardownRequestLogEndpointMetric(unittest.TestCase):
    def test_should_log_on_error(self):
        test_endpoint = "test-endpoint"
        err = Exception("dummy error")
        fake_request = FakeRequestWithStartTime(test_endpoint)

        with capture_logs() as cap_logs:
            teardown_request_log_endpoint_metric(fake_request, err)

        assert_exception_metric(test_endpoint, err, cap_logs)
        assert_latency_metric(test_endpoint, cap_logs)

    def test_should_not_log_on_error(self):
        test_endpoint = "test-endpoint"
        fake_request = FakeRequestWithStartTime(test_endpoint)

        self._assert_no_log(teardown_request_log_endpoint_metric, fake_request, None)

    def _assert_no_log(self, *args, **kwargs):
        with capture_logs() as cap_logs:
            log.info("dummy log to ensure it is running")
        assert len(cap_logs) == 1
        log_line = cap_logs[0]
        assert log_line["log_level"] == "info"
        assert log_line["event"] == "dummy log to ensure it is running"


class TestAfterRequestLogEndpointMetric(unittest.TestCase):
    def test_should_log_latency(self):
        test_endpoint = "test-endpoint"

        fake_request = FakeRequestWithStartTime(test_endpoint)
        response = Response(status=200)

        with capture_logs() as cap_logs:
            after_request_log_endpoint_metric(fake_request, response)

        assert_latency_metric(test_endpoint, cap_logs)

    def test_should_log_error_on_internal_error(self):
        test_endpoint = "test-endpoint"

        fake_request = FakeRequestWithStartTime(test_endpoint)
        response = Response(status=500)

        with capture_logs() as cap_logs:
            after_request_log_endpoint_metric(fake_request, response)

        assert_error_metric(test_endpoint, "500", cap_logs)
        assert_latency_metric(test_endpoint, cap_logs)


def assert_exception_metric(
    endpoint: str, error: Exception, capture_logs: list[EventDict]
):
    for log in capture_logs:
        if (
            log["log_level"] == "error"
            and log["endpoint"] == endpoint
            and log["error"] == type(error).__name__
            and log["event"] == f"endpoint.{endpoint}.error"
        ):
            return True
    return False


def assert_error_metric(endpoint: str, status_code: str, capture_logs: list[EventDict]):
    for log in capture_logs:
        if (
            log["log_level"] == "error"
            and log["endpoint"] == endpoint
            and log["status_code"] == status_code
            and log["event"] == f"endpoint.{endpoint}.error"
        ):
            return True

    return False


def assert_latency_metric(endpoint: str, capture_logs: list[EventDict]):
    for log in capture_logs:
        if (
            log["log_level"] == "info"
            and log["endpoint"] == endpoint
            and "latency" in log
            and log["event"] == f"endpoint.{endpoint}.latency"
        ):
            return True

    return False
