import json
import os
from subprocess import PIPE, run
from uuid import UUID

from flask import Blueprint, Response, request

from adapters.fhir_store import ResourceClient
from services.patient_call_logs_service import PatientCallLogsService
from services.patient_service import PatientService
from utils.middleware import jwt_authenticated, jwt_authorized

calls_blueprint = Blueprint("calls", __name__, url_prefix="/calls")

APNS_TOPIC = os.getenv("APNS_TOPIC")
APPLE_PUSH_ENDPOINT = os.getenv("APPLE_PUSH_ENDPOINT")
CALLING_STATUS = "calling"
PATIENT_CALL_LOGS = "patient_call_logs"


@calls_blueprint.route("", methods=["POST"])
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def call_by_appointment():
    request_body = request.get_json()
    if request_body is None:
        return Response(status=400, response="request body is missing")
    appointment_id = request_body.get("appointment", None)
    patient_id = request_body.get("patient", None)
    return CallsController().start(appointment_id, patient_id)


class CallsController:
    def __init__(
        self,
        resource_client=None,
        patient_service=None,
        patient_call_logs_serivce=None,
    ):
        self.resource_client = resource_client or ResourceClient()
        self.patient_service = patient_service or PatientService(self.resource_client)
        self.patient_call_logs_service = (
            patient_call_logs_serivce or PatientCallLogsService()
        )

    def start(self, appointment_id: UUID, patient_id: UUID) -> Response:
        err, voip_token = self.patient_service.get_voip_token(patient_id)
        if err:
            return Response(status=400, response=err.args)
        voip_password = self._get_voip_password()
        cert = f"/voip_certificate/voip_certificate:{voip_password}"
        endpoint = f"{APPLE_PUSH_ENDPOINT}/{voip_token}"
        data = self._get_data(appointment_id)
        command = self._build_command(endpoint, cert, data)

        err, _ = self.patient_call_logs_service.upsert_call_docs(
            appointment_id, patient_id
        )

        if err:
            return Response(status=400, response=err)

        result = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)

        if result.stdout:
            return Response(
                status=400, response=f"errors with voip with {appointment_id}"
            )
        return Response(status=204)

    def _get_data(self, appointment_id: UUID) -> dict[str]:
        data = {
            "aps": {"alert": "UMed Healthcare"},
            "id": appointment_id,
            "nameCaller": "UMed Healthcare",
            "handle": "UMed Healthcare",
            "isVideo": True,
        }
        return data

    def _get_voip_password(self) -> str:
        fs_voip_password = open("/voip_password/voip_password", "r")
        return fs_voip_password.readlines()[0].strip()

    def _build_command(self, endpoint, cert, data) -> list:
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
        return command
