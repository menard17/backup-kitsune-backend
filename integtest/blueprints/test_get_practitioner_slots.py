import json
import uuid
from datetime import datetime, timedelta
from urllib.parse import quote

import pytz
from firebase_admin import auth
from pytest_bdd import given, scenarios, then, when

from integtest.blueprints.characters import Doctor, Slot
from integtest.blueprints.fhir_input_constants import PRACTITIONER_DATA
from integtest.blueprints.helper import get_role
from integtest.conftest import Client
from integtest.utils import get_token

scenarios("../features/get_practitioner_slots.feature")


@given("a practitioner role is created", target_fixture="doctor")
def create_practitioner(client: Client):
    doctor = auth.create_user(
        email=f"doctor-{uuid.uuid4()}@fake.umed.jp",
        email_verified=True,
        password=f"password-{uuid.uuid4()}",
        display_name="Test Doctor",
        disabled=False,
    )

    token = auth.create_custom_token(doctor.uid)
    token = get_token(doctor.uid)

    practitioner_resp = client.post(
        "/practitioners",
        data=json.dumps(PRACTITIONER_DATA),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert practitioner_resp.status_code == 202
    practitioner_id = json.loads(practitioner_resp.data.decode("utf-8"))["id"]

    practitioner_roles_resp = client.post(
        "/practitioner_roles",
        data=json.dumps(get_role(practitioner_id)),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    role = json.loads(practitioner_roles_resp.data)["practitioner_role"]
    assert role["practitioner"]["reference"] == f"Practitioner/{practitioner_id}"
    return Doctor(doctor.uid, role)


@when("the practitioner role set the period to busy", target_fixture="slot")
def set_busy_slots(client: Client, doctor: Doctor):
    token = auth.create_custom_token(doctor.uid)
    token = get_token(doctor.uid)

    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    start = now.isoformat()
    end = (now + timedelta(hours=1)).isoformat()

    request_body = {
        "start": start,
        "end": end,
        "status": "busy",
    }
    url = f'/practitioner_roles/{doctor.fhir_data["id"]}/slots'

    resp = client.post(
        url,
        data=json.dumps(request_body),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    slot = json.loads(resp.data)
    assert slot["comment"] == "slot creation from backend"
    assert slot["status"] == "busy"
    assert slot["start"] == start
    assert slot["end"] == end
    return slot


@then("the user can fetch those busy slots")
def available_slots(client: Client, doctor: Doctor, slot: Slot):
    token = auth.create_custom_token(doctor.uid)
    token = get_token(doctor.uid)

    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    start = (now - timedelta(hours=1)).isoformat()
    end = (now + timedelta(hours=1)).isoformat()

    url = f'/practitioner_roles/{doctor.fhir_data["id"]}/slots?start={quote(start)}&end={quote(end)}&status=busy'

    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    slots = json.loads(resp.data)["data"]
    has_slot = False
    for s in slots:
        if s["id"] == slot["id"]:
            has_slot = True
    assert has_slot
