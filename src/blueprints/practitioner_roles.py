import json
import uuid
from datetime import datetime, time, timedelta
from typing import List

import pytz
from fhir.resources.practitionerrole import PractitionerRole
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
        role_type = request.args.get("role_type")
        if role_type and role_type in {"nurse", "doctor"}:
            roles = self.resource_client.search(
                "PractitionerRole", [("role", role_type)]
            )
        else:
            roles = self.resource_client.get_resources("PractitionerRole")
        roles = self.resource_client.get_resources("PractitionerRole")

        if roles.entry is None:
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
        if not (
            (start := request_body.get("start"))
            and (end := request_body.get("end"))
            and (email := request_body.get("email"))
            and (photo := request_body.get("photo"))
            and (is_doctor := request_body.get("is_doctor"))
            and (zoom_id := request_body.get("zoom_id"))
            and (zoom_password := request_body.get("zoom_password"))
            and (available_time := request_body.get("available_time"))
            and (gender := request_body.get("gender"))
        ):

            return Response(status=400, response="Body is insufficient")

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
        biographies = []
        names = get_names_ext(request_body, language_options)
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
            is_doctor,
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
        """
        This is not atomic process atm & requires multiple resources (schedule and practitionerRole).
        Also input is pure FHIR json which is not ideal
        """
        role = PractitionerRole.parse_obj(request.get_json())

        if role.id != role_id:
            return Response(status=400, response="role_id mismatch")

        claims_roles = role_auth.extract_roles(request.claims)
        if claims_roles["Practitioner"].get("id") is None:
            return Response(status=401, response="only practitioner can call the API")
        if (
            role.practitioner.reference
            != f'Practitioner/{claims_roles["Practitioner"]["id"]}'
        ):
            return Response(
                status=401,
                response="can only change practitioner role referencing to the practitioner",
            )

        # update the planning horizon of the schedule
        schedule_search = self.resource_client.search(
            "Schedule",
            search=[
                ("actor", role.id),
                (
                    "active",
                    str(True),
                ),  # assumes we only have one active schedule at the period
            ],
        )

        if schedule_search.entry is None:
            return Response(
                status=500,
                response="(unexpected) the practitioner role is missing active schedule",
            )

        schedule = schedule_search.entry[0].resource
        schedule.planningHorizon = {
            "start": role.period.start,
            "end": role.period.end,
        }
        schedule = self.resource_client.put_resource(schedule.id, schedule)

        # update the role
        role = PractitionerRole.parse_obj(request.get_json())
        role = self.resource_client.put_resource(role.id, role)

        data = {"practitioner_role": role.dict(), "schedule": schedule.dict()}
        return Response(status=200, response=json.dumps(data, default=json_serial))

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
        'is_doctor': true,
        'start': '2021-08-15T13:55:57.967345+09:00',
        'end': '2021-08-15T14:55:57.967345+09:00',
        'zoom_id': 'zoom id',
        'zoom_password': 'zoom password',
        'available_time':  {},
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
    :type language_options: List[str]

    :rtype: List[Biography]
    """
    biographies = []
    for language in language_options:
        if bio := request_body.get("bio_" + language):
            biographies.append(Biography(bio, language))
    return biographies


def get_names_ext(request_body: dict, language_options: list) -> List[HumanName]:
    """
    Returns list of HumanName. request param is comparised of prefix(given_name or family_name) and suffix connected with _.
    suffix is language code

    :param request_body: request body from http request
    :type request_body: dict
    :param language_options: list of language that are supported
    :type language_options: List[str]

    :rtype: List[HumanName]
    """
    names = []
    for language in language_options:
        if (given_name := request_body.get("given_name_" + language)) and (
            family_name := request_body.get("family_name_" + language)
        ):
            names.append(HumanName(given_name, family_name, language))
    return names
