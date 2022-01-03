import json
import uuid
from datetime import datetime, time, timedelta
from typing import List

import pytz
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
from utils.middleware import jwt_authenticated, role_auth

practitioner_roles_blueprint = Blueprint(
    "practitioner_roles", __name__, url_prefix="/practitioner_roles"
)


def to_bool(item: str) -> bool:
    true_set = {"true", "1"}
    return item.lower() in true_set


class PractitionerRoleController:
    def __init__(
        self,
        resource_client=None,
        schedule_service=None,
        practitioner_service=None,
        practitioner_role_service=None,
    ):
        self.resource_client = resource_client or ResourceClient()
        self.schdule_service = schedule_service or ScheduleService(self.resource_client)
        self.practitioner_service = practitioner_service or PractitionerService(
            self.resource_client
        )
        self.practitioner_role_service = (
            practitioner_role_service or PractitionerRoleService(self.resource_client)
        )

    def get_practitioner_roles(self) -> Response:
        """Returns roles of practitioner.
        If `role` is provided in query param, corresponding role of practitioner roles will be returned.
        If `role` is not provided in query param, all the practitioner roles are returned.

        :return: all practitioner roles are returns in JSON object
        :rtype: Response
        """
        search_clause = []

        if (role_type := request.args.get("role_type")) and role_type in {
            "nurse",
            "doctor",
        }:
            search_clause.append(("role", role_type))

        if practitoner_id := request.args.get("practitoner_id"):
            search_clause.append(("practitioner", practitoner_id))

        if search_clause:
            roles = self.resource_client.search("PractitionerRole", search_clause)

        else:
            roles = self.resource_client.get_resources("PractitionerRole")

        if roles.total == 0:
            return Response(status=200, response=json.dumps([]))

        resp = json.dumps(
            [r.resource.dict() for r in roles.entry],
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
        photo = request_body.get("photo")
        role_type = request_body.get("role_type")
        gender = request_body.get("gender")

        zoom_id, zoom_password, available_time = None, None, []
        language_options = ["en", "ja"]
        names = get_names_ext(request_body, language_options)
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
        byte_size = (PIXEL_SIZE ** 2) * 3
        if (image_size := size_from_base64(photo)) > byte_size:
            return Response(
                status=400,
                response=f"photo is: {image_size} and expected to be less than {byte_size}",
            )

        role_id = f"urn:uuid:{uuid.uuid1()}"
        pracititioner_id = f"urn:uuid:{uuid.uuid1()}"

        resources = []
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
        err, schedule = self.schdule_service.create_schedule(role_id, name, start, end)
        if err is not None:
            return Response(status=400, response=err.args[0])
        resources.append(schedule)

        resp = self.resource_client.create_resources(resources)

        # Then grant the custom claim for the caller in Firebase
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
        names = get_names_ext(request_body, language_options)
        biographies = get_biographies_ext(request_body, language_options)

        PIXEL_SIZE = 104  # Max size of image in pixel
        byte_size = (PIXEL_SIZE ** 2) * 3
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
        if ("Patient" in claims_roles) or (
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

        if start is None or end is None:
            return Response(status=400, response="must provide start and end")

        slot_service = SlotService(self.resource_client)
        err, slot = slot_service.create_slot_for_practitioner_role(
            role_id,
            start,
            end,
            status,
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

        schedule_search = self.resource_client.search(
            "Schedule",
            search=[
                ("actor", role_id),
                (
                    "active",
                    str(True),
                ),  # assumes we only have one active schedule at the period
            ],
        )

        if schedule_search.entry is None:
            return {"data": []}

        schedule = schedule_search.entry[0].resource

        slot_search = self.resource_client.search(
            "Slot",
            search=[
                ("schedule", schedule.id),
                ("start", "ge" + start),
                ("start", "lt" + end),
                ("status", status),
            ],
        )
        if slot_search.entry is None:
            return {"data": []}
        return {
            "data": [datetime_encoder(e.resource.dict()) for e in slot_search.entry]
        }


@practitioner_roles_blueprint.route("/", methods=["GET"])
@jwt_authenticated()
def get_practitioner_roles():
    return PractitionerRoleController().get_practitioner_roles()


@practitioner_roles_blueprint.route("/<role_id>", methods=["GET"])
@jwt_authenticated()
def get_practitioner_role_json(role_id: str):
    return PractitionerRoleController().get_practitioner_role(role_id)


@practitioner_roles_blueprint.route("/", methods=["POST"])
@jwt_authenticated()
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
def get_role_slots(role_id: str) -> dict:
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
