import logging
import os
import sys
import uuid

import flask
import requests
import stripe
import structlog
from flask import Flask
from flask_cors import CORS

from blueprints.accounts import account_blueprint
from blueprints.address import address_blueprint
from blueprints.appointments import appointment_blueprint
from blueprints.calls import calls_blueprint
from blueprints.config import config_blueprint
from blueprints.consents import consent_blueprint
from blueprints.diagnostic_reports import diagnostic_reports_blueprint
from blueprints.document_references import document_references_blueprint
from blueprints.encounters import encounters_blueprint
from blueprints.invoices import invoices_blueprint
from blueprints.lists import lists_blueprint
from blueprints.medication_requests import medication_requests_blueprint
from blueprints.messaging import messaging_blueprint
from blueprints.organizations import organization_blueprint
from blueprints.patients import patients_blueprint
from blueprints.payments import payments_blueprint
from blueprints.practitioner_roles import practitioner_roles_blueprint
from blueprints.practitioners import practitioners_blueprint
from blueprints.prequestionnaire import prequestionnaire_blueprint
from blueprints.pubsub import pubsub_blueprint
from blueprints.service_requests import service_requests_blueprint
from blueprints.slots import slots_blueprint
from blueprints.twilio_token import twilio_token_blueprint
from blueprints.verifications import verifications_blueprint
from utils.logging import add_gcp_fields
from utils.notion_setup import NotionSingleton
from utils.stripe_setup import StripeSingleton

# Structlog Logging Configuration
# The below configuration is for output structured logging for this codebase.
# This includes, but not limited to:
# - Common additional fields to log, such as log level, timestamp, filename...
# - Specific fields for every requests, such as UUID for request_id
# - Different configuration for local development (terminal) and container-based.
# Note that gunicorn needs to have a different set of configuration. See gunicorn.conf.py.
# See:
# - https://www.structlog.org/en/stable/standard-library.html#rendering-using-structlog-based-formatters-within-logging
# - https://www.structlog.org/en/stable/logging-best-practices.html#pretty-printing-vs-structured-output
# - https://www.structlog.org/en/stable/performance.html
shared_processors = [
    structlog.contextvars.merge_contextvars,
    structlog.processors.add_log_level,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
    structlog.processors.CallsiteParameterAdder(
        {
            structlog.processors.CallsiteParameter.FILENAME,
            structlog.processors.CallsiteParameter.FUNC_NAME,
            structlog.processors.CallsiteParameter.LINENO,
        }
    ),
]
structlog.configure(
    processors=shared_processors
    + [
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
if sys.stderr.isatty():
    platform_specific_processors = [
        structlog.dev.ConsoleRenderer(),
    ]
else:
    platform_specific_processors = [
        add_gcp_fields,
        structlog.processors.format_exc_info,
        structlog.processors.dict_tracebacks,
        structlog.processors.JSONRenderer(),
    ]
formatter = structlog.stdlib.ProcessorFormatter(
    foreign_pre_chain=shared_processors,
    processors=[structlog.stdlib.ProcessorFormatter.remove_processors_meta]
    + platform_specific_processors,
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
root_logger = logging.getLogger()
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

app = Flask(__name__)

origins = os.environ.get("ORIGINS")
cors = CORS(app, resources={r"*": {"origins": origins}})
app.url_map.strict_slashes = False
app.register_blueprint(account_blueprint)
app.register_blueprint(address_blueprint)
app.register_blueprint(appointment_blueprint)
app.register_blueprint(calls_blueprint)
app.register_blueprint(consent_blueprint)
app.register_blueprint(document_references_blueprint)
app.register_blueprint(encounters_blueprint)
app.register_blueprint(invoices_blueprint)
app.register_blueprint(lists_blueprint)
app.register_blueprint(organization_blueprint)
app.register_blueprint(patients_blueprint)
app.register_blueprint(payments_blueprint)
app.register_blueprint(practitioners_blueprint)
app.register_blueprint(practitioner_roles_blueprint)
app.register_blueprint(medication_requests_blueprint)
app.register_blueprint(messaging_blueprint)
app.register_blueprint(diagnostic_reports_blueprint)
app.register_blueprint(service_requests_blueprint)
app.register_blueprint(slots_blueprint)
app.register_blueprint(verifications_blueprint)
app.register_blueprint(pubsub_blueprint)
app.register_blueprint(twilio_token_blueprint)
app.register_blueprint(config_blueprint)
app.register_blueprint(prequestionnaire_blueprint)


@app.before_request
def before_request():
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        view=flask.request.path,
        request_id=str(uuid.uuid4()),
    )


@app.errorhandler(requests.HTTPError)
def handle_fhir_http_errors(err):
    # Return 503 for optimistic locking error on FHIR
    if err.response.status_code == 412:
        lock_err_msg = "the If-Match version id doesn't match the most recent version"
        if lock_err_msg in str(err.response.json()):
            return "Concurrent update, please try later.", 503

    return err.response.json(), 500


if (base_path := "SECRETS_PATH") in os.environ:
    StripeSingleton(stripe, os.environ[base_path])
    NotionSingleton.client(os.environ[base_path])
else:
    StripeSingleton(stripe)
    NotionSingleton.client()


if __name__ == "__main__":
    # Used when running locally only. When deploying to Cloud Run,
    # a webserver process such as Gunicorn will serve the app.
    app.run(host="localhost", port=8080, debug=True)
