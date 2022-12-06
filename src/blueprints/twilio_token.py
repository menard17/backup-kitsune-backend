import json
import time
from datetime import datetime, timedelta

from flask import Blueprint, Response, request
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant

from adapters.fhir_store import ResourceClient
from json_serialize import json_serial
from services.appointment_service import AppointmentService
from utils.middleware import jwt_authenticated
from utils.twilio_setup import TwilioSingleton

twilio_token_blueprint = Blueprint("twilio_token", __name__, url_prefix="/twilio_token")


@jwt_authenticated()
@twilio_token_blueprint.route("/tokens", methods=["GET"])
def twilio_jwt() -> Response:
    return TwilioTokenController().get_twilio_token(request)


class TwilioTokenController:
    def __init__(
        self,
        resource_client=None,
        appointment_service=None,
        twilio_object=None,
    ):
        self.resource_client = resource_client or ResourceClient()
        self.appointment_service = appointment_service or AppointmentService(
            self.resource_client
        )
        self.twilio_object = twilio_object or TwilioSingleton.token()

    def get_twilio_token(self, request) -> Response:
        """Get jwt from api key and sec. It should be authenticated with token from firebase.
        Appointment schedule should also be checked before generating token."""

        if not (appointment_id := request.args.get("appointment_id")):
            return Response(status=400, response="missing param: appointment_id")

        if not (identity_id := request.args.get("identity_id")):
            return Response(status=400, response="missing param: identity_id")

        ontime, detail = self.appointment_service.check_appointment_ontime(
            appointment_id
        )

        if not ontime:
            return Response(status=400, response=detail)

        if not self._check_participant_valid(appointment_id, identity_id):
            return Response(status=400, response="not participant for the meeting")

        # retrieve an access token for this room
        access_token = self._get_access_token(appointment_id, identity_id)
        # return the decoded access token in the response
        return Response(
            status=200,
            response=json.dumps(
                {"token": access_token.to_jwt()},
                default=json_serial,
            ),
        )

    def _get_access_token(self, appointmend_id: str, identity_id: str) -> AccessToken:
        exp = time.mktime((datetime.now() + timedelta(hours=1)).timetuple())
        sid, secret, acc_id = self.twilio_object
        access_token = AccessToken(
            acc_id,
            sid,
            secret,
            identity=f"identity_{identity_id}",
            valid_until=exp,
        )

        room_name = f"room_no_{appointmend_id}"
        video_grant = VideoGrant(room=room_name)
        access_token.add_grant(video_grant)
        return access_token

    def _check_participant_valid(self, appointmend_id: str, identity_id: str) -> bool:
        is_valid = False
        appointment = self.appointment_service.get_appointment_by_id(
            appointmend_id
        ).dict()
        participants = appointment["participant"]

        for participant in participants:
            if participant["actor"]["reference"].split("/")[1] == identity_id:
                is_valid = True
                return is_valid

        return is_valid
