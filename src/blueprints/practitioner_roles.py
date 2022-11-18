import json
import uuid
from datetime import datetime, time, timedelta
from typing import List

import pytz
from dateutil.parser import isoparse
from flask import Blueprint, Response, request
from flask.wrappers import Request

from adapters.fhir_store import ResourceClient
from json_serialize import json_serial
from services.practitioner_role_service import PractitionerRoleService
from services.practitioner_service import Biography, HumanName, PractitionerService
from services.schedule_service import ScheduleService
from services.slots_service import SlotService
from utils.datetime_encoder import datetime_encoder
from utils.file_size import size_from_base64
from utils.middleware import jwt_authenticated, jwt_authorized, role_auth
from utils.string_manipulation import to_bool

# The minimum delay between booking time and the actual appointment
# This is done so that the doctor can have some time to prepare for the
# appointment.
MINIMUM_DELAY_BETWEEN_BOOKING = timedelta(minutes=15)

practitioner_roles_blueprint = Blueprint(
    "practitioner_roles", __name__, url_prefix="/practitioner_roles"
)


class PractitionerRoleController:
    def __init__(
        self,
        resource_client=None,
        schedule_service=None,
        practitioner_service=None,
        practitioner_role_service=None,
        slot_service=None,
    ):
        self.resource_client = resource_client or ResourceClient()
        self.schedule_service = schedule_service or ScheduleService(
            self.resource_client
        )
        self.practitioner_service = practitioner_service or PractitionerService(
            self.resource_client
        )
        self.practitioner_role_service = (
            practitioner_role_service or PractitionerRoleService(self.resource_client)
        )
        self.slot_service = slot_service or SlotService(self.resource_client)

    def get_practitioner_roles(self) -> Response:
        """Returns roles of practitioner.
        If `role` is provided in query param, corresponding role of practitioner roles will be returned.
        If `role` is not provided in query param, all the practitioner roles are returned.

        :return: all practitioner roles are returns in JSON object
        :rtype: Response
        """
        search_clause = []

        if role_type := request.args.get("role_type"):
            search_clause.append(("role", role_type))

        if practitoner_id := request.args.get("practitioner_id"):
            search_clause.append(("practitioner", practitoner_id))
        else:
            search_clause.append(("active", "true"))

        if (role_id := request.args.get("role_id")) is not None:
            search_clause.append(("_id", role_id))

        if to_bool(request.args.get("include_practitioner")):
            search_clause.append(
                ("_include:iterate", "PractitionerRole:practitioner:Practitioner")
            )

        if search_clause:
            roles = self.resource_client.search("PractitionerRole", search_clause)
        else:
            roles = self.resource_client.get_resources("PractitionerRole")

        if roles.total == 0:
            return Response(status=200, response=json.dumps([]))

        resp = json.dumps(
            [json.loads(datetime_encoder(e.resource.json())) for e in roles.entry],
            default=json_serial,
        )
        return Response(status=200, response=resp)

    def get_practitioner_role(self, role_id: uuid) -> Response:
        """Returns practitioner role with given role_id

        :param role_id: practitioner role id
        :type role_id: uuid
        :return: practitioner role in JSON object
        :rtype: Response
        """
        role = self.resource_client.get_resource(role_id, "PractitionerRole")
        return Response(status=200, response=role.json())

    def create_practitioner_role(self, request: Request):
        """Returns created practitioner role
        In order to create 'practitioner role', 'practitioner' and 'schedule' are created.
        This is done in transaction so that it's either all resources are created succeessfully
        or nothing is created. parameter is provided to unittest purpose.

        :param request: request containing body from http request
        :type request: Request
        :returns: practitioner role in JSON object
        :rtype: Response
        """
        request_body = request.get_json()
        REQUIRED_FIELDS = ["start", "end", "email", "photo", "role_type", "gender"]
        for field in REQUIRED_FIELDS:
            if request_body.get(field) is None:
                error_msg = f"{field} is missing in the request body"
                return Response(status=400, response=error_msg)

        start = request_body.get("start")
        end = request_body.get("end")
        email = request_body.get("email")
        photo = request_body.get("photo", "")
        role_type = request_body.get("role_type")
        gender = request_body.get("gender")

        zoom_id, zoom_password, available_time = None, None, []
        language_options = ["en", "ja"]
        biographies = get_biographies_ext(request_body, language_options)
        if role_type and (role_type == "doctor"):
            if not (
                (zoom_id := request_body.get("zoom_id"))
                and (zoom_password := request_body.get("zoom_password"))
                and (available_time := request_body.get("available_time"))
            ):
                return Response(
                    status=400, response="Doctor requires available time and zoom cred"
                )

        PIXEL_SIZE = 104  # Max size of image in pixel
        byte_size = (PIXEL_SIZE**2) * 3
        if photo and (image_size := size_from_base64(photo)) > byte_size:
            return Response(
                status=400,
                response=f"photo is: {image_size} and expected to be less than {byte_size}",
            )

        role_id = f"urn:uuid:{uuid.uuid1()}"
        pracititioner_id = f"urn:uuid:{uuid.uuid1()}"

        resources = []

        # Check if practitioner already exists or not
        search_clause = [("email", email)]
        practitioner_search = self.resource_client.search(
            "Practitioner",
            search=search_clause,
        )
        if practitioner_search.total > 0:
            return Response(
                status=400, response=f"practitoner exists with given email: {email}"
            )

        # Create a practitioner
        language_options = ["en", "ja"]
        names = get_names_ext(request_body, language_options, role_type)
        biographies = get_biographies_ext(request_body, language_options)
        err, pracititioner = self.practitioner_service.create_practitioner(
            pracititioner_id, email, photo, gender, biographies, names
        )

        if err is not None:
            return Response(status=400, response=err.args[0])
        resources.append(pracititioner)

        # Create a practitioner role
        name = names[0].given_name + " " + names[0].family_name
        (
            err,
            practitioner_role,
        ) = self.practitioner_role_service.create_practitioner_role(
            role_id,
            role_type,
            start,
            end,
            pracititioner_id,
            name,
            zoom_id,
            zoom_password,
            available_time,
        )
        if err is not None:
            return Response(status=400, response=err.args[0])
        resources.append(practitioner_role)

        # Create a schedule
        err, schedule = self.schedule_service.create_schedule(role_id, name, start, end)
        if err is not None:
            return Response(status=400, response=err.args[0])
        resources.append(schedule)

        if role_type == "staff":
            roles = role_auth.extract_roles(request.claims)
            if not roles or "Staff" not in roles:
                return Response(status=404, response="Insufficient permission")
            resp = self.resource_client.create_resources(resources)
            practitioner = list(
                filter(lambda x: x.resource.resource_type == "Practitioner", resp.entry)
            )[0].resource
            role_auth.grant_role(request.claims, "Staff", practitioner.id)
        else:
            resp = self.resource_client.create_resources(resources)
            practitioner = list(
                filter(lambda x: x.resource.resource_type == "Practitioner", resp.entry)
            )[0].resource
            role_auth.grant_role(request.claims, "Practitioner", practitioner.id)

        resp = list(
            filter(lambda x: x.resource.resource_type == "PractitionerRole", resp.entry)
        )[0].resource
        return Response(status=201, response=resp.json())

    def update_practitioner_role(self, request, role_id: uuid):
        """Returns modified practitioner role

        Modifies practitioner or/and practitioner role.
        This is done in transaction so that it's either all resources are modified succeessfully
        or nothing is modified.

        :param request: request containing body from http request
        :type request: Request
        :returns: practitioner role in JSON object
        :rtype: Response
        """
        request_body = request.get_json()
        start = request_body.get("start")
        end = request_body.get("end")
        photo = request_body.get("photo")
        zoom_id = request_body.get("zoom_id")
        zoom_password = request_body.get("zoom_password")
        available_time = request_body.get("available_time")
        gender = request_body.get("gender")
        language_options = ["en", "ja"]
        role_type = request_body.get("role_type")
        names = get_names_ext(request_body, language_options, role_type)
        biographies = get_biographies_ext(request_body, language_options)

        PIXEL_SIZE = 104  # Max size of image in pixel
        byte_size = (PIXEL_SIZE**2) * 3
        if photo and (image_size := size_from_base64(photo)) > byte_size:
            return Response(
                status=400,
                response=f"photo is: {image_size} and expected to be less than {byte_size}",
            )

        resources = []

        # Get PractitionerRole and Practitioner
        role = self.resource_client.get_resource(role_id, "PractitionerRole")
        practitioner_id = role.practitioner.reference
        practitioner_id_raw = practitioner_id.split("/")[1]
        practitioner = self.resource_client.get_resource(
            practitioner_id_raw, "Practitioner"
        )
        claims_roles = role_auth.extract_roles(request.claims)
        if ("Patient" in claims_roles and "Practitioner" not in claims_roles) or (
            "Practitioner" in claims_roles
            and claims_roles["Practitioner"]["id"] != practitioner_id_raw
        ):
            return Response(
                status=401,
                response="practitioners can only update their themselves",
            )

        # Modify practitioner role
        (
            err,
            pracititioner_role_bundle,
        ) = self.practitioner_role_service.update_practitioner_role(
            role,
            start,
            end,
            zoom_id,
            zoom_password,
            available_time,
        )
        if err is not None:
            return Response(status=400, response=err.args[0])

        if pracititioner_role_bundle:
            resources.append(pracititioner_role_bundle)

        # Modify practitioner
        err, pracititioner_bundle = self.practitioner_service.update_practitioner(
            practitioner, biographies, names, photo, gender
        )
        if err is not None:
            return Response(status=400, response=err.args[0])
        if pracititioner_bundle:
            resources.append(pracititioner_bundle)

        # Modify Schedule
        if start is not None or end is not None:
            schedules = self.schedule_service.get_active_schedules(role_id)
            # assume we only have 1 active schedule at once
            schedule = schedules.entry[0].resource
            if start is not None:
                schedule.planningHorizon.start = start
            if end is not None:
                schedule.planningHorizon.end = end
            schedule_bundle = self.resource_client.get_put_bundle(schedule, schedule.id)
            resources.append(schedule_bundle)

        # Call bulk process
        if resources:
            resp = self.resource_client.create_resources(resources)
            return Response(status=200, response=resp.json())
        return Response(status=200, response={})

    def create_practitioner_role_slots(self, request, role_id):
        """
        1. find role_id -> active schedule
        2. create slots for that active schedule

        :param request: request containing body from http request
        :type request: Request
        :param role_id: practitioner role id
        :type role_id: uuid
        """
        request_body = request.get_json()
        start = request_body.get("start")
        end = request_body.get("end")
        status = request_body.get("status", "busy")
        comment = request_body.get("comment")

        if start is None or end is None:
            return Response(status=400, response="must provide start and end")

        err, slot = self.slot_service.create_slot_for_practitioner_role(
            role_id,
            start,
            end,
            status,
            comment,
        )

        if err is not None:
            return Response(status=400, response=err.args[0])

        return Response(status=200, response=slot.json())

    def get_role_slots(self, request, role_id):
        tokyo_timezone = pytz.timezone("Asia/Tokyo")
        today_min = datetime.combine(datetime.now(), time.min)
        today_min = tokyo_timezone.localize(today_min)
        nine_am = today_min + timedelta(hours=9)
        six_pm = today_min + timedelta(hours=18)

        start = request.args.get("start", nine_am.isoformat())
        end = request.args.get("end", six_pm.isoformat())
        status = request.args.get("status", "free")
        not_status = request.args.get("not_status")

        schedules = self.schedule_service.get_active_schedules(role_id)
        if schedules.entry is None:
            return {"data": []}

        # assume we only have 1 active schedule at once
        schedule = schedules.entry[0].resource

        # Handling special case of generating a list of available slots
        if not_status is None and status == "free":
            # the FHIR resource package will decode the start/end time to
            # either date or datetime depending on the saved input.
            # e.g., "2022-09-02" -> date and "2021-08-15 13:55:57.967345+09:00" -> datetime.
            # this is to ensure we are using datetime.
            schedule_start = datetime.fromisoformat(
                schedule.planningHorizon.start.isoformat()
            )
            schedule_end = datetime.fromisoformat(
                schedule.planningHorizon.end.isoformat()
            )

            # add timezone
            if schedule_start.tzinfo is None:
                schedule_start = tokyo_timezone.localize(schedule_start)
            if schedule_end.tzinfo is None:
                schedule_end = tokyo_timezone.localize(schedule_end)

            start_time = self._get_earliest_start_time_for_free_booking(
                isoparse(start),
                schedule_start,
            )
            end_time = min(isoparse(end), schedule_end)

            # Retrieve practitioner's availability
            role = self.resource_client.get_resource(role_id, "PractitionerRole")
            available_time = role.availableTime

            # Search for busy slots
            additional_params = [("status:not", "free")]
            _, busy_slots = self.slot_service.search_overlapped_slots(
                schedule.id,
                start_time.isoformat(),
                end_time.isoformat(),
                additional_params,
            )

            _, slots = self.slot_service.generate_available_slots(
                schedule_id=schedule.id,
                start_time=start_time,
                end_time=end_time,
                available_time=available_time,
                busy_slots=busy_slots,
                timezone=tokyo_timezone,
            )
        # For general search cases
        else:
            additional_params = []
            if not_status:
                additional_params.append(("status:not", not_status))
            else:
                additional_params.append(("status", status))
            _, slots = self.slot_service.search_overlapped_slots(
                schedule.id, start, end, additional_params
            )

        return Response(
            status=200,
            response=json.dumps(
                {"data": [json.loads(datetime_encoder(slot.json())) for slot in slots]},
                default=json_serial,
            ),
            mimetype="application/json",
        )

    # Calculate the start time to call the backend for searching free slots
    #
    # This is done so that if the frontend asks for some slots which cannot be
    # fulfilled (since it's already passed), then we automatically reject it
    # and only return any slots after the current time + booking delay.
    #
    # Note that this would reflect the correct behavior where we have an
    # automatic slots system: free slots will be marked as unavailable after
    # the current time + minimum delay booking.
    def _get_earliest_start_time_for_free_booking(
        self,
        start_time: datetime,
        schedule_start_time: datetime,
    ) -> datetime:
        current_time_with_booking_delay = (
            datetime.now().astimezone(start_time.tzinfo) + MINIMUM_DELAY_BETWEEN_BOOKING
        )
        return max(
            start_time,
            schedule_start_time,
            current_time_with_booking_delay,
        )

    def update_status(self, request, role_id):

        if (is_active := request.args.get("active")) is None:
            return Response(status=400, response="missing param: active")

        is_active = to_bool(is_active)
        resources = []

        # Get practitioner_role and practitioner
        role = self.resource_client.get_resource(role_id, "PractitionerRole")
        practitioner_id = role.practitioner.reference
        practitioner_id = practitioner_id.split("/")[1]

        # Change the status of practitioner
        practitioner = self.resource_client.get_resource(
            practitioner_id, "Practitioner"
        )
        practitioner.active = is_active
        practitioner_bundle = self.resource_client.get_put_bundle(
            practitioner, practitioner_id
        )
        resources.append(practitioner_bundle)

        # Change the status of practitioner_role
        role.active = is_active
        role_bundle = self.resource_client.get_put_bundle(role, role_id)
        resources.append(role_bundle)

        if resources:
            _ = self.resource_client.create_resources(resources)
            return Response(status=204)
        return Response(status=204)


@practitioner_roles_blueprint.route("/", methods=["GET"])
@jwt_authenticated()
def get_practitioner_roles():
    return PractitionerRoleController().get_practitioner_roles()


@practitioner_roles_blueprint.route("/<role_id>", methods=["GET"])
@jwt_authenticated()
def get_practitioner_role_json(role_id: str):
    return PractitionerRoleController().get_practitioner_role(role_id)


@practitioner_roles_blueprint.route("/", methods=["POST"])
@jwt_authenticated(email_validation=True)
def create_practitioner_role():
    """
    Sample request body:
    {
        'role_type': 'doctor',
        'start': '2021-08-15T13:55:57.967345+09:00',
        'end': '2021-08-15T14:55:57.967345+09:00',
        'zoom_id': 'zoom id',
        'zoom_password': 'zoom password',
        'available_time':  [],
        'email': 'test@umed.jp',
        'gender': 'male',
        'family_name_en': 'Last name',
        'given_name_en': 'Given name',
        'bio_en': 'My background is ...',
        'photo': '/9j/4AAQSkZJRgABAQAAAQ...'
    }
    """
    return PractitionerRoleController().create_practitioner_role(request)


@practitioner_roles_blueprint.route("/<role_id>/", methods=["PUT"])
@jwt_authenticated()
def update_practitioner_role(role_id: str):
    """
    Sample request body:
    {
        'start': '2021-08-15T13:55:57.967345+09:00',
        'end': '2021-08-15T14:55:57.967345+09:00',
        'zoom_id': 'zoom id',
        'zoom_password': 'zoom password',
        'available_time':  [],
        'gender': 'male',
        'family_name_en': 'Last name',
        'given_name_en': 'Given name',
        'bio_en': 'My background is ...',
        'photo': '/9j/4AAQSkZJRgABAQAAAQ...'
    }
    """
    return PractitionerRoleController().update_practitioner_role(request, role_id)


@practitioner_roles_blueprint.route("/<role_id>/slots", methods=["POST"])
@jwt_authenticated()
def create_practitioner_role_slots(role_id: str):
    return PractitionerRoleController().create_practitioner_role_slots(request, role_id)


@practitioner_roles_blueprint.route("/<role_id>/slots", methods=["GET"])
@jwt_authenticated()
def get_role_slots(role_id: str) -> Response:
    """Returns list of slots of a doctor with the given time range

    Request params:
    1. start: start time of the search of slots and schedule. Use iso date format. Default to 9am today.
    2. end: end time of the search of slots and schedule. Use iso date format. Default to 6pm today.
    3. status: free or busy. Default to free.

    :param role_id: uuid for practitioner role
    :type role_id: str

    :rtype: dict
    """
    return PractitionerRoleController().get_role_slots(request, role_id)


@practitioner_roles_blueprint.route("/<role_id>", methods=["PATCH"])
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def change_status(role_id: str) -> Response:
    """Returns 204 if there is no error
    Updates status of both practitioner role and practitioner

    Request params:
    1. active: boolean on status
    """
    return PractitionerRoleController().update_status(request, role_id)


def get_biographies_ext(
    request_body: dict, language_options: List[str]
) -> List[Biography]:
    """
    Returns list of Biography. bio param is comparised of prefix(bio) and suffix connected with _.
    prefix is bio and suffix is language code

    :param request_body: request body from http request
    :type request_body: dict
    :param language_options: list of language that are supported
    :type languagepractitioner_roles_options: List[str]

    :rtype: List[Biography]
    """
    biographies = []
    for language in language_options:
        if bio := request_body.get("bio_" + language):
            biographies.append(Biography(bio, language))
    return biographies


def get_names_ext(
    request_body: dict, language_options: list, role_type: str = "doctor"
) -> List[HumanName]:
    """
    Returns list of HumanName. request param is comparised of prefix(given_name or family_name) and suffix connected with _.
    suffix is language code

    :param request_body: request body from http request
    :type request_body: dict
    :param language_options: list of language that are supported
    :type language_options: List[str]
    :param role_type: str that this is doctor or nurse
    :type language_options: List[str]

    :rtype: List[HumanName]
    """
    names = []
    for language in language_options:
        if (given_name := request_body.get("given_name_" + language)) and (
            family_name := request_body.get("family_name_" + language)
        ):
            names.append(HumanName(given_name, family_name, language, role_type))
    return names
