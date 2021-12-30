import json
from datetime import datetime, timedelta
from urllib.parse import quote

import pytz
from pytest_bdd import scenarios, then, when
from pytest_bdd.steps import given

from integtest.characters import Appointment, Patient, Practitioner
from integtest.conftest import Client
from integtest.utils import (
    create_appointment,
    create_patient,
    create_practitioner,
    create_user,
    get_token,
)

scenarios("../features/book_appointments.feature")


@given("a doctor", target_fixture="practitioner")
def get_doctor(client: Client):
    user = create_user()
    return create_practitioner(client, user)


@given("patientA", target_fixture="patientA")
def get_patientA(client: Client):
    user = create_user()
    return create_patient(client, user)


@given("patientB", target_fixture="patientB")
def get_patientB(client: Client):
    user = create_user()
    return create_patient(client, user)


@when("the patient books a free time of the doctor", target_fixture="appointment")
def book_appointment(client: Client, practitioner: Practitioner, patientA: Patient):
    return create_appointment(client, practitioner, patientA)


@when("yesterday appointment is created", target_fixture="appointment_yesterday")
def create_yesterday_appointment(
    client: Client, practitioner: Practitioner, patientA: Patient
):
    return create_appointment(client, practitioner, patientA, 1)


@then("an appointment is created")
def check_appointment(
    practitioner: Practitioner, patientA: Patient, appointment: Appointment
):
    assert appointment["description"] == "Booking practitioner role"
    participants = appointment["participant"]
    id_set = set()
    for p in participants:
        id_set.add(p["actor"]["reference"])
    assert id_set == set(
        [
            f"Patient/{patientA.fhir_data['id']}",
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
    client: Client, patientA: Patient, appointment_yesterday: Appointment
):

    url = f'/appointments?actor_id={patientA.fhir_data["id"]}'
    token = get_token(patientA.uid)
    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    appointments = json.loads(resp.data)["data"]

    found_appointment = False
    for appointment in appointments:
        if appointment["id"] == appointment_yesterday["id"]:
            found_appointment = True
    assert not found_appointment


@then("the period would be set as busy slots")
def available_slots(client: Client, practitioner: Practitioner, patientA: Patient):
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    start = (now - timedelta(hours=1)).isoformat()
    end = (now + timedelta(hours=1)).isoformat()

    url = f'/practitioner_roles/{practitioner.fhir_data["id"]}/slots?start={quote(start)}&end={quote(end)}&status=busy'

    token = get_token(patientA.uid)
    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    slots = json.loads(resp.data)["data"]
    assert len(slots) == 1
    assert slots[0]["status"] == "busy"


@then("the patient can see his/her own appointment")
def patient_can_see_appointment_with_list_appointment(
    client: Client, patientA: Patient
):
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    yesterday = tokyo_timezone.localize(datetime.now() - timedelta(days=1))

    url = f'/appointments?date={yesterday.date().isoformat()}&actor_id={patientA.fhir_data["id"]}'
    token = get_token(patientA.uid)
    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    appointments = json.loads(resp.data)["data"]

    found_patient = False
    for participant in appointments[0]["participant"]:
        if participant["actor"]["reference"] == f"Patient/{patientA.fhir_data['id']}":
            found_patient = True
            break
    assert found_patient


@then("the doctor can see the appointment being booked")
def doctor_can_see_appointment_being_booked(client, practitioner: Practitioner):
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    yesterday = tokyo_timezone.localize(datetime.now() - timedelta(days=1))

    url = f'/appointments?date={yesterday.date().isoformat()}&actor_id={practitioner.fhir_data["id"]}'
    token = get_token(practitioner.uid)
    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})

    appointments = json.loads(resp.data)["data"]

    found_patient = False
    for participant in appointments[0]["participant"]:
        if (
            participant["actor"]["reference"]
            == f"PractitionerRole/{practitioner.fhir_data['id']}"
        ):
            found_patient = True
            break
    assert found_patient


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
        data=json.dumps({"status": "noshow"}),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    return json.loads(resp.data)


@then("the appointment status is updated as no show")
def check_appointment_status_no_show(appointment):
    assert appointment["status"] == "noshow"


@then("frees the slot")
def frees_the_slot(client: Client, practitioner: Practitioner, patientA: Patient):
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    start = (now - timedelta(hours=2)).isoformat()
    end = (now + timedelta(hours=1)).isoformat()

    url = f'/practitioner_roles/{practitioner.fhir_data["id"]}/slots?start={quote(start)}&end={quote(end)}&status=free'

    token = get_token(patientA.uid)
    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    slots = json.loads(resp.data)["data"]
    assert len(slots) == 1
    assert slots[0]["status"] == "free"


@then("patientB cannot book an appointment")
def cannot_book_busy_slot(
    client: Client,
    patientB: Patient,
    practitioner: Practitioner,
    appointment: Appointment,
):
    appointment_data = {
        "practitioner_role_id": practitioner.fhir_data["id"],
        "patient_id": patientB.fhir_data["id"],
        "start": appointment["start"],
        "end": appointment["end"],
        "service_type": "WALKIN",
    }

    token = get_token(patientB.uid)
    resp = client.post(
        "/appointments",
        data=json.dumps(appointment_data),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 400


@then("patientA cancels the appointment")
def cancel_appointment(
    client: Client,
    patientA: Patient,
    appointment: Appointment,
):
    token = get_token(patientA.uid)
    resp = client.put(
        f"/appointments/{appointment['id']}/status",
        data=json.dumps({"status": "cancelled"}),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    return json.loads(resp.data)


@then("patientB can book an appointment")
def book_canceled_appointment(
    client: Client,
    patientB: Patient,
    practitioner: Practitioner,
    appointment: Appointment,
):
    appointment_data = {
        "practitioner_role_id": practitioner.fhir_data["id"],
        "patient_id": patientB.fhir_data["id"],
        "start": appointment["start"],
        "end": appointment["end"],
        "service_type": "WALKIN",
    }

    token = get_token(patientB.uid)
    resp = client.post(
        "/appointments",
        data=json.dumps(appointment_data),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 201


@then("patientA can check biography of practitioner")
def get_practitioner_bio(client: Client, patientA: Patient, practitioner: Practitioner):
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    yesterday = tokyo_timezone.localize(datetime.now() - timedelta(days=1))

    url = f'/appointments?date={yesterday.date().isoformat()}&actor_id={patientA.fhir_data["id"]}&include_practitioner=true'
    token = get_token(patientA.uid)
    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    appointments = json.loads(resp.data)["data"]
    practitioner = next(
        filter(lambda item: item["resourceType"] == "Practitioner", appointments)
    )
    assert practitioner["extension"][0]["url"] == "bio"
