from fhir.resources import construct_fhir_element

from adapters.fhir_store import ResourceClient
from utils.system_code import SystemCode


class ServiceRequestService:
    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def create_service_request(
        self,
        service_request_uuid: str,
        patient_id: str,
        performer_id: str,
        requester_id: str,
        encounter_id: str,
    ):
        service_request_jsondict = {
            "resourceType": "ServiceRequest",
            "status": "active",
            "intent": "order",
            "code": {
                "coding": [SystemCode.service_request_code()],
            },
            "subject": {"reference": patient_id},
            "requester": {"reference": requester_id},
            "performer": [{"reference": performer_id}],
            "encounter": {"referencec": encounter_id},
        }

        request_service = construct_fhir_element(
            service_request_jsondict["resourceType"], service_request_jsondict
        )
        request_service = self.resource_client.get_post_bundle(
            request_service, service_request_uuid
        )
        return None, request_service
