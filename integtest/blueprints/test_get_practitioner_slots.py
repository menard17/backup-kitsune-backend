import json
from datetime import datetime, timedelta
from urllib.parse import quote

import pytz
from pytest_bdd import given, scenarios, then, when

from integtest.characters import Practitioner, Slot
from integtest.conftest import Client
from integtest.utils import create_practitioner, create_user, get_token

scenarios("../features/get_practitioner_slots.feature")


@given("a doctor", target_fixture="practitioner")
def get_doctor(client: Client):
    user = create_user()
    return create_practitioner(client, user)


@when("the practitioner role set the period to busy", target_fixture="slot")
def set_busy_slots(client: Client, practitioner: Practitioner):
    token = get_token(practitioner.uid)

    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    start = now.isoformat()
    end = (now + timedelta(hours=1)).isoformat()

    request_body = {
        "start": start,
        "end": end,
        "status": "busy",
        "comment": "appointment",
    }
    url = f'/practitioner_roles/{practitioner.fhir_data["id"]}/slots'

    resp = client.post(
        url,
        data=json.dumps(request_body),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    slot = json.loads(resp.data)
    assert slot["comment"] == "appointment"
    assert slot["status"] == "busy"
    assert slot["start"] == start
    assert slot["end"] == end
    return slot


@then("the user can fetch those busy slots")
def available_slots(client: Client, practitioner: Practitioner, slot: Slot):
    token = get_token(practitioner.uid)

    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    start = (now - timedelta(hours=1)).isoformat()
    end = (now + timedelta(hours=1)).isoformat()

    url = f'/practitioner_roles/{practitioner.fhir_data["id"]}/slots?start={quote(start)}&end={quote(end)}&status=busy'

    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    slots = json.loads(resp.data)["data"]
    has_slot = False
    for s in slots:
        if s["id"] == slot["id"]:
            has_slot = True
    assert has_slot
