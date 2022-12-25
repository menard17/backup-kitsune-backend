import os
from logging.config import dictConfig

import requests
import stripe
from flask import Flask, request
from flask_cors import CORS

from blueprints.accounts import account_blueprint
from blueprints.address import address_blueprint
from blueprints.appointments import appointment_blueprint
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
from blueprints.pubsub import pubsub_blueprint
from blueprints.service_requests import service_requests_blueprint
from blueprints.slots import slots_blueprint
from blueprints.twilio_token import twilio_token_blueprint
from blueprints.verifications import verifications_blueprint
from utils.metric import (
    after_request_log_endpoint_metric,
    before_request_add_start_time,
    teardown_request_log_endpoint_metric,
)
from utils.notion_setup import NotionSingleton
from utils.stripe_setup import StripeSingleton

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["wsgi"]},
    }
)

app = Flask(__name__)

origins = os.environ.get("ORIGINS")
cors = CORS(app, resources={r"*": {"origins": origins}})
app.url_map.strict_slashes = False
app.register_blueprint(account_blueprint)
app.register_blueprint(address_blueprint)
app.register_blueprint(appointment_blueprint)
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


@app.before_request
def before_request():
    return before_request_add_start_time(request)


@app.after_request
def after_request(response):
    return after_request_log_endpoint_metric(app.logger, request, response)


@app.teardown_request
def teardown_request(err=None):
    teardown_request_log_endpoint_metric(app.logger, request, err)


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
