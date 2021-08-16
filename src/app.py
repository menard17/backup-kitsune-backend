from blueprints.patients import patients_blueprint
from blueprints.organizations import organization_blueprint
from blueprints.practitioner_roles import practitioner_roles_blueprint
from blueprints.appointments import appointment_blueprint
from blueprints.payments import payments_blueprint
from get_zoom_jwt import get_zoom_jwt
from flask import request, Flask, Response
from utils.middleware import jwt_authenticated
from flask_cors import CORS
import os

app = Flask(__name__)
origins = os.environ.get("ORIGINS")
cors = CORS(app, resources={r"*": {"origins": origins}})
app.url_map.strict_slashes = False
app.register_blueprint(patients_blueprint)
app.register_blueprint(payments_blueprint)
app.register_blueprint(organization_blueprint)
app.register_blueprint(practitioner_roles_blueprint)
app.register_blueprint(appointment_blueprint)


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
