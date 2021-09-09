import json
import uuid
from datetime import datetime, timedelta
from urllib.parse import quote

import pytz
from firebase_admin import auth
from pytest_bdd import given, scenarios, then, when

from integtest.blueprints.characters import Doctor, Patient
from integtest.blueprints.fhir_input_constants import PATIENT_DATA, PRACTITIONER_DATA
from integtest.blueprints.helper import get_role
from integtest.utils import get_token

scenarios("../features/book_appointments.feature")


@given("a doctor", target_fixture="doctor")
def get_doctor(client):
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

    assert practitioner_roles_resp.status_code == 202

    doctor_role = json.loads(practitioner_roles_resp.data)["practitioner_role"]
    return Doctor(doctor.uid, doctor_role)


@given("a patient", target_fixture="patient")
def get_patient(client):
    patient = auth.create_user(
        email=f"patient-{uuid.uuid4()}@fake.umed.jp",
        email_verified=True,
        password=f"password-{uuid.uuid4()}",
        display_name="Test Patient",
        disabled=False,
    )
    token = get_token(patient.uid)

    resp = client.post(
        "/patients",
        data=json.dumps(PATIENT_DATA),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 202
    return Patient(patient.uid, json.loads(resp.data))


@when("the patient books a free time of the doctor", target_fixture="appointment")
def book_appointment(client, doctor, patient):
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    start = now.isoformat()
    end = (now + timedelta(hours=1)).isoformat()

    appointment_data = {
        "practitioner_role_id": doctor.fhir_data["id"],
        "patient_id": patient.fhir_data["id"],
        "start": start,
        "end": end,
    }

    token = get_token(patient.uid)
    resp = client.post(
        "/appointments",
        data=json.dumps(appointment_data),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 202

    appointment = json.loads(resp.data)
    return appointment


@then("an appointment is created")
def check_appointment(appointment, patient, doctor):
    assert appointment["description"] == "Booking practitioner role"

    participants = appointment["participant"]
    id_set = set()
    for p in participants:
        id_set.add(p["actor"]["reference"])
    assert id_set == set(
        [
            f"Patient/{patient.fhir_data['id']}",
            f"PractitionerRole/{doctor.fhir_data['id']}",
        ]
    )

    assert appointment["serviceCategory"][0]["coding"][0]["code"] == "17"
    assert (
        appointment["serviceCategory"][0]["coding"][0]["display"] == "General Practice"
    )
    assert appointment["serviceType"][0]["coding"][0]["code"] == "540"
    assert appointment["serviceType"][0]["coding"][0]["display"] == "Online Service"


@then("the period would be set as busy slots")
def available_slots(client, patient, doctor):
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    start = (now - timedelta(hours=1)).isoformat()
    end = (now + timedelta(hours=1)).isoformat()

    url = f'/practitioner_roles/{doctor.fhir_data["id"]}/slots?start={quote(start)}&end={quote(end)}&status=busy'

    token = get_token(patient.uid)
    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    slots = json.loads(resp.data)["data"]
    assert len(slots) == 1
    assert slots[0]["status"] == "busy"


@then("the patient can see his/her own appointment")
def patient_can_see_appointment_with_list_appointment(client, patient):
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    yesterday = tokyo_timezone.localize(datetime.now() - timedelta(days=1))

    url = f'/appointments?date={yesterday.date().isoformat()}&actor_id={patient.fhir_data["id"]}'
    token = get_token(patient.uid)
    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})

    appointments = json.loads(resp.data)["entry"]

    found_patient = False
    for participant in appointments[0]["resource"]["participant"]:
        if participant["actor"]["reference"] == f"Patient/{patient.fhir_data['id']}":
            found_patient = True
            break
    assert found_patient


@then("the doctor can see the appointment being booked")
def doctor_can_see_appointment_being_booked(client, doctor):
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())

    url = (
        f'/appointments?date={now.date().isoformat()}&actor_id={doctor.fhir_data["id"]}'
    )
    token = get_token(doctor.uid)
    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})

    appointments = json.loads(resp.data)["entry"]

    found_patient = False
    for participant in appointments[0]["resource"]["participant"]:
        if (
            participant["actor"]["reference"]
            == f"PractitionerRole/{doctor.fhir_data['id']}"
        ):
            found_patient = True
            break
    assert found_patient


@when(
    "the patients end up not showing up so doctor set the appointment status as no show",
    target_fixture="appointment",
)
def set_appointment_no_show(client, doctor, appointment):
    token = get_token(doctor.uid)
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
def frees_the_slot(client, patient, doctor):
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    start = (now - timedelta(hours=1)).isoformat()
    end = (now + timedelta(hours=1)).isoformat()

    url = f'/practitioner_roles/{doctor.fhir_data["id"]}/slots?start={quote(start)}&end={quote(end)}&status=free'

    token = get_token(patient.uid)
    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    slots = json.loads(resp.data)["data"]
    assert len(slots) == 1
    assert slots[0]["status"] == "free"
