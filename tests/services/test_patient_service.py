import json

from fhir.resources import construct_fhir_element
from fhir.resources.domainresource import DomainResource

from services.patient_service import PatientService, remove_empty_string_from_address


class MockPatientClient:
    def __init__(self, mocker=None, email=None, second_email=None):
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

        if second_email:
            # Insert old email at index 0 and index 2
            self.data["telecom"].insert(
                0, {"system": "email", "use": "old", "value": second_email}
            )
            self.data["telecom"].append(
                {"system": "email", "use": "old", "value": second_email}
            )

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


def test_remove_empty_string_from_address_contains_empty_string():
    # Given
    addresses = [{"line": ["", "line2"], "country": "JP"}]
    expected_output = [{"line": ["line2"], "country": "JP"}]

    # When
    actual_addresses = remove_empty_string_from_address(addresses)

    # Then
    assert expected_output == actual_addresses

    # Check if original address list is not modified
    assert addresses == [{"line": ["", "line2"], "country": "JP"}]


def test_remove_empty_string_from_address_contains_without_empty_string():
    # Given
    addresses = [{"line": ["abc", "def"]}]
    expected_output = [{"line": ["abc", "def"]}]

    # When
    actual_addresses = remove_empty_string_from_address(addresses)

    # Then
    assert expected_output == actual_addresses


def test_remove_empty_string_from_address_contains_with_no_item():
    # Given
    addresses = [{"line": []}]
    expected_output = [{"line": []}]

    # When
    actual_addresses = remove_empty_string_from_address(addresses)

    # Then
    assert expected_output == actual_addresses


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


def test_get_patient_multiple_emails():
    # Given
    new_email = "new@umed.jp"
    old_email = "old@umed.jp"
    mock_resource_client = MockPatientClient(email=new_email, second_email=old_email)
    patient_service = PatientService(mock_resource_client)

    # When
    _, actual_email = patient_service.get_patient_email("1")

    # Then
    assert new_email == actual_email
