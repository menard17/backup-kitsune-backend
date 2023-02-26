import structlog
import time
from flask.wrappers import Response

log = structlog.get_logger()


def before_request_add_start_time(request):
    request.start_time = time.time()


def teardown_request_log_endpoint_metric(request, error: Exception):
    """
    after_request would not be run if the function raise an error.
    We use teardown_request to log metric when unexpected error happens

    we uses the default value from flask for the request.endpoint
    """
    if error:
        log.error(
            f"endpoint.{request.endpoint}.error",
            endpoint=request.endpoint,
            error=type(error).__name__,
        )
        log_latency(request)


def after_request_log_endpoint_metric(request, response: Response):
    """
    note: after_request would not be run if the function raise an error.
    We use teardown_request to log metric when unexpected error happens

    we uses the default value from flask for the request.endpoint
    """
    log_latency(request)

    if 400 <= response.status_code <= 599:
        log.error(
            f"endpoint.{request.endpoint}.error",
            endpoint=request.endpoint,
            status_code=response.status_code,
        )
    return response


def log_latency(request):
    end_time = time.time()
    latency_in_ms = (end_time - request.start_time) * 1000
    log.info(
        f"endpoint.{request.endpoint}.latency",
        endpoint=request.endpoint,
        latency=latency_in_ms,
    )
