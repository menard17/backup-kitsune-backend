import logging
import time
import unittest

from flask.wrappers import Response

from utils.metric import (
    after_request_log_endpoint_metric,
    before_request_add_start_time,
    teardown_request_log_endpoint_metric,
)

logger = logging.getLogger(__name__)


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

        with self.assertLogs() as cm:
            teardown_request_log_endpoint_metric(logger, fake_request, err)

        err_log = "ERROR:test_metric:endpoint.test-endpoint.error: dummy error"
        assert err_log in cm.output
        assert_latency_metric(test_endpoint, cm.output)

    def test_should_not_log_on_error(self):
        test_endpoint = "test-endpoint"
        fake_request = FakeRequestWithStartTime(test_endpoint)

        self._assert_no_log(
            teardown_request_log_endpoint_metric, logger, fake_request, None
        )

    def _assert_no_log(self, fn, *args, **kwargs):
        with self.assertLogs(level="INFO") as cm:
            logger.info("dummy log to ensure it is running")
            fn(*args, **kwargs)
        assert cm.output == ["INFO:test_metric:dummy log to ensure it is running"]


class TestAfterRequestLogEndpointMetric(unittest.TestCase):
    def test_should_log_latency(self):
        test_endpoint = "test-endpoint"

        fake_request = FakeRequestWithStartTime(test_endpoint)
        response = Response(status=200)

        with self.assertLogs(level="INFO") as cm:
            after_request_log_endpoint_metric(logger, fake_request, response)

        assert_latency_metric(test_endpoint, cm.output)

    def test_should_log_error_on_internal_error(self):
        test_endpoint = "test-endpoint"

        fake_request = FakeRequestWithStartTime(test_endpoint)
        response = Response(status=500)

        with self.assertLogs(level="INFO") as cm:
            after_request_log_endpoint_metric(logger, fake_request, response)

        err_log = "ERROR:test_metric:endpoint.test-endpoint.error: status_code: [500], data: [b'']]"
        assert err_log in cm.output
        assert_latency_metric(test_endpoint, cm.output)


def assert_latency_metric(endpoint_name: str, context_manager_output: list[str]):
    startwith = f"INFO:test_metric:endpoint.{endpoint_name}.latency"
    endwith = "ms"
    for o in context_manager_output:
        if o.startswith(startwith) and o.endswith(endwith):
            return True

    return False
