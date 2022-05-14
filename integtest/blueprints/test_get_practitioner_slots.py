import json
from datetime import datetime, timedelta
from urllib.parse import quote

import pytz
from pytest_bdd import given, scenarios, then, when

from integtest.characters import Practitioner, Slot
from integtest.conftest import Client
from integtest.utils import create_practitioner, create_user, get_token

scenarios("../features/get_practitioner_slots.feature")


# Note that this doctor have the following schedule:
# {
#     "daysOfWeek": ["mon", "tue", "wed"],
#     "availableStartTime": "09:00:00",
#     "availableEndTime": "16:30:00",
# }
@given("a doctor with defined schedule", target_fixture="practitioner")
def get_doctor(client: Client):
    user = create_user()
    return create_practitioner(client, user)


@when("the practitioner role set the period to busy", target_fixture="slot")
def set_busy_slots(client: Client, practitioner: Practitioner):
    token = get_token(practitioner.uid)

    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    # Block the time slot on Monday, from 11:10 to 11:50
    # Use a non-15 minutes rounding to test rounding logic as well
    # The result should be the same as blocking from 11:00 to 12:00
    start = tokyo_timezone.localize(datetime(2022, 5, 16, 11, 10)).isoformat()
    end = tokyo_timezone.localize(datetime(2022, 5, 16, 11, 50)).isoformat()

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
def get_busy_slots(client: Client, practitioner: Practitioner, slot: Slot):
    token = get_token(practitioner.uid)

    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    time_at_test = tokyo_timezone.localize(datetime(2022, 5, 16, 11))
    start = (time_at_test - timedelta(hours=1)).isoformat()
    end = (time_at_test + timedelta(hours=1)).isoformat()

    url = f'/practitioner_roles/{practitioner.fhir_data["id"]}/slots?start={quote(start)}&end={quote(end)}&status=busy'

    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    slots = json.loads(resp.data)["data"]
    has_slot = False
    for s in slots:
        if s["id"] == slot["id"]:
            has_slot = True
    assert has_slot


@then("the user can fetch all available slots")
def get_available_slots(client: Client, practitioner: Practitioner):
    token = get_token(practitioner.uid)

    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    # Practitioner schedule on Monday, from 9:00 to 16:30, and each slot is
    # 15 minutes, so there should be a total of 30 slots in a whole day.
    # However, we have a rule to not let the patient book an appointment within
    # 15 minutes delay, so if a patient is trying to book at 9:10, then only
    # appointments from 9:30 to 16:30 is returned (9:10 + 15 min delay
    # and 5 min round up to nearest 15 minutes). Hence there should be 28 slots.
    # The "start" should be used as the current time on the frontend system.
    start = tokyo_timezone.localize(datetime(2022, 5, 16, 9, 10)).isoformat()
    end = tokyo_timezone.localize(datetime(2022, 5, 17, 0)).isoformat()

    url = f'/practitioner_roles/{practitioner.fhir_data["id"]}/slots?start={quote(start)}&end={quote(end)}&status=free'

    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    slots = json.loads(resp.data)["data"]
    assert slots is not None
    assert len(slots) == 28
    assert slots[0]["start"] == "2022-05-16T09:30:00+09:00"
    assert slots[0]["end"] == "2022-05-16T09:45:00+09:00"
    assert slots[-1]["start"] == "2022-05-16T16:15:00+09:00"
    assert slots[-1]["end"] == "2022-05-16T16:30:00+09:00"


@then("the user cannot fetch available slots outside doctor's schedule")
def get_available_slots_outside_schedule(client: Client, practitioner: Practitioner):
    token = get_token(practitioner.uid)

    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    # Practitioner schedule on Monday, Tuesday and Wednesday from 9:00 to 16:30
    # The below tests should not return any results

    # From start of Thursday to end of Sunday
    start = tokyo_timezone.localize(datetime(2022, 5, 19, 0, 0)).isoformat()
    end = tokyo_timezone.localize(datetime(2022, 5, 23, 0, 0)).isoformat()

    url = f'/practitioner_roles/{practitioner.fhir_data["id"]}/slots?start={quote(start)}&end={quote(end)}&status=free'

    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    slots = json.loads(resp.data)["data"]
    assert slots is not None
    assert len(slots) == 0

    # During Monday but out of office hours
    start = tokyo_timezone.localize(datetime(2022, 5, 16, 0, 0)).isoformat()
    end = tokyo_timezone.localize(datetime(2022, 5, 16, 9, 0)).isoformat()

    url = f'/practitioner_roles/{practitioner.fhir_data["id"]}/slots?start={quote(start)}&end={quote(end)}&status=free'

    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    slots = json.loads(resp.data)["data"]
    assert slots is not None
    assert len(slots) == 0

    start = tokyo_timezone.localize(datetime(2022, 5, 16, 16, 30)).isoformat()
    end = tokyo_timezone.localize(datetime(2022, 5, 17, 0, 0)).isoformat()

    url = f'/practitioner_roles/{practitioner.fhir_data["id"]}/slots?start={quote(start)}&end={quote(end)}&status=free'

    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    slots = json.loads(resp.data)["data"]
    assert slots is not None
    assert len(slots) == 0


@then("the user can fecth all available slots except busy slots")
def get_available_slots_except_busy_slots(client: Client, practitioner: Practitioner):
    token = get_token(practitioner.uid)

    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    # Same as the available_slots scenario, there should be 28 slots from
    # 9:30 to 16:30 if a patient try to book at 9:10. However, since there is
    # a busy slot from 11:00 to 12:00, there should only be 24 slots left
    # (9:30 - 11:00 and 12:00 to 16:30).
    start = tokyo_timezone.localize(datetime(2022, 5, 16, 9, 10)).isoformat()
    end = tokyo_timezone.localize(datetime(2022, 5, 17, 0)).isoformat()

    url = f'/practitioner_roles/{practitioner.fhir_data["id"]}/slots?start={quote(start)}&end={quote(end)}&status=free'

    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    slots = json.loads(resp.data)["data"]
    assert slots is not None
    assert len(slots) == 24
    assert slots[0]["start"] == "2022-05-16T09:30:00+09:00"
    assert slots[0]["end"] == "2022-05-16T09:45:00+09:00"
    assert slots[5]["start"] == "2022-05-16T10:45:00+09:00"
    assert slots[5]["end"] == "2022-05-16T11:00:00+09:00"
    # busy slot gap from 11:00 to 12:00
    assert slots[6]["start"] == "2022-05-16T12:00:00+09:00"
    assert slots[6]["end"] == "2022-05-16T12:15:00+09:00"
    assert slots[-1]["start"] == "2022-05-16T16:15:00+09:00"
    assert slots[-1]["end"] == "2022-05-16T16:30:00+09:00"
