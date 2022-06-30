import json
from unittest.mock import patch

import pytest
from fhir.resources.bundle import Bundle
from fhir.resources.patient import Patient

from blueprints.patients import PatientController


def test_get_patient(mocker, resource_client, test_patient_data):
    mocker.patch.object(resource_client, "get_resource", return_value=test_patient_data)
    controller = PatientController(resource_client)

    result = controller.get_patient("test-patient-id")

    assert json.loads(result.data)["data"] == test_patient_data
    resource_client.get_resource.assert_called_once_with("test-patient-id", "Patient")


def test_get_patients(mocker, resource_client, test_bundle_data):
    mocker.patch.object(resource_client, "get_resources", return_value=test_bundle_data)
    controller = PatientController(resource_client)

    request = FakeRequest()
    result = controller.get_patients(request)

    assert json.loads(result.data)["data"] == test_bundle_data
    resource_client.get_resources.assert_called_once_with("Patient", 300)


def test_link(mocker, resource_client, test_bundle_data):
    mocker.patch.object(resource_client, "link", return_value=test_bundle_data)
    controller = PatientController(resource_client)

    next_link = "https://my.fhir.link/Patient/?_count=1&_page_token=Cjj3YqaT4f%2F%2F%2F%2F%2BABeFKRf0xQQD%2FAf%2F%2BNTk0ZjgxODM1MjM2ZGM1M2IyZTMwNTUxNTUwMWFjODQAARABIZRNcFwxQ70GOQAAAAAebFmdSAFQAFoLCSzWOfWKBujqEANgxd%2BBywc%3D"  # noqa: E501
    result = controller.link(next_link)

    assert json.loads(result.data)["data"] == test_bundle_data
    resource_client.link.assert_called_once_with(next_link)


def test_link_should_fail_if_check_link_failed(
    mocker, resource_client, test_bundle_data
):
    mocker.patch.object(resource_client, "link", return_value=test_bundle_data)
    controller = PatientController(resource_client)

    next_link = "https://my.fhir.link/NotPatient/?_count=1&_page_token=Cjj3YqaT4f%2F%2F%2F%2F%2BABeFKRf0xQQD%2FAf%2F%2BNTk0ZjgxODM1MjM2ZGM1M2IyZTMwNTUxNTUwMWFjODQAARABIZRNcFwxQ70GOQAAAAAebFmdSAFQAFoLCSzWOfWKBujqEANgxd%2BBywc%3D"  # noqa: E501
    result = controller.link(next_link)

    assert result.status_code == 400


def test_create_patient_happy_path(mocker, resource_client, test_patient_data):
    patient_input = Patient()
    request = FakeRequest(
        data=patient_input, claims={"uid": "test-uid", "email_verified": True}
    )
    mocker.patch.object(
        resource_client, "create_resource", return_value=test_patient_data
    )
    with patch("blueprints.patients.role_auth") as mock_role_auth:
        controller = PatientController(resource_client)

        result = controller.create_patient(request)

        assert result == (test_patient_data, 201)
        resource_client.create_resource.assert_called_once_with(patient_input)
        mock_role_auth.grant_role.assert_called_once_with(
            {"uid": "test-uid", "email_verified": True}, "Patient", "test-patient-id"
        )


def test_create_patient_should_return_401_when_no_email_verified(
    mocker, resource_client, test_patient_data
):
    patient_input = Patient()
    request = FakeRequest(data=patient_input, claims={"uid": "test-uid"})
    mocker.patch.object(
        resource_client, "create_resource", return_value=test_patient_data
    )
    controller = PatientController(resource_client)

    result = controller.create_patient(request)

    assert result.status == "401 UNAUTHORIZED"


def test_create_patient_should_return_401_when_email_unverified(
    mocker, resource_client, test_patient_data
):
    patient_input = Patient()
    request = FakeRequest(
        data=patient_input, claims={"uid": "test-uid", "email_verified": False}
    )
    mocker.patch.object(
        resource_client, "create_resource", return_value=test_patient_data
    )
    controller = PatientController(resource_client)

    result = controller.create_patient(request)

    assert result.status == "401 UNAUTHORIZED"


def test_patch_patient(mocker, resource_client, test_patient_data):
    patient_input = Patient()
    request = FakeRequest(patient_input)
    mocker.patch.object(
        resource_client, "patch_resource", return_value=test_patient_data
    )
    controller = PatientController(resource_client)

    result = controller.patch_patient(request, "test-patient-id")

    assert result == (test_patient_data, 200)
    resource_client.patch_resource.assert_called_once_with(
        "test-patient-id", "Patient", patient_input
    )


class FakeRequest:
    def __init__(self, data={}, args={}, claims=None):
        self.data = data
        self.claims = claims
        self.args = args

    def get_json(self):
        return self.data

    def args(self):
        return self.args


@pytest.fixture
def resource_client(mocker):
    yield mocker.Mock()


@pytest.fixture
def test_patient_data():
    patient = Patient()
    patient.id = "test-patient-id"
    return patient


@pytest.fixture
def test_bundle_data():
    bundle = Bundle(type="document")
    bundle.id = "test-bundle-id"
    return bundle
