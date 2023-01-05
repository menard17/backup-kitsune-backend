"""
See the design doc and use cases for APIs here:
https://www.notion.so/umed-group/Line-Up-Patient-Backend-Design-c45d8d26f6594dcbb4cb269d6cc405c5
"""
import json

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
        print(fhir_list)
        count = 0 if fhir_list.entry is None else len(fhir_list.entry)
        return Response(
            status=200,
            response=json.dumps({"data": count}),
        )

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
