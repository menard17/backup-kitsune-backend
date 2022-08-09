from fhir.resources import construct_fhir_element

from adapters.fhir_store import ResourceClient


class MedicationRequestService:
    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def create_medication_request(
        self,
        patient_id: str,
        requester_id: str,
        encounter_id: str,
        medications: list,
        status: str = "active",
        priority: str = "routine",
    ):
        modified_medications = []
        for index in range(len(medications)):
            modified_medications.append(
                {
                    "system": "register",
                    "code": medications[index]["code"],
                    "display": medications[index]["display"],
                }
            )

        medication_request_jsondict = {
            "resourceType": "MedicationRequest",
            "status": status,
            "intent": "order",
            "subject": {"reference": f"Patient/{patient_id}"},
            "requester": {"reference": f"PractitionerRole/{requester_id}"},
            "encounter": {"reference": f"Encounter/{encounter_id}"},
            "priority": priority,
            "medicationCodeableConcept": {"coding": medications},
        }

        medication_request = construct_fhir_element(
            "MedicationRequest", medication_request_jsondict
        )
        result = self.resource_client.get_post_bundle(medication_request)
        return None, result
