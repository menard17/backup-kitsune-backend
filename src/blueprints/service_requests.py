import json

from flask import Blueprint, Response

from adapters.fhir_store import ResourceClient
from json_serialize import json_serial
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


class ServiceRequestController:
    def __init__(self, resource_client=None):
        self.resource_client = resource_client or ResourceClient()

    def get_service_requests(self, patient_id: str = None, encounter_id: str = None):
        search_clause = []
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
