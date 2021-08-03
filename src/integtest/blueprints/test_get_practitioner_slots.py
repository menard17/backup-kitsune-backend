import json
import pytz

from pytest_bdd import scenarios, given, when, then, parsers
from firebase_admin import auth
from datetime import datetime, timedelta

from fhir.resources import construct_fhir_element
from adapters.fhir_store import ResourceClient
from integtest.utils import get_token
from urllib.parse import quote

TEST_USER_1_UUID = "lFmnnQFWznZZ8C2l9hUmq41liPn1"

scenarios('../features/get_practitioner_slots.feature')

@given("a practitioner role is created", target_fixture="role")
def create_practitioner(client):
    token = auth.create_custom_token(TEST_USER_1_UUID)
    token = get_token(TEST_USER_1_UUID)
    resource_client = ResourceClient()

    practitioner_data = {
        "resourceType": "Practitioner",
        "active": True,
        "name": [{
            "family": "Test",
            "given": [
                "Cool"
            ],
            "prefix": [
                "Dr"
            ]
        }],
    }

    practitioner = construct_fhir_element("Practitioner", practitioner_data)
    practitioner = resource_client.create_resource(practitioner)

    role = {
        "resourceType": "PractitionerRole",
        "active": True,
        "period": {
            "start": "2001-01-01",
            "end": "2099-03-31"
        },
        "practitioner": {
            "reference": f"Practitioner/{practitioner.id}",
            "display": "Dr Cool in test"
        },
        "availableTime": [
            {
                "daysOfWeek": [
                    "mon",
                    "tue",
                    "wed"
                ],
                "availableStartTime": "09:00:00",
                "availableEndTime": "16:30:00"
            },
            {
                "daysOfWeek": [
                    "thu",
                    "fri"
                ],
                "availableStartTime": "09:00:00",
                "availableEndTime": "12:00:00"
            }
        ],
        "notAvailable": [{
            "description": "Adam will be on extended leave during May 2017",
            "during": {
                "start": "2017-05-01",
                "end": "2017-05-20"
            }
        }],
        "availabilityExceptions": "Adam is generally unavailable on public holidays and during the Christmas/New Year break",
    }

    resp = client.post(
        '/practitioner_roles',
        data=json.dumps(role),
        headers={"Authorization": f"Bearer {token}"},
        content_type='application/json'
    )

    role = json.loads(resp.data)["practitioner_role"]
    assert role["practitioner"]["reference"] == f"Practitioner/{practitioner.id}"
    return role

@when("the practitioner role set the period to busy", target_fixture="slot")
def set_busy_slots(client, role):
    token = auth.create_custom_token(TEST_USER_1_UUID)
    token = get_token(TEST_USER_1_UUID)

    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    start = now.isoformat()
    end = (now + timedelta(hours=1)).isoformat()

    request_body = {
        "start": start,
        "end": end,
        "status": "busy",
    }
    url = f'/practitioner_roles/{role["id"]}/slots'

    resp = client.post(
        url,
        data=json.dumps(request_body),
        headers={"Authorization": f"Bearer {token}"},
        content_type='application/json'
    )
    slot = json.loads(resp.data)
    assert slot["comment"] == "slot creation from backend"
    assert slot["status"] == "busy"
    assert slot["start"] == start
    assert slot["end"] == end
    return slot

@then("the user can fetch those busy slots")
def available_slots(client, role, slot):
    token = auth.create_custom_token(TEST_USER_1_UUID)
    token = get_token(TEST_USER_1_UUID)

    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    start = (now - timedelta(hours=1)).isoformat()
    end = (now + timedelta(hours=1)).isoformat()

    url = f'/practitioner_roles/{role["id"]}/slots?start={quote(start)}&end={quote(end)}&status=busy'

    resp = client.get(
        url,
        headers={"Authorization": f"Bearer {token}"}
    )
    slots = json.loads(resp.data)["data"]
    hasSlot = False
    for s in slots:
        if s["id"] == slot["id"]:
            hasSlot = True
    assert hasSlot
