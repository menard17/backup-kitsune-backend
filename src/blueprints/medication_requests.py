import json

from flask import Blueprint, Response, request

from adapters.fhir_store import ResourceClient
from json_serialize import json_serial
from services.medication_request_service import MedicationRequestService
from utils.datetime_encoder import datetime_encoder
from utils.middleware import jwt_authenticated, jwt_authorized

medication_requests_blueprint = Blueprint(
    "medication_requests", __name__, url_prefix="/medication_requests"
)


@medication_requests_blueprint.route("/", methods=["GET"])
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def get_service_requests() -> dict:
    patient_id = request.args.get("patient_id")
    encounter_id = request.args.get("encounter_id")
    return MedicationRequestController().get_medication_requests(
        patient_id=patient_id, encounter_id=encounter_id
    )


@medication_requests_blueprint.route("/", methods=["POST"])
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def create_medication_request() -> dict:
    return MedicationRequestController().create_medication_request()


class MedicationRequestController:
    def __init__(self, resource_client=None, medication_request_service=None):
        self.resource_client = resource_client or ResourceClient()
        self.medication_request_service = (
            medication_request_service or MedicationRequestService(self.resource_client)
        )

    def get_medication_requests(self, patient_id: str = None, encounter_id: str = None):
        search_clause = [("status", "active,completed")]
        if patient_id:
            search_clause.append(("patient", patient_id))
        if encounter_id:
            search_clause.append(("encounter", encounter_id))

        medication_request_search = self.resource_client.search(
            "MedicationRequest", search=search_clause
        )

        if medication_request_search is None or medication_request_search.entry is None:
            return Response(
                status=200, response=json.dumps({"data": []}, default=json_serial)
            )
        return Response(
            status=200,
            response=json.dumps(
                {
                    "data": [
                        datetime_encoder(e.resource.dict())
                        for e in medication_request_search.entry
                    ]
                },
                default=json_serial,
            ),
        )

    def create_medication_request(self):
        request_body = request.get_json()

        REQUIRED_FIELDS = ["patient_id", "encounter_id"]
        for field in REQUIRED_FIELDS:
            if request_body.get(field) is None:
                error_msg = f"{field} is missing in the request body"
                return Response(status=400, response=error_msg)

        patient_id = request_body.get("patient_id")
        requester_id = request_body.get("requester_id")
        encounter_id = request_body.get("encounter_id")
        status = request_body.get("status")
        priority = request_body.get("priority")
        medications = request_body.get("medications", [])

        if status and status not in ["active", "completed"]:
            return Response(status=400, response=f"status, {status} is not supported")

        if priority and priority not in ["routine", "urgent", "asap", "stat"]:
            return Response(
                status=400, response=f"priority, {priority} is not supported"
            )

        # change status of previously existing medication request to "cancelled"
        search_list = [("encounter", encounter_id)]
        medication_request_search = self.resource_client.search(
            "MedicationRequest", search=search_list
        )
        if medication_request_search.entry:
            for e in medication_request_search.entry:
                self.resource_client.patch_resource(
                    e.resource.id,
                    "MedicationRequest",
                    [{"op": "add", "path": "/status", "value": "cancelled"}],
                )

        # create new medication requests
        resources = []
        err, resp_bundle = self.medication_request_service.create_medication_request(
            patient_id=patient_id,
            requester_id=requester_id,
            encounter_id=encounter_id,
            medications=medications,
            status=status,
            priority=priority,
        )
        if err is not None:
            return Response(status=400, response=err)
        resources.append(resp_bundle)

        resource = self.resource_client.create_resources(resources)
        resp = json.dumps(
            [json.loads(datetime_encoder(e.resource.json())) for e in resource.entry],
            default=json_serial,
        )
        return Response(status=201, response=resp)
