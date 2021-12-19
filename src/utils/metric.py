import logging
import time

from flask.wrappers import Response


def before_request_add_start_time(request):
    request.start_time = time.time()


def teardown_request_log_endpoint_metric(logger: logging.Logger, request, error=None):
    """
    after_request would not be run if the function raise an error.
    We use teardown_request to log metric when unexpected error happens

    we uses the default value from flask for the request.endpoint
    """
    if error:
        logger.error(f"endpoint.{request.endpoint}.error: {error}")
        log_latency(logger, request)


def after_request_log_endpoint_metric(
    logger: logging.Logger, request, response: Response
):
    """
    note: after_request would not be run if the function raise an error.
    We use teardown_request to log metric when unexpected error happens

    we uses the default value from flask for the request.endpoint
    """
    log_latency(logger, request)

    if 400 <= response.status_code <= 599:
        logger.error(
            f"endpoint.{request.endpoint}.error: status_code: [{response.status_code}], data: [{response.data}]]"
        )
    return response


def log_latency(logger: logging.Logger, request):
    end_time = time.time()
    latency_in_ms = (end_time - request.start_time) * 1000
    logger.info(f"endpoint.{request.endpoint}.latency: {latency_in_ms} ms")
