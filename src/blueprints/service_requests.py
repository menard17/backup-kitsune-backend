import json

from flask import Blueprint, Response, request

from adapters.fhir_store import ResourceClient
from json_serialize import json_serial
from services.service_request_service import ServiceRequestService
from utils.datetime_encoder import datetime_encoder
from utils.middleware import jwt_authenticated, jwt_authorized

service_requests_blueprint = Blueprint(
    "service_requests", __name__, url_prefix="/service_requests"
)


@service_requests_blueprint.route("/<service_request_id>", methods=["GET"])
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def get_service_request(service_request_id: str) -> dict:
    return ServiceRequestController().get_service_request(service_request_id)


@service_requests_blueprint.route("/", methods=["GET"])
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def get_service_requests() -> dict:
    patient_id = request.args.get("patient_id")
    encounter_id = request.args.get("encounter_id")
    return ServiceRequestController().get_service_requests(
        patient_id=patient_id, encounter_id=encounter_id
    )


@service_requests_blueprint.route("/", methods=["POST"])
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def create_service_request() -> dict:
    return ServiceRequestController().create_service_request()


class ServiceRequestController:
    def __init__(self, resource_client=None, service_request_service=None):
        self.resource_client = resource_client or ResourceClient()
        self.service_request_service = service_request_service or ServiceRequestService(
            self.resource_client
        )

    def get_service_requests(self, patient_id: str = None, encounter_id: str = None):
        search_clause = [("status", "active,completed")]
        if patient_id:
            search_clause.append(("patient", patient_id))
        if encounter_id:
            search_clause.append(("encounter", encounter_id))

        service_request_search = self.resource_client.search(
            "ServiceRequest", search=search_clause
        )

        if service_request_search is None or service_request_search.entry is None:
            return Response(
                status=200, response=json.dumps({"data": []}, default=json_serial)
            )
        return Response(
            status=200,
            response=json.dumps(
                {
                    "data": [
                        datetime_encoder(e.resource.dict())
                        for e in service_request_search.entry
                    ]
                },
                default=json_serial,
            ),
        )

    def get_service_request(self, service_request_id: str):
        service_request = self.resource_client.get_resource(
            service_request_id, "ServiceRequest"
        )
        return Response(
            status=200,
            response=json.dumps({"data": [datetime_encoder(service_request.dict())]}),
        )

    def create_service_request(self):
        request_body = request.get_json()

        REQUIRED_FIELDS = ["patient_id", "encounter_id"]
        for field in REQUIRED_FIELDS:
            if request_body.get(field) is None:
                error_msg = f"{field} is missing in the request body"
                return Response(status=400, response=error_msg)

        patient_id = request_body.get("patient_id")
        requester_id = request_body.get("requester_id")
        encounter_id = request_body.get("encounter_id")
        service_request = request_body.get("service_request")
        request_display = request_body.get("request_display")
        status = request_body.get("status")
        priority = request_body.get("priority")

        if status and status not in ["active", "completed"]:
            return Response(status=400, response=f"status, {status} is not supported")

        if priority and priority not in ["routine", "urgent", "asap", "stat"]:
            return Response(
                status=400, response=f"priority, {priority} is not supported"
            )

        # change status of previously existing service request to "revoked"
        search_list = [("encounter", encounter_id)]
        service_request_search = self.resource_client.search(
            "ServiceRequest", search=search_list
        )
        if service_request_search.entry:
            for e in service_request_search.entry:
                self.resource_client.patch_resource(
                    e.resource.id,
                    "ServiceRequest",
                    [{"op": "add", "path": "/status", "value": "revoked"}],
                )

        # create new service requests
        err, resp = self.service_request_service.create_service_request(
            patient_id=patient_id,
            requester_id=requester_id,
            encounter_id=encounter_id,
            service_request=service_request,
            request_display=request_display,
            status=status,
            priority=priority,
        )

        if err is not None:
            return Response(status=400, response=err.args[0])
        return Response(status=201, response=resp.json())
