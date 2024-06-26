import copy
import json
from datetime import datetime

import pytz
from fhir.resources import construct_fhir_element
from fhir.resources.appointment import Appointment
from fhir.resources.patient import Patient
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

PATIENT_DATA = {
    "resourceType": "Patient",
    "id": "example",
    "active": True,
    "name": [{"use": "official", "family": "Chalmers", "given": ["Peter", "James"]}],
    "gender": "male",
    "birthDate": "1990-01-01",
    "deceasedBoolean": False,
    "address": [
        {
            "use": "home",
            "type": "both",
            "text": "534 Erewhon St PeasantVille, Rainbow, Vic  3999",
            "line": ["534 Erewhon St"],
            "city": "PleasantVille",
            "district": "Rainbow",
            "state": "Vic",
            "postalCode": "3999",
            "period": {"start": "1974-12-25"},
            "country": "US",
        }
    ],
    "telecom": [
        {"system": "email", "use": "home", "value": "example@umed.jp"},
        {"system": "phone", "use": "mobile", "value": "00000000000"},
    ],
}


def test_get_appointment():
    test_appointment_id = "dummy-appointment-id"

    def mock_get_resource(uid, type):
        if type == "Appointment":
            assert uid == test_appointment_id
            return Appointment.parse_obj(BOOKED_APPOINTMENT_DATA)

    resource_client = MockResourceClient()
    resource_client.get_resource = mock_get_resource

    controller = AppointmentController(resource_client)
    resp = controller.get_appointment(test_appointment_id)

    assert resp.status_code == 200


def test_update_appointment():
    test_appointment_id = "dummy-appointment-id"

    def mock_get_resource(uid, type):
        if type == "Appointment":
            assert uid == test_appointment_id
            return Appointment.parse_obj(BOOKED_APPOINTMENT_DATA)
        if type == "Slot":
            return Slot.parse_obj(SLOT_DATA)
        if type == "Patient":
            return Patient.parse_obj(PATIENT_DATA)

    def mock_put_resource(resource, uid):
        return {
            "resource": resource,
            "request": {"method": "PUT", "url": f"https://example.com/{uid}"},
        }

    def mock_create_resources(bundles):
        class MockResource:
            resource_type = "Appointment"
            no_show_appointment = copy.deepcopy(BOOKED_APPOINTMENT_DATA)
            no_show_appointment["status"] = "noshow"
            resource = Appointment.parse_obj(no_show_appointment)

        class MockBundle:
            entry = [MockResource]

        return MockBundle()

    resource_client = MockResourceClient()
    resource_client.get_put_bundle = mock_put_resource
    resource_client.get_resource = mock_get_resource
    resource_client.create_resources = mock_create_resources

    controller = AppointmentController(resource_client)
    req = FakeRequest(data={"status": "noshow", "email_notification": "false"})
    resp = controller.update_appointment(req, test_appointment_id)

    resp_data = json.loads(resp.data.decode("utf-8"))

    assert resp.status_code == 200
    assert resp_data["status"] == "noshow"


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
        args={"actor_id": patient_id, "date": expected_search_date},
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
    assert (
        json.loads(resp_data)["data"][0]["id"]
        == APPOINTMENT_SEARCH_DATA["entry"][0]["resource"]["id"]
    )


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
    assert (
        json.loads(resp_data)["data"][0]["id"]
        == APPOINTMENT_SEARCH_DATA["entry"][0]["resource"]["id"]
    )


def test_search_appointment_with_start_date_and_date_provided_should_fail():
    patient_id = "dummy-patient-id"
    expected_search_start_date = "2021-08-25"
    expected_search_date = "2022-01-01"

    resource_client = MockResourceClient()

    request = FakeRequest(
        args={
            "start_date": expected_search_start_date,
            "date": expected_search_date,
            "actor_id": patient_id,
        },
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

    assert resp.status_code == 400
    assert resp_data == "both date and start_date supplied. Use start_date."


def test_search_appointment_with_start_date_and_end_date_provided():
    patient_id = "dummy-patient-id"
    expected_search_start_date = "2021-08-25"
    expected_search_end_date = "2022-01-01"

    def mock_search(resource_type, search):
        assert resource_type == "Appointment"
        assert ("date", "ge" + expected_search_start_date) in search
        assert ("date", "le" + expected_search_end_date) in search
        assert ("actor", patient_id) in search
        return construct_fhir_element("Bundle", APPOINTMENT_SEARCH_DATA)

    resource_client = MockResourceClient()
    resource_client.search = mock_search

    request = FakeRequest(
        args={
            "start_date": expected_search_start_date,
            "end_date": expected_search_end_date,
            "actor_id": patient_id,
        },
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
    assert (
        json.loads(resp_data)["data"][0]["id"]
        == APPOINTMENT_SEARCH_DATA["entry"][0]["resource"]["id"]
    )


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
    assert resp_data == "Unauthorized for the actor_id"


def test_search_appointment_patiets_if_both_practitioner_and_patient_present():
    other_patient_id = "other-patient-id"
    auth_patient_id = "auth-patient-id"

    practitioner_id = "practitioner_id"

    resource_client = MockResourceClient()

    request = FakeRequest(
        args={"actor_id": other_patient_id},
        claims={
            "roles": {
                "Patient": {
                    "id": auth_patient_id,
                },
                "Practitioner": {"id": practitioner_id},
            },
        },
    )
    controller = AppointmentController(resource_client)
    resp = controller.search_appointments(request)

    assert resp.status_code == 200


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


def test_search_appointment_pagination_returns_next_link():
    patient_id = "dummy-patient-id"

    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    expected_search_date = now.date().isoformat()  # defaults to current date
    expected_count = 1  # page size
    expected_url = "https://healthcare.googleapis.com/v1/projects/dummy-fhir-path/fhirStores/phat-fhir-store-id/fhir/Appointment/?_count=1&actor=9e477534-b74a-4139-9338-90977e81bc34&date=ge2021-08-25&page_token=Cjj3YokQdv%2F%2F%2F%2F%2BABd%2BH721RFgD%2FAf%2F%2BNWM4NDM2YmQ3ZWExOTZiYTE5NzAyMDQ4Njc4NjMyOWUAARABIZRNcFwxQ70GOQAAAACJ73adSAFQAFoLCbs%2BeLJbiDrKEANg2qiOZGgB"  # noqa: E501

    def mock_search(resource_type, search):
        assert resource_type == "Appointment"
        assert ("date", "ge" + expected_search_date) in search
        assert ("actor", patient_id) in search
        assert ("_count", f"{expected_count}") in search

        # add next page link search result
        APPOINTMENT_SEARCH_DATA["link"].append(
            {
                "relation": "next",
                "url": expected_url,
            }
        )
        return construct_fhir_element("Bundle", APPOINTMENT_SEARCH_DATA)

    resource_client = MockResourceClient()
    resource_client.search = mock_search

    request = FakeRequest(
        args={
            "actor_id": patient_id,
            "start_date": expected_search_date,
            "count": expected_count,
        },
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
    assert json.loads(resp_data)["next_link"] == expected_url
