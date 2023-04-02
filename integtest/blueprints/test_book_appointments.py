import json
from datetime import datetime, timedelta, timezone
from urllib.parse import quote, urlencode

import pytz
from firebase_admin import auth
from pytest_bdd import parsers, scenarios, then, when
from pytest_bdd.steps import given

from integtest.characters import Appointment, Patient, Practitioner, User
from integtest.conftest import Client
from integtest.utils import (
    create_appointment,
    create_encounter,
    create_patient,
    create_practitioner,
    create_user,
    get_token,
    make_admin,
)

scenarios("../features/book_appointments.feature")


@given("a user", target_fixture="user")
def get_user() -> User:
    return create_user()


@given("a patient with nurse user", target_fixture="nurse_user")
def get_patient(client: Client) -> Patient:
    user = create_user()
    create_patient(client, user)
    return user


@given("a doctor", target_fixture="practitioner")
def get_doctor(client: Client) -> Practitioner:
    user = create_user()
    return create_practitioner(client, user, role_type="doctor")


@given("a doctor B", target_fixture="practitioner_b")
def get_doctor_b(client: Client) -> Practitioner:
    user = create_user()
    return create_practitioner(client, user, role_type="doctor")


@given("patient A", target_fixture="patient_a")
def get_patient_a(client: Client, user) -> Patient:
    return create_patient(client, user)


@given("a patient A", target_fixture="patient_a")
def get_patient_A(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


@given(
    "a doctor is created with the same user as patient A",
    target_fixture="practitioner_a",
)
def get_doctor_a(client: Client, user) -> Practitioner:
    return create_practitioner(client, user, role_type="doctor")


@given("a nurse", target_fixture="nurse")
def get_nurse(client: Client, nurse_user: User) -> Practitioner:
    return create_practitioner(client, nurse_user, role_type="nurse")


@given("patient B", target_fixture="patient")
@given("a patient", target_fixture="patient")
def get_patient_b(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


@given("a back-office staff", target_fixture="staff")
def get_back_office_staff(client: Client) -> Practitioner:
    user = create_user()

    # Assign required role for staff
    firebase_user = auth.get_user_by_email(user.email)
    custom_claims = firebase_user.custom_claims or {}
    current_roles = custom_claims.get("roles", {})
    current_roles["Staff"] = {}
    auth.set_custom_user_claims(user.uid, {"roles": current_roles})

    return create_practitioner(client, user, role_type="staff")


@when(
    parsers.parse("the patient books a free time of the doctor: {days}"),
    target_fixture="appointment",
)
def book_appointment(
    client: Client, practitioner: Practitioner, patient: Patient, days: str
) -> Appointment:
    return create_appointment(client, practitioner, patient, days=int(days))


@when(
    parsers.parse("the patient books a free time of the doctor again: {days}"),
    target_fixture="booked_appointment",
)
def book_another_appointment(
    client: Client, practitioner: Practitioner, patient: Patient, days: str
) -> Appointment:
    return create_appointment(client, practitioner, patient, days=int(days))


@when("an appointment is created by patient B")
def book_new_appointment(
    client: Client, practitioner_a: Practitioner, patient: Patient
):
    return create_appointment(client, practitioner_a, patient)


@when("an appointment is booked for nurse", target_fixture="visit_appointment")
def book_nurse_appointment(
    client: Client, nurse: Practitioner, patient: Patient, practitioner: Practitioner
) -> Appointment:
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    start = (now - timedelta(days=1)).isoformat()
    end = (now - timedelta(days=1) + timedelta(hours=1)).isoformat()

    appointment_data = {
        "practitioner_role_id": nurse.fhir_data["id"],
        "patient_id": patient.fhir_data["id"],
        "start": start,
        "end": end,
        "service_type": "walkin",
        "service": "visit",
        "email_notification": "false",
    }

    token = get_token(practitioner.uid)
    resp = client.post(
        "/appointments",
        data=json.dumps(appointment_data),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 201

    appointment = json.loads(resp.data)
    return appointment


@when("yesterday appointment is created", target_fixture="appointment_yesterday")
def create_yesterday_appointment(
    client: Client, practitioner: Practitioner, patient: Patient
) -> Appointment:
    return create_appointment(client, practitioner, patient, 1)


@when("the patient books another free time of the doctor", target_fixture="appointment")
def book_appointment_for_tomorrow(
    client: Client, practitioner: Practitioner, patient: Patient
):
    # book in tomorrow
    return create_appointment(client, practitioner, patient, days=-1)


@when("a time has been blocked by doctor and then freed", target_fixture="slot")
def create_freed_slot(client: Client, practitioner: Practitioner):
    token = get_token(practitioner.uid)

    target_day = datetime.now() + timedelta(days=7)

    start = datetime(
        target_day.year, target_day.month, target_day.day, 1, 0, 0
    ).replace(tzinfo=timezone.utc)
    end = start + timedelta(minutes=15)

    star_str = start.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    end_str = end.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    slot_data = {
        "start": star_str,
        "end": end_str,
        "status": "busy-unavailable",
        "comment": "Blocked",
    }

    resp = client.post(
        f"/practitioner_roles/{practitioner.fhir_data['id']}/slots",
        data=json.dumps(slot_data),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 200

    slot = json.loads(resp.data)

    resp = client.put(
        f"/slots/{slot['id']}/free",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 204

    return slot


@then("an appointment is created")
def check_appointment(
    practitioner: Practitioner, patient: Patient, appointment: Appointment
):
    assert appointment["description"] == "Booking practitioner role"
    participants = appointment["participant"]
    id_set = set()
    for p in participants:
        id_set.add(p["actor"]["reference"])
    assert id_set == set(
        [
            f"Patient/{patient.fhir_data['id']}",
            f"PractitionerRole/{practitioner.fhir_data['id']}",
        ]
    )

    assert appointment["serviceCategory"][0]["coding"][0]["code"] == "17"
    assert (
        appointment["serviceCategory"][0]["coding"][0]["display"] == "General Practice"
    )
    assert appointment["serviceType"][0]["coding"][0]["code"] == "540"
    assert appointment["serviceType"][0]["coding"][0]["display"] == "Online Service"


@then("no appointment should show up")
def should_return_no_appointment(
    client: Client, patient: Patient, appointment_yesterday: Appointment
):

    url = f'/appointments?actor_id={patient.fhir_data["id"]}'
    token = get_token(patient.uid)
    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    appointments = json.loads(resp.data)["data"]

    found_appointment = False
    for appointment in appointments:
        if appointment["id"] == appointment_yesterday["id"]:
            found_appointment = True
    assert not found_appointment


@then("the period would be set as busy slots")
def available_slots(client: Client, practitioner: Practitioner, patient: Patient):
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    start = (now - timedelta(hours=1)).isoformat()
    end = (now + timedelta(hours=1)).isoformat()

    url = f'/practitioner_roles/{practitioner.fhir_data["id"]}/slots?start={quote(start)}&end={quote(end)}&status=busy'

    token = get_token(patient.uid)
    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    slots = json.loads(resp.data)["data"]
    assert len(slots) == 1
    assert slots[0]["status"] == "busy"


@then("the patient can see his/her own appointment")
def patient_can_see_appointment_with_list_appointment(client: Client, patient: Patient):
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    yesterday = tokyo_timezone.localize(datetime.now() - timedelta(days=1))
    today = tokyo_timezone.localize(datetime.now())
    search_params = {
        "start_date": yesterday.date().isoformat(),
        "end_date": today.date().isoformat(),
        "actor_id": patient.fhir_data["id"],
        "include_patient": True,
    }
    url = f"/appointments?{urlencode(search_params)}"
    token = get_token(patient.uid)
    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    appointments = json.loads(resp.data)["data"]

    found_patient = False
    for participant in appointments[0]["participant"]:
        if participant["actor"]["reference"] == f"Patient/{patient.fhir_data['id']}":
            found_patient = True
            break
    assert found_patient


@then("the doctor can see the appointment being booked")
def doctor_can_see_appointment_being_booked(client, practitioner: Practitioner):
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    yesterday = tokyo_timezone.localize(datetime.now() - timedelta(days=1))

    # using legacy `date` search param here to ensure backward compatibility.
    # for new client code, use `start_date` and `end_date` instead.
    # PS. `patient_can_see_appointment_with_list_appointment` function here is using
    # new search params.
    search_params = {
        "start_date": yesterday.date().isoformat(),
        "actor_id": practitioner.fhir_data["id"],
        "include_encounter": True,
    }
    url = f"/appointments?{urlencode(search_params)}"
    token = get_token(practitioner.uid)
    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})

    resources = json.loads(resp.data)["data"]
    appointments = [
        resource for resource in resources if resource["resourceType"] == "Appointment"
    ]
    encounters = [
        resource for resource in resources if resource["resourceType"] == "Encounter"
    ]

    found_doctor = False
    for participant in appointments[0]["participant"]:
        if (
            participant["actor"]["reference"]
            == f"PractitionerRole/{practitioner.fhir_data['id']}"
        ):
            found_doctor = True
            break
    assert found_doctor

    appointment_id_from_encounter = encounters[0]["appointment"][0]["reference"].split(
        "/"
    )[1]
    assert appointments[0]["id"] == appointment_id_from_encounter


@when(
    "the patients end up not showing up so doctor set the appointment status as no show",
    target_fixture="appointment",
)
def set_appointment_no_show(
    client: Client, practitioner: Practitioner, appointment: Appointment
):
    token = get_token(practitioner.uid)
    resp = client.put(
        f"/appointments/{appointment['id']}/status",
        data=json.dumps({"status": "noshow", "email_notification": "false"}),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    return json.loads(resp.data)


@then("the appointment status is updated as no show")
def check_appointment_status_no_show(appointment):
    assert appointment["status"] == "noshow"


@then("frees the slot")
def frees_the_slot(client: Client, practitioner: Practitioner, patient: Patient):
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    start = (now - timedelta(hours=2)).isoformat()
    end = (now + timedelta(hours=1)).isoformat()

    # Given that we free the slots, it means there should be no unavalable slots
    # anymore. This is done since "free" slots are also pre-populated, and it's
    # hard to identify the freed slots without passing the id through the test.
    url = f'/practitioner_roles/{practitioner.fhir_data["id"]}/slots?start={quote(start)}&end={quote(end)}&not_status=free'

    token = get_token(patient.uid)
    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    slots = json.loads(resp.data)["data"]
    assert len(slots) == 0


@then("patient cannot book an appointment")
def cannot_book_busy_slot(
    client: Client,
    patient: Patient,
    practitioner: Practitioner,
    appointment: Appointment,
):
    appointment_data = {
        "practitioner_role_id": practitioner.fhir_data["id"],
        "patient_id": patient.fhir_data["id"],
        "start": appointment["start"],
        "end": appointment["end"],
        "service_type": "walkin",
        "email_notification": "false",
    }

    token = get_token(patient.uid)
    resp = client.post(
        "/appointments",
        data=json.dumps(appointment_data),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 400


@then("patient cancels the appointment")
def cancel_appointment(
    client: Client,
    patient: Patient,
    appointment: Appointment,
):
    token = get_token(patient.uid)
    resp = client.put(
        f"/appointments/{appointment['id']}/status",
        data=json.dumps({"status": "cancelled", "email_notification": "false"}),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    return json.loads(resp.data)


@then("patient can book an appointment")
def book_canceled_appointment(
    client: Client,
    patient: Patient,
    practitioner: Practitioner,
    appointment: Appointment,
):
    appointment_data = {
        "practitioner_role_id": practitioner.fhir_data["id"],
        "patient_id": patient.fhir_data["id"],
        "start": appointment["start"],
        "end": appointment["end"],
        "service_type": "WALKIN",
        "email_notification": "false",
    }

    token = get_token(patient.uid)
    resp = client.post(
        "/appointments",
        data=json.dumps(appointment_data),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 201


@then("patientA can check biography of practitioner")
def get_practitioner_bio(
    client: Client, patient_a: Patient, practitioner: Practitioner
):
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    yesterday = tokyo_timezone.localize(datetime.now() - timedelta(days=1))

    url = f'/appointments?date={yesterday.date().isoformat()}&actor_id={patient_a.fhir_data["id"]}&include_practitioner=true'
    token = get_token(patient_a.uid)
    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    appointments = json.loads(resp.data)["data"]
    practitioner = next(
        filter(lambda item: item["resourceType"] == "Practitioner", appointments)
    )
    assert practitioner["extension"][0]["url"] == "bio"


@then("the appointment is for nurse visit")
def appopintment_service_type(visit_appointment: Appointment):
    assert visit_appointment["serviceType"][0]["coding"][0]["code"] == "497"


@then("the doctor can see list of appointments")
def get_list_of_appointments(client: Client, patient_a: Patient, user: User):
    practitioner_url = f"/practitioners?email={user.email}"
    token = get_token(patient_a.uid)
    resp = client.get(practitioner_url, headers={"Authorization": f"Bearer {token}"})
    practitioner_id = json.loads(resp.data)["data"][0]["id"]
    appointment_url = f"/appointments?actor_id={practitioner_id}"
    resp_appointment = client.get(
        appointment_url, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp_appointment.status_code == 200


@then("the encounter is created")
def get_encounter(
    client: Client,
    appointment: Appointment,
    patient: Patient,
    practitioner: Practitioner,
):
    return create_encounter(client, practitioner, patient, appointment)


@then("the patient can book at the same start time")
def book_at_start_time_of_freed_slot(
    client: Client, patient: Patient, practitioner: Practitioner
):
    target_day = datetime.now() + timedelta(days=7)

    start = datetime(
        target_day.year, target_day.month, target_day.day, 1, 0, 0
    ).replace(tzinfo=timezone.utc)
    end = start + timedelta(minutes=15)

    star_str = start.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    end_str = end.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    appointment_data = {
        "practitioner_role_id": practitioner.fhir_data["id"],
        "patient_id": patient.fhir_data["id"],
        "start": star_str,
        "end": end_str,
        "service_type": "WALKIN",
        "email_notification": "false",
    }

    token = get_token(patient.uid)
    resp = client.post(
        "/appointments",
        data=json.dumps(appointment_data),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 201


@when("pagination count being 1", target_fixture="count")
def pagination_count_set_to_one():
    return 1


@then("the doctor can see the first appointment page", target_fixture="next_link")
def doctor_can_see_first_appointment_page(
    client, practitioner: Practitioner, count: int
):
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    yesterday = tokyo_timezone.localize(datetime.now() - timedelta(days=1))

    # also checks if include patient and practitioner will work
    search_params = {
        "start_date": yesterday.date().isoformat(),
        "actor_id": practitioner.fhir_data["id"],
        "count": count,
        "include_practitioner": True,
        "include_patient": True,
    }

    url = f"/appointments?{urlencode(search_params)}"
    token = get_token(practitioner.uid)
    resp_raw = client.get(url, headers={"Authorization": f"Bearer {token}"})
    resp = json.loads(resp_raw.data)

    data = resp["data"]
    next_link = resp["next_link"]

    appointments = [d for d in data if d["resourceType"] == "Appointment"]
    assert len(appointments) == count

    patients = [d for d in data if d["resourceType"] == "Patient"]
    assert len(patients) == 1

    practitioners = [d for d in data if d["resourceType"] == "Practitioner"]
    assert len(practitioners) == 1

    assert next_link != ""

    return next_link


@then("the doctor can see the next appointment page")
def doctor_can_see_next_appointment_page(
    client,
    practitioner: Practitioner,
    count: int,
    next_link: str,
):
    search_params = {"next_link": next_link}

    url = f"/appointments?{urlencode(search_params)}"
    token = get_token(practitioner.uid)
    resp_raw = client.get(url, headers={"Authorization": f"Bearer {token}"})
    resp = json.loads(resp_raw.data)

    # last page of the pagination
    assert "next_link" not in resp

    data = resp["data"]
    appointments = [d for d in data if d["resourceType"] == "Appointment"]
    assert len(appointments) == count

    patients = [d for d in data if d["resourceType"] == "Patient"]
    assert len(patients) == 1

    practitioners = [d for d in data if d["resourceType"] == "Practitioner"]
    assert len(practitioners) == 1


@then("the back-office staff can see the booked appointment")
def back_office_staff_check_appointment(
    client, staff: Practitioner, appointment: Appointment
):
    token = get_token(staff.uid)
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    yesterday = tokyo_timezone.localize(datetime.now() - timedelta(days=1))
    tomorrow = tokyo_timezone.localize(datetime.now() + timedelta(days=1))
    search_params = {
        "start_date": yesterday.date().isoformat(),
        "end_date": tomorrow.date().isoformat(),
    }
    appointment_url = f"/appointments?{urlencode(search_params)}"
    resp_appointment = client.get(
        appointment_url, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp_appointment.status_code == 200
    appointments = json.loads(resp_appointment.data)["data"]
    assert (
        len(list(filter(lambda item: item["id"] == appointment["id"], appointments)))
        > 0
    )


@then("the doctor can get booked appointments")
def get_booked_appointments(
    client,
    practitioner: Practitioner,
    appointment: Appointment,
    booked_appointment: Appointment,
):
    token = get_token(practitioner.uid)
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    start = tokyo_timezone.localize(datetime.now() - timedelta(days=5))
    end = tokyo_timezone.localize(datetime.now() + timedelta(days=5))
    search_params = {
        "start_date": start.date().isoformat(),
        "end_date": end.date().isoformat(),
        "actor_id": practitioner.fhir_data["id"],
        "status": "booked",
    }
    appointment_url = f"/appointments?{urlencode(search_params)}"
    resp_appointment = client.get(
        appointment_url, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp_appointment.status_code == 200
    appointments = json.loads(resp_appointment.data)["data"]
    assert (
        len(
            list(
                filter(
                    lambda item: item["id"] == booked_appointment["id"], appointments
                )
            )
        )
        > 0
    )
    assert (
        len(list(filter(lambda item: item["id"] == appointment["id"], appointments)))
        == 0
    )


@then("the doctor can get cancelled appointments")
def get_cancelled_appointments(
    client: Client,
    practitioner: Practitioner,
    booked_appointment: Appointment,
    appointment: Appointment,
):
    token = get_token(practitioner.uid)
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    start = tokyo_timezone.localize(datetime.now() - timedelta(days=5))
    end = tokyo_timezone.localize(datetime.now() + timedelta(days=5))
    search_params = {
        "start_date": start.date().isoformat(),
        "end_date": end.date().isoformat(),
        "status": "cancelled",
        "actor_id": practitioner.fhir_data["id"],
    }
    appointment_url = f"/appointments?{urlencode(search_params)}"
    resp_appointment = client.get(
        appointment_url, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp_appointment.status_code == 200
    appointments = json.loads(resp_appointment.data)["data"]
    assert (
        len(
            list(
                filter(
                    lambda item: item["id"] == booked_appointment["id"], appointments
                )
            )
        )
        == 0
    )
    assert (
        len(list(filter(lambda item: item["id"] == appointment["id"], appointments)))
        > 0
    )


@given("an admin", target_fixture="admin")
def get_admin() -> User:
    user = create_user()
    return make_admin(user)


@when("the admin creates a list", target_fixture="queue")
def admin_create_a_list(client: Client, admin: User) -> dict:
    token = get_token(admin.uid)
    resp = client.post(
        "/lists",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 201

    queue = json.loads(resp.data)
    assert queue["mode"] == "working"
    assert queue["status"] == "current"
    assert queue["title"] == "Patient Queue"
    return queue


@then("the patient can join the lineup", target_fixture="queue")
def patient_join_the_lineup(client: Client, patient: Patient, queue: dict) -> dict:
    token = get_token(patient.uid)
    patient_id = patient.fhir_data["id"]
    resp = client.post(
        f"/lists/{queue['id']}/items/{patient_id}?notification=false",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 201

    queue = json.loads(resp.data)["data"]
    assert len(queue["entry"]) == 1
    assert queue["entry"][0]["item"]["reference"] == f"Patient/{patient_id}"
    return queue


@then("the patinet A can join the lineup", target_fixture="queue")
def patient_A_join_the_lineup(client: Client, patient_a: Patient, queue: dict) -> dict:
    token = get_token(patient_a.uid)
    patient_id = patient_a.fhir_data["id"]
    resp = client.post(
        f"/lists/{queue['id']}/items/{patient_id}?notification=false",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 201

    queue = json.loads(resp.data)["data"]
    assert len(queue["entry"]) == 2
    # assert queue["entry"][0]["item"]["reference"] == f"Patient/{patient_id}"
    return queue


@when(parsers.parse("the doctor B updates the visit type to {visit_type}"))
def update_visit_type_for_doctor_b(
    visit_type: str, client: Client, practitioner_b: Practitioner
):
    jst = pytz.timezone("Asia/Tokyo")
    now = datetime.now().astimezone(jst)
    base_time = now.time().isoformat()
    current_time_plus_ten_mins = (now + timedelta(minutes=10)).time().isoformat()
    role = practitioner_b.fhir_data
    token = get_token(practitioner_b.uid)
    resp = client.put(
        f"/practitioner_roles/{role['id']}",
        data=json.dumps(
            {
                "available_time": [
                    {
                        "daysOfWeek": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
                        "availableStartTime": base_time,
                        "availableEndTime": current_time_plus_ten_mins,
                    },
                ],
                "visit_type": visit_type,
                "role_type": "doctor",
            }
        ),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200


@when(parsers.parse("the doctor updates the visit type to {visit_type}"))
def update_visit_type(visit_type: str, client: Client, practitioner: Practitioner):
    role = practitioner.fhir_data
    token = get_token(practitioner.uid)
    resp = client.put(
        f"/practitioner_roles/{role['id']}",
        data=json.dumps(
            {
                "available_time": [
                    {
                        "daysOfWeek": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
                        "availableStartTime": "00:00:00",
                        "availableEndTime": "23:59:59",
                    },
                ],
                "visit_type": visit_type,
            }
        ),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200


@then("the doctor picks up the appointment", target_fixture="appointment")
def doctor_pick_up_appointment_for_list(
    client: Client,
    practitioner: Practitioner,
    queue: dict,
):
    token = get_token(practitioner.uid)
    practitioner_id = practitioner.practitioner_id
    resp = client.post(
        f"appointments/list/{queue['id']}/practitioner/{practitioner_id}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 201
    return json.loads(resp.data)


@then("the doctor B picks up the appointment")
def doctorB_pick_up_appointment_for_list(
    client: Client, practitioner_b: Practitioner, queue: dict
):
    token = get_token(practitioner_b.uid)
    practitioner_id = practitioner_b.practitioner_id
    resp = client.post(
        f"appointments/list/{queue['id']}/practitioner/{practitioner_id}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 201


@then("the doctor B cannot pick up the appointment")
def doctor_b_pick_up_appointment_for_list(
    client: Client, practitioner_b: Practitioner, queue: dict
):
    token = get_token(practitioner_b.uid)
    practitioner_id = practitioner_b.practitioner_id
    resp = client.post(
        f"appointments/list/{queue['id']}/practitioner/{practitioner_id}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 400


@when("the doctor updates the visit type to walk-in and change avaible time")
def update_visit_type_with_avaible_time(client: Client, practitioner: Practitioner):
    role = practitioner.fhir_data
    token = get_token(practitioner.uid)
    resp = client.put(
        f"/practitioner_roles/{role['id']}",
        data=json.dumps(
            {
                "available_time": [
                    {
                        "daysOfWeek": ["mon", "tue", "wed"],
                        "availableStartTime": "01:00:00",
                        "availableEndTime": "01:05:00",
                    },
                ],
                "visit_type": "walk-in",
                "role_type": "doctor",
            }
        ),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200


@then("the doctor cannot pick up the appointment outside of the avaible time")
def doctor_pick_up_appointment_for_list_outside_of_aviable_time(
    client: Client, practitioner: Practitioner, queue: dict
):
    token = get_token(practitioner.uid)
    practitioner_id = practitioner.practitioner_id
    resp = client.post(
        f"appointments/list/{queue['id']}/practitioner/{practitioner_id}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 400


@then("the patient is no longer on the list")
def patient_not_in_the_list(client: Client, practitioner: Practitioner, queue: dict):
    token = get_token(practitioner.uid)
    resp = client.get(
        f"/lists/{queue['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    resp_list = json.loads(resp.data)["data"]
    assert "entry" not in resp_list


@when("the doctor cancels the appointment", target_fixture="appointment")
def doctor_cancel_appointment(
    client: Client,
    practitioner: Practitioner,
    appointment: Appointment,
):
    token = get_token(practitioner.uid)
    resp = client.put(
        f"/appointments/{appointment['id']}/status",
        data=json.dumps({"status": "cancelled", "email_notification": "false"}),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    return json.loads(resp.data)


@then("the appointment status is updated as cancelled")
def check_appointment_status_cancelled(appointment):
    assert appointment["status"] == "cancelled"
