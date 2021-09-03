import json

from fhir.resources import construct_fhir_element
from fhir.resources.domainresource import DomainResource

from blueprints.encounters import EncountersController


class MockEncounterClient:
    def __init__(self):
        self.data = {
            "id": "123",
            "resourceType": "Encounter",
            "status": "planned",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "ambulatory",
            },
        }

    def get_resource(self, id: str, resource_type: str) -> DomainResource:
        return construct_fhir_element(resource_type, json.dumps(self.data))

    def patch_resource(self, id: str, resource_type: str, data: dict):
        self.data = {
            "id": "123",
            "resourceType": "Encounter",
            "status": data[0]["value"],
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "ambulatory",
            },
        }

        return construct_fhir_element(resource_type, self.data)


def test_update_encounter_status_not_in_list(firebase_auth):
    mock_resource = MockEncounterClient()
    encounter_controller = EncountersController(mock_resource, firebase_auth)
    response = encounter_controller.update_encounter("id1", "arriveds")
    assert response.status_code == 401
    assert mock_resource.get_resource("id1", "Encounter").status == "planned"


def test_update_encounter_status_in_list(firebase_auth):
    mock_resource = MockEncounterClient()
    encounter_controller = EncountersController(mock_resource, firebase_auth)
    response = encounter_controller.update_encounter("id1", "arrived")
    assert response.status_code == 202
    assert mock_resource.get_resource("id1", "Encounter").status == "arrived"
