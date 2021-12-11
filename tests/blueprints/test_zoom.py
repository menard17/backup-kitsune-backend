import json
from datetime import datetime, timedelta, timezone

import jwt
from fhir.resources.appointment import Appointment
from helper import FakeRequest, MockResourceClient

from blueprints.zoom import ZoomController
from tests.blueprints.test_appointments import BOOKED_APPOINTMENT_DATA


class MockZoomObject:
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret


def test_zoom_before_meeting():
    """Set the USER env var to assert the behavior."""
    BOOKED_APPOINTMENT_DATA["start"] = datetime.now(timezone.utc) + timedelta(hours=1)
    BOOKED_APPOINTMENT_DATA["end"] = datetime.now(timezone.utc) + timedelta(hours=2)

    def mock_get_resource(id, resource_type):
        return Appointment.parse_obj(BOOKED_APPOINTMENT_DATA)

    resource_client = MockResourceClient()
    resource_client.get_resource = mock_get_resource

    controller = ZoomController(resource_client)
    req = FakeRequest(args={"appointment_id": "5150902a-4ca6-49a7-9130-76720264964c"})

    KEY = "Key"
    SECRET = "Secret"
    zoom_object = MockZoomObject(KEY, SECRET)

    resp = controller.get_zoom_jwt(req, zoom_object)

    assert resp.status == "400 BAD REQUEST"
    assert resp.data.decode("utf-8") == "meeting is not started yet"


def test_zoom_after_meeting():
    """Set the USER env var to assert the behavior."""
    BOOKED_APPOINTMENT_DATA["start"] = datetime.now(timezone.utc) - timedelta(hours=2)
    BOOKED_APPOINTMENT_DATA["end"] = datetime.now(timezone.utc) - timedelta(hours=1)

    def mock_get_resource(id, resource_type):
        return Appointment.parse_obj(BOOKED_APPOINTMENT_DATA)

    resource_client = MockResourceClient()
    resource_client.get_resource = mock_get_resource

    controller = ZoomController(resource_client)
    req = FakeRequest(args={"appointment_id": "5150902a-4ca6-49a7-9130-76720264964c"})

    KEY = "Key"
    SECRET = "Secret"
    zoom_object = MockZoomObject(KEY, SECRET)

    resp = controller.get_zoom_jwt(req, zoom_object)

    assert resp.status == "400 BAD REQUEST"
    assert resp.data.decode("utf-8") == "meeting is already finished"


def test_zoom_on_time():
    """Set the USER env var to assert the behavior."""
    BOOKED_APPOINTMENT_DATA["start"] = datetime.now(timezone.utc)
    BOOKED_APPOINTMENT_DATA["end"] = datetime.now(timezone.utc) + timedelta(hours=1)

    def mock_get_resource(id, resource_type):
        return Appointment.parse_obj(BOOKED_APPOINTMENT_DATA)

    resource_client = MockResourceClient()
    resource_client.get_resource = mock_get_resource

    controller = ZoomController(resource_client)
    req = FakeRequest(args={"appointment_id": "5150902a-4ca6-49a7-9130-76720264964c"})

    KEY = "Key"
    SECRET = "Secret"
    zoom_object = MockZoomObject(KEY, SECRET)

    resp_data = controller.get_zoom_jwt(req, zoom_object).data.decode("utf-8")
    token = (json.loads(resp_data))["data"]["jwt"]
    decoded_token = jwt.decode(token, SECRET, algorithms="HS256")

    assert KEY == decoded_token["appKey"]
