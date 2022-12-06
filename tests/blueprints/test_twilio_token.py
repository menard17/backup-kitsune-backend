import uuid
from datetime import datetime, timedelta, timezone

from fhir.resources.appointment import Appointment
from helper import FakeRequest, MockResourceClient

from blueprints.twilio_token import TwilioTokenController
from tests.blueprints.test_appointments import BOOKED_APPOINTMENT_DATA

ACCID = "ACCID"
SECRET = "Secret"
SID = "Sid"


class MockTwilioObject:
    def __init__(self, acc_sid, secret, sid):
        self.acc_sid = acc_sid
        self.secret = secret
        self.sid = sid


def test_twilio_token_before_meeting():
    """Set the USER env var to assert the behavior."""
    BOOKED_APPOINTMENT_DATA["start"] = datetime.now(timezone.utc) + timedelta(hours=1)
    BOOKED_APPOINTMENT_DATA["end"] = datetime.now(timezone.utc) + timedelta(hours=2)

    def mock_get_resource(id, resource_type):
        return Appointment.parse_obj(BOOKED_APPOINTMENT_DATA)

    resource_client = MockResourceClient()
    resource_client.get_resource = mock_get_resource

    twilio_object = MockTwilioObject(ACCID, SECRET, SID)

    controller = TwilioTokenController(resource_client, twilio_object=twilio_object)
    req = FakeRequest(
        args={
            "appointment_id": str(uuid.uuid4()),
            "identity_id": str(uuid.uuid4()),
        }
    )

    resp = controller.get_twilio_token(req)

    assert resp.status_code == 400
    assert resp.data.decode("utf-8") == "meeting is not started yet"


def test_twilio_token_after_meeting():
    """Set the USER env var to assert the behavior."""
    BOOKED_APPOINTMENT_DATA["start"] = datetime.now(timezone.utc) - timedelta(hours=2)
    BOOKED_APPOINTMENT_DATA["end"] = datetime.now(timezone.utc) - timedelta(hours=1)

    def mock_get_resource(id, resource_type):
        return Appointment.parse_obj(BOOKED_APPOINTMENT_DATA)

    resource_client = MockResourceClient()
    resource_client.get_resource = mock_get_resource

    twilio_object = MockTwilioObject(ACCID, SECRET, SID)

    controller = TwilioTokenController(resource_client, twilio_object=twilio_object)
    req = FakeRequest(
        args={
            "appointment_id": str(uuid.uuid4()),
            "identity_id": str(uuid.uuid4()),
        }
    )

    resp = controller.get_twilio_token(req)

    assert resp.status_code == 400
    assert resp.data.decode("utf-8") == "meeting is already finished"


def test_not_participant():
    """Set the USER env var to assert the behavior."""
    BOOKED_APPOINTMENT_DATA["start"] = datetime.now(timezone.utc)
    BOOKED_APPOINTMENT_DATA["end"] = datetime.now(timezone.utc) + timedelta(hours=1)

    def mock_get_resource(id, resource_type):
        return Appointment.parse_obj(BOOKED_APPOINTMENT_DATA)

    resource_client = MockResourceClient()
    resource_client.get_resource = mock_get_resource
    twilio_object = MockTwilioObject(ACCID, SECRET, SID)
    controller = TwilioTokenController(resource_client, twilio_object=twilio_object)
    req = FakeRequest(
        args={
            "appointment_id": str(uuid.uuid4()),
            "identity_id": str(uuid.uuid4()),
        }
    )
    resp = controller.get_twilio_token(req)

    assert resp.status_code == 400
    assert resp.data.decode("utf-8") == "not participant for the meeting"


def test_on_time():
    """Set the USER env var to assert the behavior."""
    BOOKED_APPOINTMENT_DATA["start"] = datetime.now(timezone.utc)
    BOOKED_APPOINTMENT_DATA["end"] = datetime.now(timezone.utc) + timedelta(hours=1)

    def mock_get_resource(id, resource_type):
        return Appointment.parse_obj(BOOKED_APPOINTMENT_DATA)

    resource_client = MockResourceClient()
    resource_client.get_resource = mock_get_resource
    twilio_object = MockTwilioObject(ACCID, SECRET, SID)

    controller = TwilioTokenController(resource_client, twilio_object=twilio_object)

    req = FakeRequest(
        args={
            "appointment_id": "appointment_id",
            "identity_id": "dummy-role-id",
        }
    )

    res = controller.get_twilio_token(req)
    assert res.status_code == 200
