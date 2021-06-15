import pytz

from adapters.fhir_store import ResourceClient
from datetime import datetime, time, timedelta
from flask import Blueprint, request
from middleware import jwt_authenticated, jwt_authorized


doctors_blueprint = Blueprint("doctor", __name__, url_prefix="/doctors")


@doctors_blueprint.route("/<doctor_id>/slots", methods=["GET"])
@jwt_authenticated()
def get_doctor_slots(doctor_id: str) -> dict:
    """Returns list of slots of a doctor with the given time range

    :param doctor_id: uuid for doctor
    :type doctor_id: str

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

    print("search schedule")
    schedule_search = resource_client.search(
        "Schedule",
        search = [
            ("actor", doctor_id),
            ("active", str(True)),
            ("date", "ge" + start),
            ("date", "le" + end)
        ]
    )

    if schedule_search.entry is None:
        return {"data": []}

    schedule = schedule_search.entry[0].resource
    slot_search = resource_client.search(
        "Slot",
        search = [
            ("schedule", schedule.id),
            ("start", "ge" + start),
            ("start", "lt" + end),
            ("status", "free"),
        ],
    )
    if slot_search.entry is None:
        return {"data": []}
    return {"data": [e.resource.dict() for e in slot_search.entry]}
