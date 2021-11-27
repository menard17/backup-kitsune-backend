import json
import time
from datetime import datetime, timedelta, timezone

import jwt
from flask import Blueprint, Response, request

from adapters.fhir_store import ResourceClient
from json_serialize import json_serial
from utils.middleware import jwt_authenticated
from utils.zoom_setup import ZoomObject

zoom_blueprint = Blueprint("zoom", __name__, url_prefix="/zoom_jwt")


@zoom_blueprint.route("/", methods=["GET"])
@jwt_authenticated()
def zoom_jwt() -> Response:
    return ZoomController().get_zoom_jwt(request)


class ZoomController:
    def __init__(self, resource_client=None):
        self.resource_client = resource_client or ResourceClient()

    def get_zoom_jwt(self, request, zoom_object=None) -> str:
        """Get jwt from api key and sec. It should be authenticated with token from firebase.
        Appointment schedule should also be checked before generating token."""

        if not (appointment_id := request.args.get("appointment_id")):
            return Response(status=400, response="missing param: appointment_id")

        appointment = self.resource_client.get_resource(appointment_id, "Appointment")
        if datetime.now(timezone.utc) < appointment.start - timedelta(
            minutes=5
        ):
            return Response(status=400, response="meeting is not started yet")

        if datetime.now(timezone.utc) > appointment.end:
            return Response(status=400, response="meeting is already finished")

        if not zoom_object:
            zoom_object = ZoomObject()

        zoom_api_key = zoom_object.key
        zoom_api_secret = zoom_object.secret
        exp = appointment.end

        payload = {
            "appKey": zoom_api_key,
            "iat": time.mktime(datetime.now().timetuple()),
            "exp": time.mktime(exp.timetuple()),
            "tokenExp": time.mktime(exp.timetuple()),
        }

        jwt_encoded = jwt.encode(payload, zoom_api_secret)

        return Response(
            status=200,
            response=json.dumps(
                {
                    "data": {
                        "jwt": jwt_encoded,
                    }
                },
                default=json_serial,
            ),
        )
