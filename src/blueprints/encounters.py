import json

from fhir.resources.encounter import Encounter
from firebase_admin import auth
from flask import Blueprint, request
from flask.wrappers import Response

from adapters.fhir_store import ResourceClient
from json_serialize import json_serial
from utils.datetime_encoder import datetime_encoder
from utils.middleware import jwt_authenticated, jwt_authorized

encounters_blueprint = Blueprint("encounters", __name__, url_prefix="/patients")


@encounters_blueprint.route("/<patient_id>/encounters/<encounter_id>", methods=["GET"])
@jwt_authenticated()
@jwt_authorized("/Patient/{patient_id}")
def get_encounter(patient_id: str, encounter_id: str) -> Response:
    return EncountersController().get_encounter(patient_id, encounter_id)


@encounters_blueprint.route("/<patient_id>/encounters", methods=["GET"])
@jwt_authenticated()
@jwt_authorized("/Patient/{patient_id}")
def get_encounters(patient_id: str) -> Response:
    appointment_id = request.args.get("appointment_id")
    return EncountersController().get_encounters(patient_id, appointment_id)


@encounters_blueprint.route(
    "/<patient_id>/encounters/<encounter_id>", methods=["PATCH"]
)
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def update_status_encounter(patient_id: str, encounter_id: str) -> Response:
    status = request.args.get("status")
    return EncountersController().update_encounter(encounter_id, status)


@encounters_blueprint.route("/<patient_id>/encounters", methods=["POST"])
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def create_encounter(patient_id: str) -> Response:
    return EncountersController().create_encounter(request.get_json())


class EncountersController:
    def __init__(self, resource_client=None, firebase_auth=None):
        self.resource_client = resource_client or ResourceClient()
        self.firebase_auth = firebase_auth or auth

    def _search_encounters(self, search_clause) -> Response:
        """
        Helper function to return resources based on search clauses

        :param search_clause: search parameters
        :type search_clause: list(tuple(str, str))

        :rtype: Response
        """
        encounter_search = self.resource_client.search(
            "Encounter", search=search_clause
        )

        if encounter_search.entry is None:
            return Response(
                status=200, response=json.dumps({"data": []}, default=json_serial)
            )
        return Response(
            status=200,
            response=json.dumps(
                {
                    "data": [
                        datetime_encoder(e.resource.dict())
                        for e in encounter_search.entry
                    ]
                },
                default=json_serial,
            ),
        )

    def get_encounter(self, patient_id: str, encounter_id: str) -> Response:
        """
        Returns details of a encounter given patient_id

        :param patient_id: uuid for patient
        :type patient_id: str
        :param encounter_id: uuid for encounter
        :type encounter_id: str

        :rtype: Response
        """
        search_list = [("id", encounter_id), ("patient", patient_id)]
        return self._search_encounters(search_list)

    def get_encounters(self, patient_id: str, appointment_id: str = None) -> Response:
        """
        Returns details of all encounters.
        Access to this function should be limited.
        Have to get FHIR's UUID from UID bypass for test.

        Optionally resource can be fileted by appointment id

        :param patient_id: uuid for patient
        :type patient_id: str
        :param? appointment_id: uuid for appointment
        :type? appointment_id: str

        :rtype: Response
        """
        search_list = [("subject", patient_id)]
        if appointment_id:
            search_list.append(("appointment", appointment_id))
        return self._search_encounters(search_list)

    def create_encounter(self, data) -> Response:
        """Returns the details of a encounter created.

        This creates a encounter in FHIR, as well as create a custom claims with
        Note that this function should only be called
        from the frontend client(by patient) since everything assumes to use Firebase for
        authentication/authorization. Diagnosis should be created after encounter is created

        Body should contain appointment, practitionerRole, and patient

        :param data: FHIR data for practitioner
        :type data: JSON

        :rtype: Response
        """
        encounter = Encounter.parse_obj(data)
        encounter = self.resource_client.create_resource(encounter)

        return Response(status=200, response=encounter.json())

    def update_encounter(self, encounter_id: str, status: str) -> Response:
        status_set = set(
            [
                "planned",
                "arrived",
                "triaged",
                "in-progress",
                "onleave",
                "finished",
                "cancelled",
            ]
        )
        if status not in status_set:
            return Response(status=401, response="Wrong input")

        value = [{"op": "add", "path": "/status", "value": status}]

        new_encounter = self.resource_client.patch_resource(
            encounter_id, "Encounter", value
        )

        return Response(status=202, response=new_encounter.json())
