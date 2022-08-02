import json
import uuid

from flask import Blueprint, request
from flask.wrappers import Response

from adapters.fhir_store import ResourceClient
from json_serialize import json_serial
from services.account_service import AccountService
from services.encounter_service import EncounterService
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
    return EncountersController().create_encounter()


class EncountersController:
    def __init__(
        self, resource_client=None, account_service=None, encounter_service=None
    ):
        self.resource_client = resource_client or ResourceClient()
        self.account_service = account_service or AccountService(self.resource_client)
        self.encounter_service = encounter_service or EncounterService(
            self.resource_client
        )

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

        if encounter_search.total == 0:
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
        Helper function to return resources based on search clauses

        :param search_clause: search parameters
        :type search_clause: list(tuple(str, str))

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
            search_list.append(("_revinclude", "DiagnosticReport:encounter"))
        return self._search_encounters(search_list)

    def create_encounter(self) -> Response:
        """Returns the details of a encounter created.

        This creates an account and an encounter in FHIR, as well as create a custom claims with
        Note that this function should only be called
        from the frontend client(by patient) since everything assumes to use Firebase for
        authentication/authorization. Diagnosis should be created after encounter is created.

        The account and the encounter are created in transactionally meaning
        both will be either created or not created.

        Only one encounter can be created per appointment

        When encounter is created, appointment status is updated to fulfilled automaticaclly.

        Body should contain appointment, practitionerRole, and patient

        Sample Json body
        {
            'appointment_id': '0d49bb25-97f7-4f6d-8459-2b6a18d4d1'
            'patient_id': '0d49bb25-97f7-4f6d-8459-2b6a18d4d2',
            'role_id': '0d49bb25-97f7-4f6d-8459-2b6a18d4d3'
        }

        :rtype: Response
        """
        request_body = request.get_json()
        if (appointment_id := request_body.get("appointment_id")) is None:
            return Response(
                status=400,
                response="missing param: appointment_id",
            )
        if (patient_id := request_body.get("patient_id")) is None:
            return Response(
                status=400,
                response="missing param: patient_id",
            )
        if (role_id := request_body.get("role_id")) is None:
            return Response(
                status=400,
                response="missing param: role_id",
            )
        # Check if encounter already exists
        search_list = [("appointment", appointment_id)]
        encounter_search = self.resource_client.search("Encounter", search=search_list)

        if encounter_search.total == 0:
            resources = []
            account_id = f"urn:uuid:{uuid.uuid1()}"

            # Create account bundle
            err, account = self.account_service.create_account_bundle(
                patient_id, account_id
            )
            if err is not None:
                return Response(status=400, response=err.args[0])
            resources.append(account)

            # Create encounter bundle
            err, encounter = self.encounter_service.create_encounter(
                appointment_id, role_id, patient_id, account_id
            )
            if err is not None:
                return Response(status=400, response=err.args[0])
            resources.append(encounter)

            resp = self.resource_client.create_resources(resources)
            account = next(
                filter(
                    lambda resources: resources.resource.resource_type == "Account",
                    resp.entry,
                )
            )
            encounter = next(
                filter(
                    lambda resources: resources.resource.resource_type == "Encounter",
                    resp.entry,
                )
            )

            # None check for account and encounter
            if account is not None and encounter is not None:
                account = account.resource
                encounter = encounter.resource
            else:
                return Response(
                    status=400, response="Account or Encounter is not created correctly"
                )

            # Appointment gets fulfilled
            for appointment in encounter.appointment:
                appointment_id = appointment.reference.split("/")[1]
                value = [{"op": "add", "path": "/status", "value": "fulfilled"}]
                appointment = self.resource_client.patch_resource(
                    appointment_id, "Appointment", value
                )

            return Response(
                status=201,
                response=json.dumps(
                    {
                        "data": [
                            json.loads(encounter.json()),
                            json.loads(appointment.json()),
                            json.loads(account.json()),
                        ]
                    },
                    default=json_serial,
                ),
            )
        return Response(status=400, response="Encounter was created before")

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

        return Response(status=200, response=new_encounter.json())
