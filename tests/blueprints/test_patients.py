import pytest
from blueprints.patients import Controller
from fhir.resources.bundle import Bundle
from fhir.resources.patient import Patient


def test_get_patient(mocker, resource_client, firebase_auth, test_patient_data):
    mocker.patch.object(resource_client, "get_resource", return_value=test_patient_data)
    controller = Controller(resource_client, firebase_auth)

    result = controller.get_patient("test-patient-id")

    assert result == test_patient_data
    resource_client.get_resource.assert_called_once_with("test-patient-id", "Patient")


def test_get_patients(mocker, resource_client, firebase_auth, test_bundle_data):
    mocker.patch.object(resource_client, "get_resources", return_value=test_bundle_data)
    controller = Controller(resource_client, firebase_auth)

    result = controller.get_patients()

    assert result == test_bundle_data
    resource_client.get_resources.assert_called_once_with("Patient")


def test_create_patient_happy_path(
    mocker, resource_client, firebase_auth, test_patient_data
):
    patient_input = Patient()
    request = FakeRequest(patient_input, {"uid": "test-uid", "email_verified": True})
    mocker.patch.object(
        resource_client, "create_resource", return_value=test_patient_data
    )
    controller = Controller(resource_client, firebase_auth)

    result = controller.create_patient(request)

    assert result == (test_patient_data, 202)
    resource_client.create_resource.assert_called_once_with(patient_input)
    firebase_auth.set_custom_user_claims.assert_called_once_with(
        "test-uid", {"role": "Patient", "role_id": "test-patient-id"}
    )


def test_create_patient_should_return_401_when_no_email_verified(
    mocker, resource_client, firebase_auth, test_patient_data
):
    patient_input = Patient()
    request = FakeRequest(patient_input, {"uid": "test-uid"})
    mocker.patch.object(
        resource_client, "create_resource", return_value=test_patient_data
    )
    controller = Controller(resource_client, firebase_auth)

    result = controller.create_patient(request)

    assert result.status == "401 UNAUTHORIZED"


def test_create_patient_should_return_401_when_email_unverified(
    mocker, resource_client, firebase_auth, test_patient_data
):
    patient_input = Patient()
    request = FakeRequest(patient_input, {"uid": "test-uid", "email_verified": False})
    mocker.patch.object(
        resource_client, "create_resource", return_value=test_patient_data
    )
    controller = Controller(resource_client, firebase_auth)

    result = controller.create_patient(request)

    assert result.status == "401 UNAUTHORIZED"


def test_patch_patient(mocker, resource_client, firebase_auth, test_patient_data):
    patient_input = Patient()
    request = FakeRequest(patient_input)
    mocker.patch.object(
        resource_client, "patch_resource", return_value=test_patient_data
    )
    controller = Controller(resource_client, firebase_auth)

    result = controller.patch_patient(request, "test-patient-id")

    assert result == (test_patient_data, 202)
    resource_client.patch_resource.assert_called_once_with(
        "test-patient-id", "Patient", patient_input
    )


class FakeRequest:
    def __init__(self, data, claims=None):
        self.data = data
        self.claims = claims

    def get_json(self):
        return self.data


@pytest.fixture
def resource_client(mocker):
    yield mocker.Mock()


@pytest.fixture
def firebase_auth(mocker):
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
