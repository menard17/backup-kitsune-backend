import pytz
import json

from adapters.fhir_store import ResourceClient
from datetime import datetime, time, timedelta
from flask import Blueprint, request, Response
from middleware import jwt_authenticated, jwt_authorized
from fhir.resources.practitionerrole import PractitionerRole
from fhir.resources import construct_fhir_element


practitioner_roles_blueprint = Blueprint("practitioner_roles", __name__, url_prefix="/practitioner_roles")

@practitioner_roles_blueprint.route("/", methods=["POST"])
# @jwt_authenticated()
def create_practitioner_role():
    resource_client = ResourceClient()
    role = PractitionerRole.parse_obj(request.get_json())
    role = resource_client.create_resource(role)

    schedule_jsondict = {
        "resourceType": "Schedule",
        "active": True,
        "actor": [{
            "reference": "PractitionerRole/" + role.id,
            "display": "PractitionerRole: " + role.id,
        }],
        "planningHorizon": {
            "start": role.period.start,
            "end": role.period.end,
        },
        "comment": "auto generated schedule on practitioner role creation",
    }
    schedule = construct_fhir_element("Schedule", schedule_jsondict)
    schedule = resource_client.create_resource(schedule)

    data = {
        "practitioner_role": role.json(),
        "schedule": schedule.json()
    }

    return Response(status=202, response=json.dumps(data))


@practitioner_roles_blueprint.route("/<role_id>/slots", methods=["POST"])
# @jwt_authenticated()
def create_practitioner_role_slots(role_id: str):
    """
    1. find role_id -> active schedule
    2. create slots for that active schedule
    """
    request_body = request.get_json()
    start = request_body.get("start")
    end = request_body.get("end")
    status = request_body.get("status")

    if start is None or end is None:
        return Response(status=400, response="must provide start and end")

    resource_client = ResourceClient()
    schedule_search = resource_client.search(
        "Schedule",
        search = [
            ("actor", role_id),
            ("active", str(True)), # assumes single active schedule at a time
        ]
    )

    if schedule_search.entry is None:
        return Response(status=404, response="cannot find schedule")

    # check if the time is available
    schedule = schedule_search.entry[0].resource
    slot_search = resource_client.search(
        "Slot",
        search = [
            ("schedule", schedule.id),
            ("start", "ge" + start),
            ("start", "lt" + end),
            ("status", "busy"),
        ],
    )
    if slot_search.entry is not None:
        return Response(status=400, response="the time is already booked")

    slot_jsondict = {
        "resourceType": "Slot",
        "schedule": {
            "reference": "Schedule/" + schedule.id
        },
        "status": status or "busy",
        "start": start,
        "end": end,
        "comment": "slot creation from backend"
    }
    slot = construct_fhir_element("Slot", slot_jsondict)
    slot = resource_client.create_resource(slot)
    return Response(status=200, response=slot.json())


@practitioner_roles_blueprint.route("/<role_id>/slots", methods=["GET"])
# @jwt_authenticated()
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

    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    today_min = datetime.combine(datetime.now(), time.min)
    today_min = tokyo_timezone.localize(today_min)
    nine_am = today_min + timedelta(hours=9)
    six_pm = today_min + timedelta(hours=18)

    start = request.args.get("start", nine_am.isoformat())
    end = request.args.get("end", six_pm.isoformat())
    status = request.args.get("status", "free")

    print("search schedule")
    schedule_search = resource_client.search(
        "Schedule",
        search = [
            ("actor", role_id),
            ("active", str(True)), # assumes we only have one active schedule at the period
        ]
    )

    if schedule_search.entry is None:
        return {"data": []}

    schedule = schedule_search.entry[0].resource
    print("search slots")
    slot_search = resource_client.search(
        "Slot",
        search = [
            ("schedule", schedule.id),
            ("start", "ge" + start),
            ("start", "lt" + end),
            ("status", status),
        ],
    )
    if slot_search.entry is None:
        return {"data": []}
    return {"data": [e.resource.dict() for e in slot_search.entry]}
