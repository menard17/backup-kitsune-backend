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


def test_check_link_success():
    valid_link = "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/Patient/?_count=1&_page_token=Cjj3YqaT4f%2F%2F%2F%2F%2BABeFKRf0xQQD%2FAf%2F%2BNTk0ZjgxODM1MjM2ZGM1M2IyZTMwNTUxNTUwMWFjODQAARABIZRNcFwxQ70GOQAAAAAebFmdSAFQAFoLCSzWOfWKBujqEANgxd%2BBywc%3D"  # noqa: E501
    service = PatientService(None)

    ok, errResp = service.check_link(valid_link)

    assert ok
    assert errResp is None


def test_check_link_return_false_when_not_link_for_patient():
    appointment_link = "https://my.fhir.link/Appointment?_count=1&actor=87c802f0-c486-438d-b2e9-e06543303b4c&date=ge2022-05-21&_page_token=Cjj3YokQdv%2F%2F%2F%2F%2BABd%2BH721RFgD%2FAf%2F%2BNWM4NDM2YmQ3ZWExOTZiYTE5NzAyMDQ4Njc4NjMyOWUAARABIZRNcFwxQ70GOQAAAACJ73adSAFQAFoLCbs%2BeLJbiDrKEANg2qiOZGgB"  # noqa: E501
    service = PatientService(None)

    ok, errResp = service.check_link(appointment_link)

    assert not ok
    assert errResp.status_code == 400
    assert errResp.data == b"not link for patient"
