import json

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
    req = FakeRequest({"status": "noshow"})
    resp = controller.update_appointment(req, test_appointment_id)

    resp_data = json.loads(resp.data.decode("utf-8"))

    assert resp.status_code == 200
    assert resp_data["status"] == "noshow"


def test_update_appointment_return_400_if_not_updating_for_noshow():
    resource_client = MockResourceClient()

    controller = AppointmentController(resource_client)
    req = FakeRequest({"status": "cancelled"})
    resp = controller.update_appointment(req, "dummy-appointment-id")

    resp_data = resp.data.decode("utf-8")

    assert resp.status_code == 400
    assert resp_data == "not supporting status update aside from noshow"
