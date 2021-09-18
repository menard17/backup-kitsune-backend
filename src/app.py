import os

import stripe
from flask import Flask, Response, request
from flask_cors import CORS

from blueprints.appointments import appointment_blueprint
from blueprints.diagnostic_reports import diagnostic_reports_blueprint
from blueprints.encounters import encounters_blueprint
from blueprints.organizations import organization_blueprint
from blueprints.patients import patients_blueprint
from blueprints.payments import payments_blueprint
from blueprints.practitioner_roles import practitioner_roles_blueprint
from blueprints.practitioners import practitioners_blueprint
from blueprints.service_requests import service_requests_blueprint
from get_zoom_jwt import get_zoom_jwt
from services.messaging_service import messaging_blueprint
from utils.middleware import jwt_authenticated
from utils.stripe_setup import StripeSingleton

app = Flask(__name__)
origins = os.environ.get("ORIGINS")
cors = CORS(app, resources={r"*": {"origins": origins}})
app.url_map.strict_slashes = False
app.register_blueprint(appointment_blueprint)
app.register_blueprint(encounters_blueprint)
app.register_blueprint(organization_blueprint)
app.register_blueprint(patients_blueprint)
app.register_blueprint(payments_blueprint)
app.register_blueprint(practitioners_blueprint)
app.register_blueprint(practitioner_roles_blueprint)
app.register_blueprint(messaging_blueprint)
app.register_blueprint(diagnostic_reports_blueprint)
app.register_blueprint(service_requests_blueprint)

if (base_path := "SECRETS_PATH") in os.environ:
    StripeSingleton(stripe, os.environ[base_path])
else:
    StripeSingleton(stripe)


@app.route("/zoom_jwt", methods=["GET"])
def zoom_jwt() -> Response:
    response = get_zoom_jwt()

    return Response(status=200, response=response)


@app.route("/dummy_auth", methods=["GET"])
@jwt_authenticated()
def dummy_auth() -> Response:
    response = "User authenticated. Uid: " + request.uid

    return Response(status=200, response=response)


if __name__ == "__main__":
    # Used when running locally only. When deploying to Cloud Run,
    # a webserver process such as Gunicorn will serve the app.
    app.run(host="localhost", port=8080, debug=True)
