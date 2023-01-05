"""
See the design doc and use cases for APIs here:
https://www.notion.so/umed-group/Line-Up-Patient-Backend-Design-c45d8d26f6594dcbb4cb269d6cc405c5
"""
import json
from datetime import datetime

import pytz
from fhir.resources import construct_fhir_element
from flask import Blueprint
from flask.wrappers import Response

from adapters.fhir_store import ResourceClient
from utils.datetime_encoder import datetime_encoder
from utils.middleware import jwt_authenticated, jwt_authorized

lists_blueprint = Blueprint("lists", __name__, url_prefix="/lists")


@lists_blueprint.route("/", methods=["POST"])
@jwt_authenticated()
@jwt_authorized("/Admin/*")
def create_list() -> Response:
    """
    This creates an empty List.
    The list has an `entry` field and an array of references to patients.
    The list represents the patient queue.
    """
    return ListsController().create()


@lists_blueprint.route("/", methods=["GET"])
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def get_lists() -> Response:
    """
    This gets all of the lists.
    """
    return ListsController().get_lists()


@lists_blueprint.route("/<list_id>/counts", methods=["GET"])
@jwt_authenticated()
def get_number_of_item_in_list(list_id: str) -> Response:
    """
    This gets numer of item in the specific list.
    """
    return ListsController().get_list_len(list_id)


@lists_blueprint.route("/<list_id>", methods=["GET"])
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def get_a_list(list_id: str) -> Response:
    """
    This gets the data of a specific list.
    """
    return ListsController().get_a_list(list_id)


@lists_blueprint.route("/<list_id>/items/<patient_id>", methods=["POST"])
@jwt_authenticated()
@jwt_authorized("/Patient/{patient_id}")
def create_entry(list_id: str, patient_id: str) -> Response:
    """
    This creates an entry to the list. The entry will be put at the end of the list.
    This is for a patient to enter the queue.
    """
    return ListsController().create_entry(list_id, patient_id)


@lists_blueprint.route("/<list_id>/items/<patient_id>", methods=["DELETE"])
@jwt_authenticated()
@jwt_authorized("/Patient/{patient_id}")
def delete_entry(list_id: str, patient_id: str) -> Response:
    """
    This deletes an entry from the FHIR list.
    If the patient wants to drop off,
    the patient can call this API to remove itself from the queue.
    """
    return ListsController().delete_entry(list_id, patient_id)


@lists_blueprint.route("/<list_id>/appointments", methods=["GET"])
@jwt_authenticated()
def get_spot_details(list_id: str) -> Response:
    return ListsController().get_spot_details(list_id)


class ListsController:
    def __init__(self, resource_client=None):
        self.resource_client = resource_client or ResourceClient()

    def create(self) -> Response:
        empty_list = {
            "resourceType": "List",
            "id": "example-empty",
            "status": "current",
            "mode": "working",
            "title": "Patient Queue",
        }
        fhir_list = construct_fhir_element("List", empty_list)
        fhir_list = self.resource_client.create_resource(fhir_list)
        return Response(
            status=201,
            response=json.dumps(datetime_encoder(fhir_list.dict())),
        )

    def get_lists(self) -> Response:
        lists = self.resource_client.get_resources("List")
        return Response(
            status=200, response=json.dumps({"data": datetime_encoder(lists.dict())})
        )

    def get_a_list(self, list_id: str) -> Response:
        fhir_list = self.resource_client.get_resource(list_id, "List")
        return Response(
            status=200,
            response=json.dumps({"data": datetime_encoder(fhir_list.dict())}),
        )

    def get_list_len(self, list_id: str) -> Response:
        fhir_list = self.resource_client.get_resource(list_id, "List")
        count = 0 if fhir_list.entry is None else len(fhir_list.entry)
        return Response(
            status=200,
            response=json.dumps({"data": count}),
        )

    def get_spot_details(self, list_id: str) -> Response:
        fhir_list = self.resource_client.get_resource(list_id, "List")
        count = 0 if fhir_list.entry is None else len(fhir_list.entry)
        jst = pytz.timezone("Asia/Tokyo")
        today = datetime.now().astimezone(jst)

        search_clause = [
            ("active", "true"),
            ("role", "walk-in"),
            ("date", "lt" + today.date().isoformat()),
            ("date", "gt" + today.date().isoformat()),
        ]

        result = self.resource_client.search(
            "PractitionerRole",
            search=search_clause,
        )

        if result.entry is None:
            return Response(status=200, response={"error": "No available doctors"})

        duration = 420  # Expect each appointment to take 420 secs(7 mins)
        weekday = convert_day_of_week_to_str(today.weekday())
        spot_counts = (
            get_spot_counts(duration, weekday, today.time(), result.entry) - count
        )

        resp = json.dumps(
            {
                "available_spot": spot_counts,
                "time": today.isoformat(),
                "list_id": list_id,
            }
        )
        return Response(status=200, response=resp)

    def create_entry(self, list_id: str, patient_id: str) -> Response:
        # get the list data
        fhir_list = self.resource_client.get_resource(list_id, "List")
        if fhir_list.entry is None:
            fhir_list.entry = []

        # validate that the patient is not already in the queue
        for e in fhir_list.entry:
            if e.item.reference.split("/")[1] == patient_id:
                return Response(status=400, response="Patient already in the list")

        # update the entry with the patient, use optimistic lock to avoid concurrency update.
        fhir_list.entry.append({"item": {"reference": f"Patient/{patient_id}"}})
        lock_header = self.resource_client.last_seen_etag
        fhir_list = self.resource_client.put_resource(
            fhir_list.id, fhir_list, lock_header
        )
        return Response(
            status=201,
            response=json.dumps({"data": datetime_encoder(fhir_list.dict())}),
        )

    def delete_entry(self, list_id: str, patient_id: str) -> Response:
        # get the list data
        fhir_list = self.resource_client.get_resource(list_id, "List")

        # validate that the patient is already in the queue
        patient_list_idx = -1
        for idx, e in enumerate(fhir_list.entry):
            if e.item.reference.split("/")[1] == patient_id:
                patient_list_idx = idx
        if patient_list_idx == -1:
            return Response(status=400, response="Patient not in the list")

        # remove the item of the patient from the entry
        entry = fhir_list.entry
        fhir_list.entry = entry[:patient_list_idx] + entry[patient_list_idx + 1 :]

        # update the entry with the removal of the patient
        lock_header = self.resource_client.last_seen_etag
        fhir_list = self.resource_client.put_resource(
            fhir_list.id, fhir_list, lock_header
        )

        return Response(
            status=200,
            response=json.dumps({"data": datetime_encoder(fhir_list.dict())}),
        )


def get_spot_counts(
    duration: int, day: str, time: datetime.time, bundle_entries: list
) -> int:
    """
    One spot is defined as expected space for 1 appointment for 1 doctor.
    If there are 6 spots, it means you are expected to have 6 appointments by 1 doctor or 3 appointments by 2 doctors.
    The spot is different from slot as slot is not dynamic
    but spot is used to forcast how many appointments can be created in the future.
    This is abtract concept and not FHIR concept.

    :param duration: length of expected appointment time in seconds
    :type duration: int
    :param day: day of the week from mon to sun. Consistent with FHIR format of day.
    :type day: str
    :param time: base time to calculate number of spots
    :type time: datetime.time
    :param bundle_entries: list of outputs from search of practitioner role
    :type bundle_entries: list

    :rtype: int
    """
    sums = 0
    for bundle in bundle_entries:
        available_times = bundle.resource.availableTime
        for available_time in available_times:
            if day in available_time.daysOfWeek:
                start = available_time.availableStartTime
                end = available_time.availableEndTime
                if time > start and time < end:
                    sums += (
                        (
                            _convert_time_to_datetime(end)
                            - _convert_time_to_datetime(time)
                        ).total_seconds()
                    ) // duration
    return int(sums)


def _convert_time_to_datetime(time: datetime.time) -> datetime:
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    return datetime(now.year, now.month, now.day, time.hour, time.minute, time.second)


def convert_day_of_week_to_str(day: int) -> str:
    day_dict = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}
    return day_dict[day]
