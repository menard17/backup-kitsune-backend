import json
import uuid
from datetime import datetime, time, timedelta

import pytz
from fhir.resources.practitioner import Practitioner
from flask import Blueprint, Response, request

from adapters.fhir_store import ResourceClient
from json_serialize import json_serial
from services.practitioner_role_service import PractitionerRoleService
from utils import role_auth
from utils.datetime_encoder import datetime_encoder
from utils.email_verification import is_email_in_allowed_list, is_email_verified
from utils.middleware import jwt_authenticated

practitioners_blueprint = Blueprint(
    "practitioners", __name__, url_prefix="/practitioners"
)


class PractitionerController:
    def __init__(self, resource_client=None, practitioner_role_service=None):
        self.resource_client = resource_client or ResourceClient()
        self.practitioner_role_service = (
            practitioner_role_service or PractitionerRoleService(self.resource_client)
        )

    def search_practitioners(self, request) -> Response:
        search_clause = []
        search_clause.append(("_summary", "data"))

        if email := request.args.get("email"):
            search_clause.append(("email", email))
        else:
            search_clause.append(("active", str(True)))

        if role_type := request.args.get("role_type"):
            (
                err,
                practitioner_id,
            ) = self.practitioner_role_service.get_practitioner_ids(role_type)
            if err is not None:
                return Response(status=400, response=err.args[0])

            if not practitioner_id:
                return Response(
                    status=200, response=json.dumps({"data": []}, default=json_serial)
                )

            search_clause.append(("_id", ",".join(practitioner_id)))

        result = self.resource_client.search(
            "Practitioner",
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

        :rtype: Practitioner(DomainResource)
        """
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

    def create_practitioner(self, request) -> Practitioner:
        """Returns the details of a doctor created.
        This creates a practitioner in FHIR, as well as create a custom claims with it
        Note that this function should only be called
        from the frontend client since everything assumes to use Firebase for
        authentication/authorization.
        Currently there is no check for duplicate entry or retryable, all assuming
        that the operations here succeeded without failure.

        :param request: the request for this operation

        :rtype: Practitioner(DomainResource)
        """
        practitioner = Practitioner.parse_obj(request.get_json())
        practitioner = self.resource_client.create_resource(practitioner)

        if practitioner:
            # Then grant the custom claim for the caller in Firebase
            role_auth.grant_role(request.claims, "Practitioner", practitioner.id)

        return practitioner

    def get_practitioner(self, practitioner_id: uuid) -> Response:
        """Returns practitioner with given practitioner_id

        :param practitioner_id: practitioner id
        :type practitioner_id: uuid
        :return: practitioner in JSON object
        :rtype: Response
        """
        role = self.resource_client.get_resource(practitioner_id, "Practitioner")
        return Response(status=200, response=datetime_encoder(role.json()))


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
        return {"data": []}, 200
    return {"data": [datetime_encoder(e.resource.dict()) for e in slots]}, 200


@practitioners_blueprint.route("/", methods=["POST"])
@jwt_authenticated()
def create_practitioner():
    if not is_email_verified(request) or not is_email_in_allowed_list(request):
        return Response(status=401, response="Not authorized correctly")

    result = PractitionerController().create_practitioner(request)

    if result is None:
        return Response(status=500, response="No Response")

    return result.dict(), 201


def get_today_time(hours: int):
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    today_min = datetime.combine(datetime.now(), time.min)
    today_min = tokyo_timezone.localize(today_min)
    return today_min + timedelta(hours=hours)


@practitioners_blueprint.route("/", methods=["GET"])
@jwt_authenticated()
def search():
    """
    Sample request body:
    {
        'email': 'example@umed.jp',
        'role_type': 'doctor',
    }
    """
    return PractitionerController().search_practitioners(request)


@practitioners_blueprint.route("/<practitioner_id>", methods=["GET"])
@jwt_authenticated()
def get_practitioner(practitioner_id: str):
    return PractitionerController().get_practitioner(practitioner_id)
