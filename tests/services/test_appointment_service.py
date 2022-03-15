from datetime import datetime, timedelta, timezone

from fhir.resources import construct_fhir_element

from services.appointment_service import AppointmentService

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
    start_time = (datetime.now()).strftime(datetime_format)
    end_time = (datetime.now() + timedelta(minutes=15)).strftime(datetime_format)
    resource_client = MockAppointmentResourceClient(start_time, end_time)
    appointment_service = AppointmentService(resource_client)

    # When
    ontime, _ = appointment_service.check_appointment_ontime(1)

    # Then
    assert ontime
