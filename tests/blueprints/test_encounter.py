import json

from fhir.resources import construct_fhir_element
from fhir.resources.domainresource import DomainResource

from blueprints.encounters import EncountersController


class MockEncounterClient:
    def __init__(self, mocker=None):
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

        self.mocker = mocker

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

    def search(self, resource_type: str, search: list) -> DomainResource:
        self.mocker.entry = None
        return self.mocker


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
    assert response.status_code == 200
    assert mock_resource.get_resource("id1", "Encounter").status == "arrived"


def test_no_encounters_from_search(firebase_auth, mocker):
    mock = mocker.Mock()
    mock_resource = MockEncounterClient(mock)
    encounter_controller = EncountersController(mock_resource, firebase_auth)
    response = encounter_controller.get_encounters("id1")
    assert response.status_code == 200
    assert json.loads(response.data) == {"data": []}


def test_no_encounter_from_search(firebase_auth, mocker):
    mock = mocker.Mock()
    mock_resource = MockEncounterClient(mock)
    encounter_controller = EncountersController(mock_resource, firebase_auth)
    response = encounter_controller.get_encounter("patientId", "encounterId")
    assert response.status_code == 200
    assert json.loads(response.data) == {"data": []}
