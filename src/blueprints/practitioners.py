import pytz

from firebase_admin import auth
from flask import Blueprint, request, Response
from datetime import datetime, time, timedelta

from fhir.resources.practitioner import Practitioner
from adapters.fhir_store import ResourceClient
from utils.middleware import jwt_authenticated
from utils.email_verification import is_email_verified, is_email_in_allowed_list


practitioners_blueprint = Blueprint(
    "practitioners", __name__, url_prefix="/practitioners"
)


class PractitionerController:
    def __init__(self, resource_client=None, auth=auth):
        self.resource_client = resource_client or ResourceClient()
        self.auth = auth

    def get_practitioner_slots(
        self, practitioner_id: str, start: str, end: str, status: str
    ) -> Practitioner:
        """Returns list of slots of a practitioner with the given time range

        :param practitioner_id: id of practitioner
        :type practitioner_id: str
        :param start: start time of the search of slots and schedule. Use iso date format
        :type start: str
        :param end: end time of the search of slots and schedule. Use iso date format
        :type end: str
        :param status: free or busy
        :type status: str

        :rtype: Practitioner
        """

        print("search schedule")
        schedule_search = self.resource_client.search(
            "Schedule",
            search=[
                ("actor", practitioner_id),
                ("active", str(True)),  # always find active schedule only
                ("date", "ge" + start),
                ("date", "le" + end),
            ],
        )

        if schedule_search.entry is None:
            return {"data": []}

        # assumes we only have one active schedule at the period
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
        return slot_search.entry

    def create_practitioner(self, uid: str, data):
        """Returns the details of a doctor created.
        This creates a practitioner in FHIR, as well as create a custom claims with it
        Note that this function should only be called
        from the frontend client since everything assumes to use Firebase for
        authentication/authorization.
        Currently there is no check for duplicate entry or retryable, all assuming
        that the operations here succeeded without failure.

        :param uid: id of practitioner associated to Firebase
        :type uid: str
        :param data: FHIR data for practitioner
        :type data: JSON

        :rtype: dict
        """
        practitioner_data = Practitioner.parse_obj(data)
        practitioner = self.resource_client.create_resource(practitioner_data)

        if practitioner:
            # Then grant the custom claim for the caller in Firebase
            custom_claims = {}
            custom_claims["role"] = "Practitioner"
            custom_claims["role_id"] = practitioner.id
            self.auth.set_custom_user_claims(uid, custom_claims)
        return practitioner


@practitioners_blueprint.route("/<practitioner_id>/slots", methods=["GET"])
@jwt_authenticated()
def get_practitioner_slots(practitioner_id: str) -> dict:

    nine_am = get_today_time(9)
    six_pm = get_today_time(18)
    start = request.args.get("start", nine_am.isoformat())
    end = request.args.get("end", six_pm.isoformat())
    status = request.args.get("status", "free")
    slots = PractitionerController().get_practitioner_slots(
        practitioner_id, start, end, status
    )
    if slots is None:
        return {"data": []}
    return {"data": [e.resource.dict() for e in slots]}


@practitioners_blueprint.route("/", methods=["POST"])
@jwt_authenticated()
def create_practitioner():
    if not is_email_verified(request) or not is_email_in_allowed_list(request):
        return Response(status=401, response="Not authorized correctly")

    result = PractitionerController().create_practitioner(
        request.claims["uid"], request.get_json()
    )

    if result is None:
        return Response(status=401, response="No Response")

    return result.dict(), 202


def get_today_time(hours: int):
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    today_min = datetime.combine(datetime.now(), time.min)
    today_min = tokyo_timezone.localize(today_min)
    return today_min + timedelta(hours=hours)
