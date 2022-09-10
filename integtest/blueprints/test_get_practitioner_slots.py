import json
from datetime import date, datetime, time, timedelta, tzinfo
from urllib.parse import quote

import pytz
from dateutil.parser import isoparse
from pytest_bdd import given, scenarios, then, when

from integtest.characters import Practitioner, Slot
from integtest.conftest import Client
from integtest.utils import create_practitioner, create_user, get_token

scenarios("../features/get_practitioner_slots.feature")

MINIMUM_DELAY_BETWEEN_BOOKING = timedelta(minutes=15)
POTENTIAL_CLOCK_DRIFT = timedelta(minutes=1)


# Note that this doctor have the following schedule:
# {
#     "daysOfWeek": ["mon", "tue", "wed"],
#     "availableStartTime": "09:00:00",
#     "availableEndTime": "16:30:00",
# }
# Most of the test in this module use next week at the time of test, so that
# it's easier to write test without inteference from current-time logic.
@given("a doctor with defined schedule", target_fixture="practitioner")
def get_doctor(client: Client):
    user = create_user()
    return create_practitioner(client, user)


# There is a special case where we want to test the minimum delay between
# booking mechanism, so use a doctor with full schedule in order to have more
# available slots and prevent flaky tests.
@given("a doctor with full schedule", target_fixture="practitioner")
def get_doctor_full_schedule(client: Client):
    user = create_user()
    return create_practitioner(
        client,
        user,
        available_time=[
            {
                "daysOfWeek": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
                "availableStartTime": "00:00:00",
                "availableEndTime": "23:59:59",
            }
        ],
    )


@when("the practitioner role set the period to busy", target_fixture="slot")
def set_busy_slots(client: Client, practitioner: Practitioner):
    token = get_token(practitioner.uid)

    timezone = pytz.timezone("Asia/Tokyo")
    # Block the time slot tomorrow, from 11:09 to 11:51.
    # Use a non-10 minutes rounding to test rounding logic as well
    # The result should be the same as blocking from 11:00 to 12:00
    next_monday = _next_weekday(datetime.today(), 0)
    start = _localize(next_monday, time(11, 9), timezone).isoformat()
    end = _localize(next_monday, time(11, 51), timezone).isoformat()

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

    timezone = pytz.timezone("Asia/Tokyo")
    next_monday = _next_weekday(datetime.today(), 0)
    start = _localize(next_monday, time(0, 0), timezone).isoformat()
    end = _localize(next_monday + timedelta(days=1), time(0, 0), timezone).isoformat()
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

    timezone = pytz.timezone("Asia/Tokyo")
    # Practitioner schedule on any day, from 9:00 to 16:30, and each slot is
    # 10 minutes, so there should be a total of 45 slots in a whole day.
    next_monday = _next_weekday(datetime.today(), 0)
    start = _localize(next_monday, time(0, 0), timezone).isoformat()
    end = _localize(next_monday + timedelta(days=1), time(0, 0), timezone).isoformat()

    url = f'/practitioner_roles/{practitioner.fhir_data["id"]}/slots?start={quote(start)}&end={quote(end)}&status=free'

    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    slots = json.loads(resp.data)["data"]
    assert slots is not None
    assert len(slots) == 45
    assert slots[0]["start"] == _localize(next_monday, time(9, 0), timezone).isoformat()
    assert slots[0]["end"] == _localize(next_monday, time(9, 10), timezone).isoformat()
    assert (
        slots[-1]["start"] == _localize(next_monday, time(16, 20), timezone).isoformat()
    )
    assert (
        slots[-1]["end"] == _localize(next_monday, time(16, 30), timezone).isoformat()
    )


@then("the user cannot fetch available slots outside doctor's schedule")
def get_available_slots_outside_schedule(client: Client, practitioner: Practitioner):
    token = get_token(practitioner.uid)

    timezone = pytz.timezone("Asia/Tokyo")

    # Practitioner schedule on Monday, Tuesday and Wednesday from 9:00 to 16:30
    # The below tests should not return any results

    # From start of Thursday to end of Sunday
    next_thursday = _next_weekday(datetime.today(), 4)
    start = _localize(next_thursday, time(0, 0), timezone).isoformat()
    end = _localize(next_thursday + timedelta(days=1), time(0, 0), timezone).isoformat()
    url = f'/practitioner_roles/{practitioner.fhir_data["id"]}/slots?start={quote(start)}&end={quote(end)}&status=free'

    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    slots = json.loads(resp.data)["data"]
    assert slots is not None
    assert len(slots) == 0

    # During Monday but before office hours (before 9:00)
    next_monday = _next_weekday(datetime.today(), 0)
    start = _localize(next_monday, time(0, 0), timezone).isoformat()
    end = _localize(next_monday, time(9, 0), timezone).isoformat()
    url = f'/practitioner_roles/{practitioner.fhir_data["id"]}/slots?start={quote(start)}&end={quote(end)}&status=free'

    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    slots = json.loads(resp.data)["data"]
    assert slots is not None
    assert len(slots) == 0

    # During Monday but after office hours (after 16:30)
    start = _localize(next_monday, time(17, 0), timezone).isoformat()
    end = _localize(next_monday + timedelta(days=1), time(0, 0), timezone).isoformat()

    url = f'/practitioner_roles/{practitioner.fhir_data["id"]}/slots?start={quote(start)}&end={quote(end)}&status=free'

    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    slots = json.loads(resp.data)["data"]
    assert slots is not None
    assert len(slots) == 0


@then("the user can fetch all available slots except busy slots")
def get_available_slots_except_busy_slots(client: Client, practitioner: Practitioner):
    token = get_token(practitioner.uid)

    timezone = pytz.timezone("Asia/Tokyo")
    # Same as the available_slots scenario, there should be 45 slots from
    # 9:00 to 16:30. However, since there is a busy slot from 11:00 to 12:00,
    # there should only be 41 slots left (9:00 - 11:00 and 12:00 to 16:30).
    next_monday = _next_weekday(datetime.today(), 0)
    start = _localize(next_monday, time(0, 0), timezone).isoformat()
    end = _localize(next_monday + timedelta(days=1), time(0, 0), timezone).isoformat()

    url = f'/practitioner_roles/{practitioner.fhir_data["id"]}/slots?start={quote(start)}&end={quote(end)}&status=free'

    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    slots = json.loads(resp.data)["data"]
    assert slots is not None
    assert len(slots) == 39
    assert slots[0]["start"] == _localize(next_monday, time(9, 0), timezone).isoformat()
    assert slots[0]["end"] == _localize(next_monday, time(9, 10), timezone).isoformat()
    assert (
        slots[11]["start"] == _localize(next_monday, time(10, 50), timezone).isoformat()
    )
    assert slots[11]["end"] == _localize(next_monday, time(11, 0), timezone).isoformat()
    # busy slot gap from 11:00 to 12:00
    assert (
        slots[12]["start"] == _localize(next_monday, time(12, 0), timezone).isoformat()
    )
    assert (
        slots[12]["end"] == _localize(next_monday, time(12, 10), timezone).isoformat()
    )
    assert (
        slots[-1]["start"] == _localize(next_monday, time(16, 20), timezone).isoformat()
    )
    assert (
        slots[-1]["end"] == _localize(next_monday, time(16, 30), timezone).isoformat()
    )


@then("the user can only fetch slots after minimum delay booking")
def get_available_slots_after_minimum_delay(client: Client, practitioner: Practitioner):
    token = get_token(practitioner.uid)

    timezone = pytz.timezone("Asia/Tokyo")
    # This is a special test case, where we want to make sure that the user
    # cannot book a slot given a minimum delay between booking. For example if
    # the current clock is 10:00, and the minimum delay booking is 15 mins, then
    # only available slots from 10:15 is present.
    # Due to the fact that the backend logic uses datetime.now() and it's hard
    # to mock the time inside integration test, we run this test for today and
    # dynamically check if the first slot (if present) is inside the range.
    # Also add a potential clock drift so that it's more tolerant to system
    # time.
    now = datetime.now()
    today = now.date()
    start = _localize(today, time(0, 0), timezone).isoformat()
    end = _localize(today + timedelta(days=1), time(0, 0), timezone).isoformat()

    url = f'/practitioner_roles/{practitioner.fhir_data["id"]}/slots?start={quote(start)}&end={quote(end)}&status=free'
    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    slots = json.loads(resp.data)["data"]
    assert slots is not None
    assert len(slots) == 0 or isoparse(slots[0]["start"]) > (
        now.astimezone(timezone) + MINIMUM_DELAY_BETWEEN_BOOKING - POTENTIAL_CLOCK_DRIFT
    )


def _localize(date: date, time: time, timezone: tzinfo):
    return timezone.localize(datetime.combine(date, time))


# weekday is a number from 0 to 6, where 0 is Monday and 6 is Sunday
def _next_weekday(d: date, weekday: int):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return d + timedelta(days_ahead)
