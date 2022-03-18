import json

from fhir.resources import construct_fhir_element
from fhir.resources.domainresource import DomainResource

from services.patient_service import PatientService


class MockPatientClient:
    def __init__(self, mocker=None, email=None):
        self.data = {
            "resourceType": "Patient",
            "id": "example",
            "active": True,
            "name": [
                {"use": "official", "family": "Chalmers", "given": ["Peter", "James"]}
            ],
            "gender": "male",
            "birthDate": "1990-01-01",
        }

        if email:
            self.data["telecom"] = [
                {"system": "email", "use": "home", "value": email},
            ]

        self.mocker = mocker

    def get_resource(self, id: str, resource_type: str) -> DomainResource:
        return construct_fhir_element(resource_type, json.dumps(self.data))


def test_get_patient_email_normal():
    # Given
    expected_email = "example@umed.jp"
    mock_resource_client = MockPatientClient(email=expected_email)
    patient_service = PatientService(mock_resource_client)

    # When
    _, actual_email = patient_service.get_patient_email("1")

    # Then
    assert expected_email == actual_email


def test_get_patient_email_not_exist():
    # Given
    mock_resource_client = MockPatientClient()
    patient_service = PatientService(mock_resource_client)

    # When
    _, actual_email = patient_service.get_patient_email("1")

    # Then
    assert not actual_email


def test_get_patient_name_normal():
    # Given
    expected_name = {
        "use": "official",
        "family": "Chalmers",
        "given": ["Peter", "James"],
    }
    mock_resource_client = MockPatientClient()
    patient_service = PatientService(mock_resource_client)

    # When
    _, actual_name = patient_service.get_patient_name("1")

    # Then
    assert expected_name == actual_name
