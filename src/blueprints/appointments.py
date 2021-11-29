import json
import uuid
from datetime import datetime

import pytz
from flask import Blueprint, Response, request

from adapters.fhir_store import ResourceClient
from blueprints.service_requests import ServiceRequestController
from json_serialize import json_serial
from services.appointment_service import AppointmentService
from services.service_request_service import ServiceRequestService
from services.slots_service import SlotService
from utils import role_auth
from utils.datetime_encoder import datetime_encoder
from utils.middleware import jwt_authenticated

appointment_blueprint = Blueprint("appointments", __name__, url_prefix="/appointments")


class AppointmentController:
    """
    Controller is the class that holds the functions for the calls of appointments blueprint.
    """

    def __init__(
        self,
        resource_client=None,
        slot_service=None,
        appointment_service=None,
        service_request_service=None,
    ):
        self.resource_client = resource_client or ResourceClient()
        self.slot_service = slot_service or SlotService(self.resource_client)
        self.appointment_service = appointment_service or AppointmentService(
            self.resource_client
        )
        self.service_request_service = service_request_service or ServiceRequestService(
            self.resource_client
        )

    def book_appointment(self) -> Response:
        """Creates appointment and busy slot with given practitioner role and patient
        This method is supporting transactional call

        :returns: created appointment in JSON object
        :rtype: Response
        """
        request_body = request.get_json()
        encounter_id = request_body.get("prev_encounter_id")
        requester_id = request_body.get("requester_id")

        if (
            (role_id := request_body.get("practitioner_role_id")) is None
            or (patient_id := request_body.get("patient_id")) is None
            or (start := request_body.get("start")) is None
            or (end := request_body.get("end")) is None
            or (service_type := request_body.get("service_type")) is None
        ):
            return Response(
                status=400,
                response="missing param: practitioner_role_id, patient_id, start, end, or service_type",
            )

        claims_roles = role_auth.extract_roles(request.claims)
        if "Patient" in claims_roles and claims_roles["Patient"]["id"] != patient_id:
            return Response(
                status=401, response="could only book appointment for the patient"
            )

        if (start is None) or (end is None):
            return Response(status=400, response="missing param: start or end")

        resources = []

        # Create Slot Bundle
        slot_uuid = f"urn:uuid:{uuid.uuid1()}"
        patient_rid = f"Patient/{patient_id}"
        role_rid = f"PractitionerRole/{role_id}"
        err, slot = self.slot_service.create_slot_bundle(
            role_rid,
            start,
            end,
            slot_uuid,
            "busy",
        )

        if err is not None:
            return Response(status=400, response=err.args[0])
        resources.append(slot)

        # Creeate Request Service Bundle
        service_request_uuid = None
        if requester_id is not None or encounter_id is not None:
            service_request_uuid = f"urn:uuid:{uuid.uuid1()}"
            encounter_rid = f"Encounter/{encounter_id}"
            requester_rid = f"PractitionerRole/{requester_id}"
            err, service_request = self.service_request_service.create_service_request(
                service_request_uuid,
                patient_rid,
                role_rid,
                requester_rid,
                encounter_rid,
            )

            if err is not None:
                return Response(status=400, response=err.args[0])
            resources.append(service_request)

        # Create Appointment Bundle
        appointment_uuid = f"urn:uuid:{uuid.uuid1()}"
        (
            err,
            appointment,
        ) = self.appointment_service.create_appointment_for_practitioner_role(
            role_rid,
            start,
            end,
            slot_uuid,
            patient_rid,
            service_type,
            service_request_uuid,
            appointment_uuid,
        )

        if err is not None:
            return Response(status=400, response=err.args[0])
        resources.append(appointment)

        resp = self.resource_client.create_resources(resources)
        resp = list(
            filter(lambda x: x.resource.resource_type == "Appointment", resp.entry)
        )[0].resource
        return Response(status=201, response=resp.json())

    def update_appointment(self, request, appointment_id: str) -> Response:
        """Updates status of appointment and frees dependent slot
        This method is supporting transactional call

        :returns: updated appointment in JSON object
        :rtype: Response
        """
        request_body = request.get_json()
        status = request_body.get("status")

        if status != "noshow":
            return Response(
                status=400, response="not supporting status update aside from noshow"
            )
        resources = []

        err, appointment = self.appointment_service.update_appointment_status(
            appointment_id, status
        )
        resources.append(appointment)
        if err is not None:
            return Response(status=400, response=err.args[0])

        appointment_json = json.loads(appointment["resource"].json())
        slot_id = appointment_json["slot"][0]["reference"].split("/")[1]
        err, slot = self.slot_service.free_slot(slot_id)
        if err is not None:
            return Response(status=400, response=err.args[0])

        resources.append(slot)
        resp = self.resource_client.create_resources(resources)
        resp = list(
            filter(lambda x: x.resource.resource_type == "Appointment", resp.entry)
        )[0].resource
        return Response(status=200, response=resp.json())

    def search_appointments(self, request, service_request_id: str = None) -> Response:
        """ "Returns list of appointments matching searching query

        :returns: Json list of appointments
        :rtype: Response
        """
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

        search_clause = []

        if service_request_id:
            search_clause.append(("basedOn", service_request_id))
        if date is None:
            tokyo_timezone = pytz.timezone("Asia/Tokyo")
            now = tokyo_timezone.localize(datetime.now())
            date = now.date().isoformat()
        search_clause.append(("date", "ge" + date))
        search_clause.append(("actor", actor_id))

        result = self.resource_client.search(
            "Appointment",
            search=search_clause,
        )
        if result.entry is None:
            return Response(
                status=200, response=json.dumps({"data": []}, default=json_serial)
            )
        return Response(
            status=200,
            response=json.dumps(
                {"data": [datetime_encoder(e.resource.dict()) for e in result.entry]},
                default=json_serial,
            ),
        )


@appointment_blueprint.route("/", methods=["POST"])
@jwt_authenticated()
def book_appointment():
    """
    The endpoint to book an appointment
    service_request_id is optional argument

    Sample request body:
    {
        'practitioner_role_id': '0d49bb25-97f7-4f6d-8459-2b6a18d4d170',
        'patient_id': 'd67e4a18-f386-4721-a2e7-fa6526494228',
        'start': '2021-08-15T13:55:57.967345+09:00',
        'end': '2021-08-15T14:55:57.967345+09:00',
        'service_request_id': '0d49bb25-97f7-4f6d-8459-2b6a18d4d171',
        'service_type': 'FOLLOWUP',
        'prev_encounter_id': '0d49bb25-97f7-4f6d-8459-2b6a18d4d172',
        'requester_id':  '0d49bb25-97f7-4f6d-8459-2b6a18d4d173'
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
    if encounter id is provided, appointment that is associated to service request
    that's associated to encounter will be returned.

    Args:
    * date: optional, default to current date.
            Will filter appointment with its start date to be greater or equal to the given date.
    * actor_id: required. Could be either the `patient_id` or `practitioner_role_id` of the appointment.

    """
    encounter_id = request.args.get("encounter_id")
    patient_id = request.args.get("actor_id")
    data = json.loads(
        ServiceRequestController().get_service_requests(patient_id, encounter_id).data
    )
    service_request_id = None
    if len(data["data"]) > 0:
        service_request_id = data["data"][0]["id"]
    return AppointmentController().search_appointments(request, service_request_id)
