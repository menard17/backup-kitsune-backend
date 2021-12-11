import json
import time
from datetime import datetime

import jwt
from flask import Blueprint, Response, request

from adapters.fhir_store import ResourceClient
from json_serialize import json_serial
from services.appointment_service import AppointmentService
from utils.middleware import jwt_authenticated
from utils.zoom_setup import ZoomObject

zoom_blueprint = Blueprint("zoom", __name__, url_prefix="/zoom_jwt")


@zoom_blueprint.route("/", methods=["GET"])
@jwt_authenticated()
def zoom_jwt() -> Response:
    return ZoomController().get_zoom_jwt(request)


class ZoomController:
    def __init__(
        self,
        resource_client=None,
        appointment_service=None,
    ):
        self.resource_client = resource_client or ResourceClient()
        self.appointment_service = appointment_service or AppointmentService(
            self.resource_client
        )

    def get_zoom_jwt(self, request, zoom_object=None) -> str:
        """Get jwt from api key and sec. It should be authenticated with token from firebase.
        Appointment schedule should also be checked before generating token."""

        if not (appointment_id := request.args.get("appointment_id")):
            return Response(status=400, response="missing param: appointment_id")

        ontime, detail, appointment = self.appointment_service.check_appointment_ontime(
            appointment_id
        )
        if not ontime:
            return Response(status=400, response=detail)

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
