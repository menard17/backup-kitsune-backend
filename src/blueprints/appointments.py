import json
from datetime import datetime, timedelta
from uuid import UUID, uuid1

import pytz
from flask import Blueprint, Response, request

from adapters.fhir_store import ResourceClient
from blueprints.service_requests import ServiceRequestController
from json_serialize import json_serial
from services.appointment_service import AppointmentService
from services.email_notification_service import EmailNotificationService
from services.lists_service import ListsService
from services.patient_call_logs_service import PatientCallLogsService
from services.patient_service import PatientService
from services.practitioner_role_service import PractitionerRoleService
from services.schedule_service import ScheduleService
from services.service_request_service import ServiceRequestService
from services.slots_service import SlotService
from utils import role_auth
from utils.datetime_encoder import datetime_encoder
from utils.middleware import jwt_authenticated, jwt_authorized
from utils.string_manipulation import to_bool

DEFAULT_PAGE_COUNT = "300"

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
        schedule_service=None,
        email_notification_service=None,
        patient_service=None,
        practitioner_role_service=None,
        lists_service=None,
        patient_call_logs_serivce=None,
    ):
        self.resource_client = resource_client or ResourceClient()
        self.slot_service = slot_service or SlotService(self.resource_client)
        self.appointment_service = appointment_service or AppointmentService(
            self.resource_client
        )
        self.service_request_service = service_request_service or ServiceRequestService(
            self.resource_client
        )
        self.schedule_service = schedule_service or ScheduleService(
            self.resource_client
        )
        self.email_notification_service = (
            email_notification_service or EmailNotificationService()
        )
        self.patient_service = patient_service or PatientService(self.resource_client)
        self.practitioner_role_service = (
            practitioner_role_service or PractitionerRoleService(self.resource_client)
        )
        self.lists_service = lists_service or ListsService(self.resource_client)
        self.patient_call_logs_service = (
            patient_call_logs_serivce or PatientCallLogsService()
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
        service = request_body.get("service", "online")
        send_notification = request_body.get("email_notification", "true")

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
        if (
            "Practitioner" not in claims_roles
            and "Patient" in claims_roles
            and not role_auth.is_authorized(claims_roles, "Patient", patient_id)
        ):
            return Response(
                status=401, response="only book appointment for the patient"
            )

        if (start is None) or (end is None):
            return Response(status=400, response="missing param: start or end")

        resources = []

        # Get an active schedule
        schedules = self.schedule_service.get_active_schedules(role_id)

        if schedules.total == 0:
            return Response(status=400, response="No schedule is created")

        # Create New Slot Bundle
        role_rid = f"PractitionerRole/{role_id}"
        patient_rid = f"Patient/{patient_id}"

        slot_uuid = uuid1().urn
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

        # Create Request Service Bundle
        service_request_uuid = None
        if requester_id is not None or encounter_id is not None:
            service_request_uuid = uuid1().urn
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
        appointment_uuid = uuid1().urn
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
            service,
        )

        if err is not None:
            return Response(status=400, response=err.args[0])
        resources.append(appointment)

        resp = self.resource_client.create_resources(resources)

        resp = list(
            filter(lambda x: x.resource.resource_type == "Appointment", resp.entry)
        )[0].resource

        err_logs, _ = self.patient_call_logs_service.upsert_call_docs(
            resp.id, patient_id
        )

        if err_logs:
            return Response(status=400, response=err_logs)

        if send_notification != "false":
            self._send_notification(appointment)
        return Response(status=201, response=resp.json())

    def get_appointment(self, appointment_id: str) -> Response:
        """Get appointment information by the ID.

        :returns: Appointment object conformed with FHIR
        :rtype: Response
        """
        appointment = self.appointment_service.get_appointment_by_id(appointment_id)
        return Response(
            status=200,
            response=json.dumps({"data": datetime_encoder(appointment.dict())}),
        )

    def update_appointment(self, request, appointment_id: str) -> Response:
        """Updates status of appointment and frees dependent slot
        This method is supporting transactional call

        :returns: updated appointment in JSON object
        :rtype: Response
        """
        request_body = request.get_json()
        status = request_body.get("status")
        send_notification = request_body.get("email_notification", "true")

        resources = []
        err, appointment = self.appointment_service.update_appointment_status(
            appointment_id, status
        )
        resources.append(appointment)
        if err is not None:
            return Response(status=400, response=err.args[0])

        appointment_json = json.loads(appointment["resource"].json())

        # free slots, assuming at most one slot
        slots = appointment_json["slot"]
        if len(slots) > 0 and slots[0].get("reference"):
            slot_id = slots[0]["reference"].split("/")[1]
            err, slot = self.slot_service.update_slot(slot_id, "free")
            if err is not None:
                return Response(status=400, response=err.args[0])
            resources.append(slot)

        resp = self.resource_client.create_resources(resources)
        resp = list(
            filter(lambda x: x.resource.resource_type == "Appointment", resp.entry)
        )[0].resource

        if send_notification != "false" and (
            status == "noshow" or status == "cancelled"
        ):
            self._send_notification(appointment, True)
        return Response(status=200, response=resp.json())

    def link(self, link: str) -> Response:
        ok, err_resp = self.appointment_service.check_link(request, link)
        if not ok:
            return err_resp

        result = self.resource_client.link(link)
        resp_dict = {
            "data": [
                json.loads(datetime_encoder(e.resource.json())) for e in result.entry
            ],
        }
        for link in result.link:
            if link.relation == "next":
                resp_dict["next_link"] = link.url

        return Response(
            status=200,
            response=json.dumps(resp_dict, default=json_serial),
        )

    def search_appointments(self, request, service_request_id: str = None) -> Response:
        """Returns list of appointments matching searching query
        :returns: Json list of appointments
        :rtype: Response
        """
        date = request.args.get("date")  # deprecated, use start_date instead. AB#775
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        actor_id = request.args.get("actor_id")
        status = request.args.get("status")
        include_practitioner = to_bool(request.args.get("include_practitioner"))
        include_patient = to_bool(request.args.get("include_patient"))
        include_encounter = to_bool(request.args.get("include_encounter"))

        count = request.args.get("count", DEFAULT_PAGE_COUNT)
        count = int(count)

        if start_date is not None and date is not None:
            return Response(
                status=400,
                response="both date and start_date supplied. Use start_date.",
            )

        claims_roles = role_auth.extract_roles(request.claims)
        if actor_id is None and "Staff" not in claims_roles:
            return Response(status=400, response="missing param: actor_id")

        if actor_id is not None and not role_auth.is_authorized(
            claims_roles, "Patient", actor_id
        ):
            return Response(
                status=401,
                response="Unauthorized for the actor_id",
            )

        if status and not self.is_valid_appointment_status(status=status):
            return Response(status=401, response=f"invalid status: {status}")

        search_clause = []

        if include_practitioner:
            search_clause.append(
                ("_include:iterate", "Appointment:actor:PractitionerRole")
            )
            search_clause.append(("_include:iterate", "PractitionerRole:practitioner"))

        if include_patient:
            search_clause.append(("_include:iterate", "Appointment:actor:Patient"))

        if include_encounter:
            search_clause.append(("_revinclude:iterate", "Encounter:appointment"))

        if service_request_id:
            search_clause.append(("basedOn", service_request_id))

        if actor_id:
            search_clause.append(("actor", actor_id))

        if status:
            search_clause.append(("status", status))

        # only one of `date` or `start_date` should be requested
        # if nothing is supplied, will default to search from "today"
        if date is None and start_date is None:
            tokyo_timezone = pytz.timezone("Asia/Tokyo")
            now = tokyo_timezone.localize(datetime.now())
            search_clause.append(("date", "ge" + now.date().isoformat()))
        if date:
            search_clause.append(("date", "ge" + date))
        if start_date:
            search_clause.append(("date", "ge" + start_date))
        if end_date:
            search_clause.append(("date", "le" + end_date))

        search_clause.append(("_count", f"{count}"))

        result = self.resource_client.search(
            "Appointment",
            search=search_clause,
        )
        entries = result.entry
        if entries is None:
            return Response(
                status=200, response=json.dumps({"data": []}, default=json_serial)
            )

        resp_dict = {
            "data": [json.loads(datetime_encoder(e.resource.json())) for e in entries],
        }

        # if there is next page, add to `next_link`
        # see: https://www.hl7.org/fhir/http.html#paging
        for link in result.link:
            if link.relation == "next":
                resp_dict["next_link"] = link.url

        return Response(
            status=200,
            response=json.dumps(resp_dict, default=json_serial),
        )

    @staticmethod
    def is_valid_appointment_status(status):
        status_set = {"booked", "fulfilled", "cancelled", "noshow"}
        return status in status_set

    def _send_notification(self, appointment, cancellation=False):
        is_visit = appointment["resource"].serviceType[0].coding[0].code != "540"
        start = appointment["resource"].start
        end = appointment["resource"].end
        participants = appointment["resource"].participant
        patient_id = list(
            filter(lambda x: "Patient" in x.actor.reference, participants)
        )[0].actor.reference.split("/")[1]
        role_id = list(
            filter(lambda x: "PractitionerRole" in x.actor.reference, participants)
        )[0].actor.reference.split("/")[1]
        _, patient_name = self.patient_service.get_patient_name(patient_id)
        _, patient_email = self.patient_service.get_patient_email(patient_id)
        (
            _,
            en_practitioner_name,
        ) = self.practitioner_role_service.get_practitioner_name("ABC", role_id)
        (
            _,
            ja_practitioner_name,
        ) = self.practitioner_role_service.get_practitioner_name("IDE", role_id)
        self.email_notification_service.send(
            start,
            end,
            patient_name,
            en_practitioner_name,
            ja_practitioner_name,
            patient_email,
            is_visit,
            cancellation,
        )

    def create_appointment_on_queue(
        self, list_id: str, practitioner_id: UUID
    ) -> Response:
        resources = []
        search_clause = []
        search_clause.append(("practitioner", practitioner_id))
        practitioner_role = self.resource_client.search(
            "PractitionerRole", search_clause
        )
        practitioner_role_json = json.loads(practitioner_role.json())
        role_id = practitioner_role_json["entry"][0]["resource"]["id"]
        top_queue_patient, lists = self.lists_service.dequeue(list_id)
        lock_header = self.resource_client.last_seen_etag
        if top_queue_patient is None:
            return Response(status=400, response="No Patient in list")
        resources.append(lists)
        jst = pytz.timezone("Asia/Tokyo")
        now = datetime.now().astimezone(jst)
        start = now
        end = now + timedelta(minutes=10)
        role_rid = f"PractitionerRole/{role_id}"
        patient_rid = f"Patient/{top_queue_patient}"

        # validation for start time and end time for doctor
        doctor_is_available = (
            self.practitioner_role_service.schedule_is_available_for_doctor(
                role_id, start, end
            )
        )
        if not doctor_is_available:
            # change response message
            return Response(status=400, response="Doctor is not available")

        # Create Appointment Bundle
        appointment_uuid = uuid1().urn
        (
            err,
            appointment,
        ) = self.appointment_service.create_appointment_for_practitioner_role(
            role_rid,
            start.isoformat(),
            end.isoformat(),
            None,
            patient_rid,
            "walkin",
            None,
            appointment_uuid,
            "online",
        )

        if err is not None:
            return Response(status=400, response=err.args[0])
        resources.append(appointment)

        resp = self.resource_client.create_resources(resources, lock_header)
        resp = list(
            filter(lambda x: x.resource.resource_type == "Appointment", resp.entry)
        )[0].resource

        err_logs, _ = self.patient_call_logs_service.upsert_call_docs(
            resp.id, top_queue_patient
        )

        if err_logs:
            return Response(status=400, response=err_logs)

        return Response(status=201, response=resp.json())


@appointment_blueprint.route("/", methods=["POST"])
@jwt_authenticated()
def book_appointment():
    """
    The endpoint to book an appointment
    service_request_id is optional argument
    prev_encounter_id is optional argument
    requester_id is optional argument
    service is optional argument

    Sample request body:
    {
        'practitioner_role_id': '0d49bb25-97f7-4f6d-8459-2b6a18d4d170',
        'patient_id': 'd67e4a18-f386-4721-a2e7-fa6526494228',
        'start': '2021-08-15T13:55:57.967345+09:00',
        'end': '2021-08-15T14:55:57.967345+09:00',
        'service_request_id': '0d49bb25-97f7-4f6d-8459-2b6a18d4d171',
        'service_type': 'followup',
        'prev_encounter_id': '0d49bb25-97f7-4f6d-8459-2b6a18d4d172',
        'requester_id':  '0d49bb25-97f7-4f6d-8459-2b6a18d4d173',
        'service': 'visit',
        'email_notification': 'false'
    }
    """
    return AppointmentController().book_appointment()


@appointment_blueprint.route("/<appointment_id>", methods=["GET"])
@jwt_authenticated()
def get_appointment(appointment_id: str):
    return AppointmentController().get_appointment(appointment_id)


@appointment_blueprint.route("/<appointment_id>/status", methods=["PUT"])
@jwt_authenticated()
def update_appointment(appointment_id: str):
    """
    Update appointment status. Currently suppports nowshow and cancelled

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
    * actor_id: optional. Could be either the `patient_id` or `practitioner_role_id` of the appointment.
    * include_practitioner: optional. With this argument, practitoner details are added for each appointment
    * include_patient: optional. With this argument, patient details are added for each appointment
    * status: status of appointment
    """

    # This is for pagination. FHIR will return a link for the next page.
    # And we proxy the result of the link.
    next_link = request.args.get("next_link")
    if next_link:
        return AppointmentController().link(next_link)

    encounter_id = request.args.get("encounter_id")
    actor_id = request.args.get("actor_id")
    data = json.loads(
        ServiceRequestController().get_service_requests(actor_id, encounter_id).data
    )
    service_request_id = None
    if len(data["data"]) > 0:
        service_request_id = data["data"][0]["id"]

    return AppointmentController().search_appointments(request, service_request_id)


@appointment_blueprint.route(
    "/list/<list_id>/practitioner/<practitioner_id>", methods=["POST"]
)
@jwt_authenticated()
@jwt_authorized("/Practitioner/{practitioner_id}")
def create_appointment_on_queue(list_id: str, practitioner_id: str) -> Response:
    """
    the patient creates a appointment for doctor
    """
    return AppointmentController().create_appointment_on_queue(list_id, practitioner_id)
