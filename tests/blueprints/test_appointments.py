import json
from datetime import datetime

import pytz
from fhir.resources import construct_fhir_element
from fhir.resources.appointment import Appointment
from fhir.resources.slot import Slot
from helper import FakeRequest, MockResourceClient

from blueprints.appointments import AppointmentController

BOOKED_APPOINTMENT_DATA = {
    "resourceType": "Appointment",
    "status": "booked",
    "description": "Booking practitioner role",
    "start": "2021-08-15T13:55:57.967345+09:00",
    "end": "2021-08-15T14:55:57.967345+09:00",
    "serviceType": [
        {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/valueset-service-type.html",
                    "code": "540",
                    "display": "Online Service",
                }
            ]
        }
    ],
    "serviceCategory": [
        {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/valueset-service-category.html",
                    "code": "17",
                    "display": "General Practice",
                }
            ]
        }
    ],
    "slot": [{"reference": "Slot/dummy-slot-id"}],
    "participant": [
        {
            "actor": {
                "reference": "Patient/dummy-patient-id",
            },
            "required": "required",
            "status": "accepted",
        },
        {
            "actor": {
                "reference": "PractitionerRole/dummy-role-id",
            },
            "required": "required",
            "status": "accepted",
        },
    ],
}

SLOT_DATA = {
    "resourceType": "Slot",
    "id": "dummy-slot-id",
    "schedule": {"reference": "Schedule/dummy-schedule-id"},
    "status": "busy",
    "start": "2021-08-15T13:55:57.967345+09:00",
    "end": "2021-08-15T14:55:57.967345+09:00",
}

APPOINTMENT_SEARCH_DATA = {
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


def test_update_appointment():
    test_appointment_id = "dummy-appointment-id"

    def mock_get_resource(uid, type):
        if type == "Appointment":
            assert uid == test_appointment_id
            return Appointment.parse_obj(BOOKED_APPOINTMENT_DATA)
        if type == "Slot":
            return Slot.parse_obj(SLOT_DATA)

    def mock_put_resource(uid, resource):
        if type == "Appointment":
            assert uid == test_appointment_id
        return resource

    resource_client = MockResourceClient()
    resource_client.get_resource = mock_get_resource
    resource_client.put_resource = mock_put_resource

    controller = AppointmentController(resource_client)
    req = FakeRequest(data={"status": "noshow"})
    resp = controller.update_appointment(req, test_appointment_id)

    resp_data = json.loads(resp.data.decode("utf-8"))

    assert resp.status_code == 200
    assert resp_data["status"] == "noshow"


def test_update_appointment_return_400_if_not_updating_for_noshow():
    resource_client = MockResourceClient()

    controller = AppointmentController(resource_client)
    req = FakeRequest(data={"status": "cancelled"})
    resp = controller.update_appointment(req, "dummy-appointment-id")

    resp_data = resp.data.decode("utf-8")

    assert resp.status_code == 400
    assert resp_data == "not supporting status update aside from noshow"


def test_search_appointment():
    patient_id = "dummy-patient-id"

    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    expected_search_date = now.date().isoformat()  # defaults to current date

    def mock_search(resource_type, search):
        assert resource_type == "Appointment"
        assert ("date", "ge" + expected_search_date) in search
        assert ("actor", patient_id) in search
        return construct_fhir_element("Bundle", APPOINTMENT_SEARCH_DATA)

    resource_client = MockResourceClient()
    resource_client.search = mock_search

    request = FakeRequest(
        args={"actor_id": patient_id},
        claims={
            "roles": {
                "Patient": {
                    "id": patient_id,
                },
            },
        },
    )
    controller = AppointmentController(resource_client)
    resp = controller.search_appointments(request)
    resp_data = resp.data.decode("utf-8")

    assert resp.status_code == 200
    assert resp_data == json.dumps(APPOINTMENT_SEARCH_DATA)


def test_search_appointment_with_date_provided():
    patient_id = "dummy-patient-id"
    expected_search_date = "2021-08-25"

    def mock_search(resource_type, search):
        assert resource_type == "Appointment"
        assert ("date", "ge" + expected_search_date) in search
        assert ("actor", patient_id) in search
        return construct_fhir_element("Bundle", APPOINTMENT_SEARCH_DATA)

    resource_client = MockResourceClient()
    resource_client.search = mock_search

    request = FakeRequest(
        args={"date": expected_search_date, "actor_id": patient_id},
        claims={
            "roles": {
                "Patient": {
                    "id": patient_id,
                },
            },
        },
    )

    controller = AppointmentController(resource_client)
    resp = controller.search_appointments(request)
    resp_data = resp.data.decode("utf-8")

    assert resp.status_code == 200
    assert resp_data == json.dumps(APPOINTMENT_SEARCH_DATA)


def test_search_appointment_patient_cannot_see_other_people_data():
    other_patient_id = "other-patient-id"
    auth_patient_id = "auth-patient-id"

    resource_client = MockResourceClient()

    request = FakeRequest(
        args={"actor_id": other_patient_id},
        claims={
            "roles": {
                "Patient": {
                    "id": auth_patient_id,
                },
            },
        },
    )
    controller = AppointmentController(resource_client)
    resp = controller.search_appointments(request)
    resp_data = resp.data.decode("utf-8")

    assert resp.status_code == 401
    assert resp_data == "patient can only search appointment for him/herself"


def test_search_appointment_actor_id_is_required():
    auth_patient_id = "auth-patient-id"

    resource_client = MockResourceClient()

    request = FakeRequest(
        args={},
        claims={
            "roles": {
                "Patient": {
                    "id": auth_patient_id,
                },
            },
        },
    )
    controller = AppointmentController(resource_client)
    resp = controller.search_appointments(request)
    resp_data = resp.data.decode("utf-8")

    assert resp.status_code == 400
    assert resp_data == "missing param: actor_id"
