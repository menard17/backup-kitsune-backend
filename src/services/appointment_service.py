import uuid
from datetime import datetime, timedelta, timezone

from fhir.resources import construct_fhir_element
from flask import Response
from flask.wrappers import Request

from adapters.fhir_store import ResourceClient
from utils import role_auth
from utils.system_code import ServiceType, SystemCode


class AppointmentService:
    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def create_appointment_for_practitioner_role(
        self,
        role_id,
        start,
        end,
        slot_id,
        patient_id,
        service_type: ServiceType,
        service_request_id,
        appointment_uuid: str = None,
        service: str = None,
    ):
        if not service:
            service = "online"

        appointment_jsondict = {
            "resourceType": "Appointment",
            "status": "booked",
            "description": "Booking practitioner role",
            "start": start,
            "end": end,
            "serviceType": [{"coding": [SystemCode.service(service)]}],
            "serviceCategory": [{"coding": [SystemCode.general_practice()]}],
            "appointmentType": {
                "coding": [SystemCode.appointment_service_type(service_type)]
            },
            "slot": [{"reference": slot_id}],
            "participant": [
                {
                    "actor": {
                        "reference": patient_id,
                    },
                    "required": "required",
                    "status": "accepted",
                },
                {
                    "actor": {
                        "reference": role_id,
                    },
                    "required": "required",
                    "status": "accepted",
                },
            ],
        }

        if service_request_id is not None:
            appointment_jsondict["basedOn"] = [
                {
                    "reference": service_request_id,
                    "display": "Instruction",
                }
            ]
        appointment = construct_fhir_element(
            appointment_jsondict["resourceType"], appointment_jsondict
        )
        appointment = self.resource_client.get_post_bundle(
            appointment, appointment_uuid
        )
        return None, appointment

    def update_appointment_status(
        self, appointment_id: uuid, status: str, cancel_reason: str = "patient"
    ):
        cancel_status = ["noshow", "cancelled"]
        if status not in cancel_status:
            return (
                Exception(f"Status can only be noshow or cancelled. status: {status}"),
                None,
            )

        appointment_response = self.resource_client.get_resource(
            appointment_id, "Appointment"
        )
        if appointment_response.status in cancel_status:
            return (
                Exception(f"Status is already set to: {appointment_response.status}"),
                None,
            )

        appointment_response.status = status
        if status == "cancelled":
            appointment_response.cancelationReason = {
                "coding": [SystemCode.appointment_cancel_type(cancel_reason)]
            }
        appointment = construct_fhir_element("Appointment", appointment_response)
        appointment = self.resource_client.get_put_bundle(appointment, appointment_id)

        return None, appointment

    def check_appointment_ontime(self, appointment_id: uuid):
        appointment = self.resource_client.get_resource(appointment_id, "Appointment")
        if datetime.now(timezone.utc) < appointment.start - timedelta(minutes=5):
            return False, "meeting is not started yet"

        if datetime.now(timezone.utc) > appointment.end:
            return False, "meeting is already finished"

        return True, None

    def check_link(self, request: Request, link: str) -> tuple[bool, Response]:
        """
        This sanity checks the link for security reason to disallow arbitrary calls to get
        proxy result of the FHIR.

        We add validation on the link to check it is related to the Appointment search.
        Note that the format might be coupled with the FHIR provider (GCP for now).
        Different provider might have different link schema. It is not part of the FHIR protocol.

        A sample URL from GCP:
        https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/Appointment/?_count=1&actor=87c802f0-c486-438d-b2e9-e06543303b4c&date=ge2022-05-21&_page_token=Cjj3YokQdv%2F%2F%2F%2F%2BABd%2BH721RFgD%2FAf%2F%2BNWM4NDM2YmQ3ZWExOTZiYTE5NzAyMDQ4Njc4NjMyOWUAARABIZRNcFwxQ70GOQAAAACJ73adSAFQAFoLCbs%2BeLJbiDrKEANg2qiOZGgB
        """

        def parse_actor_id(link: str) -> tuple[str, Response]:
            params_str = link.split("?")[1]  # the part of: '?a=xxx&b=xxx&c=xxx'
            specific_params = params_str.split("&")  # ['a=xxx', 'b=xxx', 'c=xxx']
            actor_params = list(filter(lambda p: "actor=" in p, specific_params))
            if len(actor_params) > 1:
                return None, Response(status=400, response="invalid link")
            elif len(actor_params) == 1:
                return actor_params[0].split("=")[1], None

            # doctor can see all appointments, okay to be without specific actor id
            return None, None

        actor_id, err_resp = parse_actor_id(link)
        if err_resp is not None:
            return False, err_resp

        claim_roles = role_auth.extract_roles(request.claims)
        # patient can only see his/her own appointments
        if (
            "Practitioner" not in claim_roles
            and "Patient" in claim_roles
            and claim_roles["Patient"]["id"] != actor_id
        ):
            return False, Response(status=401, response="not authorized")

        if "Appointment" not in link:
            return False, Response(status=400, response="not link for appointment")

        return True, None
