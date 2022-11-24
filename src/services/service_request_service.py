from fhir.resources import construct_fhir_element
from fhir.resources.domainresource import DomainResource

from adapters.fhir_store import ResourceClient
from utils.system_code import SystemCode

SERVICE_REQUEST = "ServiceRequest"


class ServiceRequestService:
    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def create_service_request(
        self,
        patient_id: str,
        requester_id: str,
        encounter_id: str,
        service_request: str,
        request_display: str,
        service_request_uuid: str = None,
        performer_id: str = None,
        status: str = "active",
        priority: str = "routine",
    ):
        service_request_jsondict = {
            "resourceType": "ServiceRequest",
            "status": status,
            "intent": "order",
            "code": {
                "coding": [
                    SystemCode.service_request_code(service_request, request_display)
                ],
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "requester": {"reference": f"PractitionerRole/{requester_id}"},
            "encounter": {"reference": f"Encounter/{encounter_id}"},
            "priority": priority,
        }

        if performer_id:
            service_request_jsondict["performer"] = [{"reference": performer_id}]

        request_service = construct_fhir_element(
            "ServiceRequest", service_request_jsondict
        )
        if service_request_uuid:
            result = self.resource_client.get_post_bundle(
                request_service, service_request_uuid
            )
        else:
            result = self.resource_client.create_resource(request_service)
        return None, result

    @staticmethod
    def get_service_request(service_request: DomainResource) -> list:
        output = []
        for request in service_request.code.coding:
            if request.system == SERVICE_REQUEST:
                output.append(
                    {
                        "display": request.display,
                        "value": request.code,
                        "verified": "false",
                    }
                )
        return output
