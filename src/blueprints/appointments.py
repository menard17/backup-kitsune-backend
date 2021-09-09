from datetime import datetime

import pytz
from fhir.resources import construct_fhir_element
from flask import Blueprint, Response, request

from adapters.fhir_store import ResourceClient
from services.slots_service import SlotService
from utils import role_auth
from utils.middleware import jwt_authenticated

appointment_blueprint = Blueprint("appointments", __name__, url_prefix="/appointments")


class AppointmentController:
    """
    Controller is the class that holds the functions for the calls of appointments blueprint.
    """

    def __init__(self, resource_client=None, slot_service=None):
        self.resource_client = resource_client or ResourceClient()
        self.slot_service = slot_service or SlotService(self.resource_client)

    def book_appointment(self):
        request_body = request.get_json()
        role_id = request_body.get("practitioner_role_id")
        patient_id = request_body.get("patient_id")
        start = request_body.get("start")
        end = request_body.get("end")

        if role_id is None:
            return Response(status=400, response="missing param: practitioner_role_id")
        claims_roles = role_auth.extract_roles(request.claims)
        if "Patient" in claims_roles and claims_roles["Patient"]["id"] != patient_id:
            return Response(
                status=401, response="could only book appointment for the patient"
            )
        if start is None:
            return Response(status=400, response="missing param: start")
        if end is None:
            return Response(status=400, response="missing param: end")

        err, slot = self.slot_service.create_slot_for_practitioner_role(
            role_id,
            start,
            end,
            "busy",
        )

        if err is not None:
            return Response(status=400, response=err.args[0])

        appointment_data = {
            "resourceType": "Appointment",
            "status": "booked",
            "description": "Booking practitioner role",
            "start": start,
            "end": end,
            "serviceType": [
                {
                    "coding": [
                        {
                            "system": "http://hl7.org/fhir/valueset-service-type.html",
                            "code": "540",
                            "display": "Online Service",
                        }
                    ]
                }
            ],
            "serviceCategory": [
                {
                    "coding": [
                        {
                            "system": "http://hl7.org/fhir/valueset-service-category.html",
                            "code": "17",
                            "display": "General Practice",
                        }
                    ]
                }
            ],
            "slot": [{"reference": f"Slot/{slot.id}"}],
            "participant": [
                {
                    "actor": {
                        "reference": f"Patient/{patient_id}",
                    },
                    "required": "required",
                    "status": "accepted",
                },
                {
                    "actor": {
                        "reference": f"PractitionerRole/{role_id}",
                    },
                    "required": "required",
                    "status": "accepted",
                },
            ],
        }
        appointment = construct_fhir_element("Appointment", appointment_data)
        appointment = self.resource_client.create_resource(appointment)
        return Response(status=202, response=appointment.json())

    def update_appointment(self, request, appointment_id: str):
        request_body = request.get_json()
        status = request_body.get("status")

        if status != "noshow":
            return Response(
                status=400, response="not supporting status update aside from noshow"
            )

        appointment = self.resource_client.get_resource(appointment_id, "Appointment")
        appointment.status = status

        resp = self.resource_client.put_resource(appointment_id, appointment)

        # data: "slot": [{"reference": "Slot/bf929953-f4df-4b54-a928-2a1ab8d5d550"}]
        # we always created one slot only on appointment. so we can hardcode to index 0.
        # and split with "/" to get the slot id.
        slot_id = appointment.slot[0].reference.split("/")[1]

        slot = self.resource_client.get_resource(slot_id, "Slot")
        slot.status = "free"
        self.resource_client.put_resource(slot_id, slot)

        return Response(status=200, response=resp.json())

    def search_appointments(self, request):
        date = request.args.get("date")
        actor_id = request.args.get("actor_id")

        if actor_id is None:
            return Response(status=400, response="missing param: actor_id")

        claims_roles = role_auth.extract_roles(request.claims)
        if "Patient" in claims_roles and claims_roles["Patient"]["id"] != actor_id:
            return Response(
                status=401,
                response="patient can only search appointment for him/herself",
            )

        if date is None:
            tokyo_timezone = pytz.timezone("Asia/Tokyo")
            now = tokyo_timezone.localize(datetime.now())
            date = now.date().isoformat()

        result = self.resource_client.search(
            "Appointment",
            search=[
                ("date", "ge" + date),
                ("actor", actor_id),
            ],
        )
        return Response(status=200, response=result.json())


@appointment_blueprint.route("/", methods=["POST"])
@jwt_authenticated()
def book_appointment():
    """
    The endpoint to book an appointment

    Sample request body:
    {
        'practitioner_role_id': '0d49bb25-97f7-4f6d-8459-2b6a18d4d170',
        'patient_id': 'd67e4a18-f386-4721-a2e7-fa6526494228',
        'start': '2021-08-15T13:55:57.967345+09:00',
        'end': '2021-08-15T14:55:57.967345+09:00'
    }
    """
    return AppointmentController().book_appointment()


@appointment_blueprint.route("/<appointment_id>/status", methods=["PUT"])
@jwt_authenticated()
def update_appointment(appointment_id: str):
    """
    Update appointment status. Currently only support to update to noshow.

    Sample Request Body:
    {
        "status": "noshow"
    }
    """
    return AppointmentController().update_appointment(request, appointment_id)


@appointment_blueprint.route("/", methods=["Get"])
@jwt_authenticated()
def search():
    """
    The endpoint to search and get a list of appointments, could search with url args.

    Args:
    * date: optional, default to current date.
            Will filter appointment with its start date to be greater or equal to the given date.
    * actor_id: required. Could be either the `patient_id` or `practitioner_role_id` of the appointment.
    """
    return AppointmentController().search_appointments(request)
