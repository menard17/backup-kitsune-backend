import pytz
import pytest

from datetime import datetime
from fhir.resources import construct_fhir_element
from fhir.resources.bundle import Bundle
from fhir.resources.patient import Patient
from blueprints.patients import Controller
from helper import MockResourceClient

SAMPLE_APPOINTMENT_SEARCH_DATA = {
    "entry": [
        {
            "fullUrl": "https://healthcare.googleapis.com/v1/projects/dummy-fhir-path",
            "resource": {
                "id": "e2c6f0cd-ec8a-4708-a64a-1c3c02c624a0",
                "meta": {
                    "lastUpdated": "2021-08-25T12:54:12.931026+00:00",
                    "versionId": "MTYyOTg5NjA1MjkzMTAyNjAwMA",
                },
                "description": "Booking practitioner role",
                "end": "2021-08-25T22:54:11.576661+09:00",
                "participant": [
                    {
                        "actor": {
                            "reference": "Patient/9e477534-b74a-4139-9338-90977e81bc34"
                        },
                        "required": "required",
                        "status": "accepted",
                    },
                    {
                        "actor": {
                            "reference": "PractitionerRole/2715eec2-abd2-4265-97db-a237db51a648"
                        },
                        "required": "required",
                        "status": "accepted",
                    },
                ],
                "serviceCategory": [
                    {
                        "coding": [
                            {
                                "code": "17",
                                "display": "General Practice",
                                "system": "http://hl7.org/fhir/valueset-service-category.html",
                            }
                        ]
                    }
                ],
                "serviceType": [
                    {
                        "coding": [
                            {
                                "code": "540",
                                "display": "Online Service",
                                "system": "http://hl7.org/fhir/valueset-service-type.html",
                            }
                        ]
                    }
                ],
                "slot": [{"reference": "Slot/bbba3c15-1c9d-47ef-8dda-e389651321d9"}],
                "start": "2021-08-25T21:54:11.576661+09:00",
                "status": "booked",
                "resourceType": "Appointment",
            },
            "search": {"mode": "match"},
        }
    ],
    "link": [
        {
            "relation": "search",
            "url": "https://healthcare.googleapis.com/v1/projects/dummy-fhir-path/Appointment/?actor=9e477534-b74a-4139-9338-90977e81bc34&date=ge2021-08-25",  # noqa: E501
        },
        {
            "relation": "first",
            "url": "https://healthcare.googleapis.com/v1/projects/dummy-fhir-path/fhirStores/phat-fhir-store-id/fhir/Appointment/?actor=9e477534-b74a-4139-9338-90977e81bc34&date=ge2021-08-25",  # noqa: E501
        },
        {
            "relation": "self",
            "url": "https://healthcare.googleapis.com/v1/projects/dummy-fhir-path/fhirStores/phat-fhir-store-id/fhir/Appointment/?actor=9e477534-b74a-4139-9338-90977e81bc34&date=ge2021-08-25",  # noqa: E501
        },
    ],
    "total": 1,
    "type": "searchset",
    "resourceType": "Bundle",
}


def test_list_appointment():
    patient_id = "dummy-patient-id"

    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    expected_search_date = now.date().isoformat()  # defaults to current date

    def mock_search(resource_type, search):
        assert resource_type == "Appointment"
        assert ("date", "ge" + expected_search_date) in search
        assert ("actor", patient_id) in search
        return construct_fhir_element("Bundle", SAMPLE_APPOINTMENT_SEARCH_DATA)

    resource_client = MockResourceClient()
    resource_client.search = mock_search

    request = FakeRequest({})
    controller = Controller(resource_client)
    controller.list_appointments(request, patient_id)


def test_list_appointment_with_date_provided():
    patient_id = "dummy-patient-id"
    expected_search_date = "2021-08-25"

    def mock_search(resource_type, search):
        assert resource_type == "Appointment"
        assert ("date", "ge" + expected_search_date) in search
        assert ("actor", patient_id) in search
        return construct_fhir_element("Bundle", SAMPLE_APPOINTMENT_SEARCH_DATA)

    resource_client = MockResourceClient()
    resource_client.search = mock_search

    request = FakeRequest(args={"date": expected_search_date})
    controller = Controller(resource_client)
    controller.list_appointments(request, patient_id)


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
    request = FakeRequest(
        data=patient_input, claims={"uid": "test-uid", "email_verified": True}
    )
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
    request = FakeRequest(data=patient_input, claims={"uid": "test-uid"})
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
    request = FakeRequest(
        data=patient_input, claims={"uid": "test-uid", "email_verified": False}
    )
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
