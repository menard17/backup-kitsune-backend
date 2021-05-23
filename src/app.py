from get_zoom_jwt import get_zoom_jwt
from flask import request, Flask, Response
from middleware import jwt_authenticated
from fhir_proxy import get_patient

app = Flask(__name__)

@app.route("/zoom_jwt", methods=["GET"])
def zoom_jwt() -> Response:
    response = get_zoom_jwt()

    return Response(
        status = 200,
        response = response
    )

@app.route("/dummy_auth", methods=["GET"])
@jwt_authenticated
def dummy_auth() -> Response:
    response = "User authenticated. Uid: " + request.uid

    return Response(
        status = 200,
        response = response
    )

@app.route("/dummy_fhir_get", methods=["GET"])
@jwt_authenticated
def dummy_fhir_get() -> Response:
    response = "User {} has {} birthdate".format(
        request.uid,
        get_patient("bf8eb518-64c4-4f4a-b5e7-64a9435539e6")["birthDate"]
    )

    return Response(
        status = 200,
        response = response
    )

if __name__ == "__main__":
    # Used when running locally only. When deploying to Cloud Run,
    # a webserver process such as Gunicorn will serve the app.
    app.run(host="localhost", port=8080, debug=True)
