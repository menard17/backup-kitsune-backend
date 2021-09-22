import json
from datetime import datetime, time, timedelta

import pytz
from fhir.resources import construct_fhir_element
from fhir.resources.practitionerrole import PractitionerRole
from flask import Blueprint, Response, request

from adapters.fhir_store import ResourceClient
from json_serialize import json_serial
from services.slots_service import SlotService
from utils.datetime_encoder import datetime_encoder
from utils.middleware import jwt_authenticated, role_auth

practitioner_roles_blueprint = Blueprint(
    "practitioner_roles", __name__, url_prefix="/practitioner_roles"
)


class PractitionerRoleController:
    def __init__(self, resource_client) -> None:
        self.resource_client = resource_client

    def get_practitioner_roles(self, request):
        roles = self.resource_client.get_resources("PractitionerRole")

        if roles.entry is None:
            return Response(status=200, response=json.dumps([]))

        resp = json.dumps(
            [r.resource.dict() for r in roles.entry],
            default=json_serial,
        )
        return Response(status=200, response=resp)

    def get_practitioner_role(self, request, role_id: str):
        role = self.resource_client.get_resource(role_id, "PractitionerRole")
        return Response(status=200, response=role.json())

    def create_practitioner_role(self, request):
        role = PractitionerRole.parse_obj(request.get_json())
        role = self.resource_client.create_resource(role)

        schedule_jsondict = {
            "resourceType": "Schedule",
            "active": True,
            "actor": [
                {
                    "reference": "PractitionerRole/" + role.id,
                    "display": "PractitionerRole: " + role.id,
                }
            ],
            "planningHorizon": {
                "start": role.period.start,
                "end": role.period.end,
            },
            "comment": "auto generated schedule on practitioner role creation",
        }
        schedule = construct_fhir_element("Schedule", schedule_jsondict)
        schedule = self.resource_client.create_resource(schedule)

        data = {"practitioner_role": role.dict(), "schedule": schedule.dict()}

        return Response(status=201, response=json.dumps(data, default=json_serial))

    def update_practitioner_role(self, request, role_id):
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
    resource_client = ResourceClient()
    return PractitionerRoleController(resource_client).get_practitioner_roles(request)


@practitioner_roles_blueprint.route("/<role_id>", methods=["Get"])
@jwt_authenticated()
def get_practitioner_role_json(role_id: str):
    resource_client = ResourceClient()
    return PractitionerRoleController(resource_client).get_practitioner_role(
        request, role_id
    )


@practitioner_roles_blueprint.route("/", methods=["POST"])
@jwt_authenticated()
def create_practitioner_role():
    resource_client = ResourceClient()
    return PractitionerRoleController(resource_client).create_practitioner_role(request)


@practitioner_roles_blueprint.route("/<role_id>/", methods=["PUT"])
@jwt_authenticated()
def update_practitioner_role(role_id: str):
    resource_client = ResourceClient()
    return PractitionerRoleController(resource_client).update_practitioner_role(
        request, role_id
    )


@practitioner_roles_blueprint.route("/<role_id>/slots", methods=["POST"])
@jwt_authenticated()
def create_practitioner_role_slots(role_id: str):
    resource_client = ResourceClient()
    return PractitionerRoleController(resource_client).create_practitioner_role_slots(
        request, role_id
    )


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
    resource_client = ResourceClient()
    return PractitionerRoleController(resource_client).get_role_slots(request, role_id)
