from datetime import datetime, timedelta, timezone

from fhir.resources import construct_fhir_element

from services.appointment_service import AppointmentService
from tests.blueprints.helper import FakeRequest

tz_jst = timezone(timedelta(hours=9))


def get_appointment(start, end):
    return {
        "resourceType": "Appointment",
        "status": "booked",
        "description": "Booking practitioner role",
        "start": start,
        "end": end,
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


class MockAppointmentResourceClient:
    def __init__(self, start, end):
        self.appointment_dict = get_appointment(start, end)

    def get_resource(self, id, resource):
        if resource == "Appointment":
            return construct_fhir_element(resource, self.appointment_dict)
        return ""


def test_jst_timezone():
    # Given
    datetime_format = "%Y-%m-%dT%H:%M:%S+09:00"
    start_time = datetime.now(tz_jst).strftime(datetime_format)
    end_time = (datetime.now(tz_jst) + timedelta(minutes=15)).strftime(datetime_format)
    resource_client = MockAppointmentResourceClient(start_time, end_time)
    appointment_service = AppointmentService(resource_client)

    # When
    ontime, _ = appointment_service.check_appointment_ontime(1)

    # Then
    assert ontime


def test_different_timezone():
    # Given
    datetime_format = "%Y-%m-%dT%H:%M:%S+00:00"
    start_time = (datetime.now(timezone.utc)).strftime(datetime_format)
    end_time = (datetime.now(timezone.utc) + timedelta(minutes=15)).strftime(
        datetime_format
    )
    resource_client = MockAppointmentResourceClient(start_time, end_time)
    appointment_service = AppointmentService(resource_client)

    # When
    ontime, _ = appointment_service.check_appointment_ontime(1)

    # Then
    assert ontime


def test_check_link_should_success():
    service = AppointmentService(None)

    fake_req = FakeRequest(
        claims={
            "roles": {
                "Practitioner": {"id": "dummy-id"},
            },
        }
    )
    valid_link = "https://my.fhir.link/Appointment/?_count=1&actor=87c802f0-c486-438d-b2e9-e06543303b4c&date=ge2022-05-21&_page_token=Cjj3YokQdv%2F%2F%2F%2F%2BABd%2BH721RFgD%2FAf%2F%2BNWM4NDM2YmQ3ZWExOTZiYTE5NzAyMDQ4Njc4NjMyOWUAARABIZRNcFwxQ70GOQAAAACJ73adSAFQAFoLCbs%2BeLJbiDrKEANg2qiOZGgB"  # noqa: E501
    ok, respErr = service.check_link(fake_req, valid_link)

    assert ok
    assert respErr is None


def test_check_link_should_return_err_response_if_invalid_link():
    service = AppointmentService(None)

    fake_req = FakeRequest(
        claims={
            "roles": {
                "Practitioner": {"id": "dummy-id"},
            },
        }
    )
    valid_link = "https://my.fhir.link/Appointment?actor=first-actor-id&actor=second-actor-causing-failure"
    ok, respErr = service.check_link(fake_req, valid_link)

    assert ok is False
    assert respErr.status_code == 400
    assert respErr.data == b"invalid link"


def test_check_link_should_return_err_response_if_not_related_to_appointment():
    service = AppointmentService(None)

    fake_req = FakeRequest(
        claims={
            "roles": {
                "Practitioner": {"id": "dummy-id"},
            },
        }
    )
    valid_link = "https://my.fhir.link/Patient?_count=1&actor=87c802f0-c486-438d-b2e9-e06543303b4c&date=ge2022-05-21&_page_token=Cjj3YokQdv%2F%2F%2F%2F%2BABd%2BH721RFgD%2FAf%2F%2BNWM4NDM2YmQ3ZWExOTZiYTE5NzAyMDQ4Njc4NjMyOWUAARABIZRNcFwxQ70GOQAAAACJ73adSAFQAFoLCbs%2BeLJbiDrKEANg2qiOZGgB"  # noqa: E501
    ok, respErr = service.check_link(fake_req, valid_link)

    assert ok is False
    assert respErr.status_code == 400
    assert respErr.data == b"not link for appointment"


def test_check_link_should_return_err_response_if_not_authorized():
    service = AppointmentService(None)

    fake_req = FakeRequest(
        claims={
            "roles": {
                "Patient": {
                    "id": "dummy-id"
                },  # patient can only see his/her appointments
            },
        }
    )
    valid_link = "https://my.fhir.link/Appointment?_count=1&actor=87c802f0-c486-438d-b2e9-e06543303b4c&date=ge2022-05-21&_page_token=Cjj3YokQdv%2F%2F%2F%2F%2BABd%2BH721RFgD%2FAf%2F%2BNWM4NDM2YmQ3ZWExOTZiYTE5NzAyMDQ4Njc4NjMyOWUAARABIZRNcFwxQ70GOQAAAACJ73adSAFQAFoLCbs%2BeLJbiDrKEANg2qiOZGgB"  # noqa: E501
    ok, respErr = service.check_link(fake_req, valid_link)

    assert ok is False
    assert respErr.status_code == 401
    assert respErr.data == b"not authorized"
