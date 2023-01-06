import json
import os
from subprocess import PIPE, run
from uuid import UUID

from flask import Blueprint, Response, request

from adapters.fhir_store import ResourceClient
from services.patient_service import PatientService
from utils.middleware import jwt_authenticated, jwt_authorized

calls_blueprint = Blueprint("calls", __name__, url_prefix="/calls")

APNS_TOPIC = os.getenv("APNS_TOPIC")
APPLE_PUSH_ENDPOINT = os.getenv("APPLE_PUSH_ENDPOINT")


@calls_blueprint.route("", methods=["POST"])
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def call_by_appointment():
    request_body = request.get_json()
    appointment_id = request_body.get("appointment")
    patient_id = request_body.get("patient")
    return CallsController().start(appointment_id, patient_id)


class CallsController:
    def __init__(self, resource_client=None, patient_service=None):
        self.resource_client = resource_client or ResourceClient()
        self.patient_service = patient_service or PatientService(self.resource_client)

    def start(self, appointment_id: str, patient_id: UUID) -> Response:
        err, voip_token = self.patient_service.get_voip_token(patient_id)
        if err:
            return Response(status=400, response=err)

        fs_voip_password = open("/voip_password/voip_password", "r")
        voip_password = fs_voip_password.readlines()[0].strip()
        cert = f"/voip_certificate/voip_certificate:{voip_password}"
        endpoint = f"{APPLE_PUSH_ENDPOINT}/{voip_token}"
        data = {
            "aps": {"alert": "UMed Healthcare"},
            "id": appointment_id,
            "nameCaller": "UMed Healthcare",
            "handle": "UMed Healthcare",
            "isVideo": True,
        }
        command = [
            "curl",
            "-v",
            "-d",
            json.dumps(data),
            "-H",
            f"apns-topic: {APNS_TOPIC}",
            "-H",
            "apns-push-type: voip",
            "--http2",
            "--cert",
            cert,
            endpoint,
        ]

        result = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        if result.stdout:
            return Response(
                status=400, response=f"errors with voip with {appointment_id}"
            )
        return Response(status=201)
