import json
import pytz
import uuid

from pytest_bdd import scenarios, given, when, then
from firebase_admin import auth
from datetime import datetime, timedelta

from fhir.resources import construct_fhir_element
from adapters.fhir_store import ResourceClient
from integtest.utils import get_token
from urllib.parse import quote

scenarios("../features/book_appointments.feature")


class Patient:
    def __init__(self, firebase_uid, patient):
        self.uid = firebase_uid
        self.fhir_data = patient


class Doctor:
    def __init__(self, firebase_uid, practitioner_role):
        self.uid = firebase_uid
        self.fhir_data = practitioner_role


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

    practitioner_data = {
        "resourceType": "Practitioner",
        "active": True,
        "name": [{"family": "Test", "given": ["Cool"], "prefix": ["Dr"]}],
    }

    practitioner = construct_fhir_element("Practitioner", practitioner_data)
    practitioner = ResourceClient().create_resource(practitioner)

    role = {
        "resourceType": "PractitionerRole",
        "active": True,
        "period": {"start": "2001-01-01", "end": "2099-03-31"},
        "practitioner": {
            "reference": f"Practitioner/{practitioner.id}",
            "display": "Dr Cool in test",
        },
        "availableTime": [
            {
                "daysOfWeek": ["mon", "tue", "wed"],
                "availableStartTime": "09:00:00",
                "availableEndTime": "16:30:00",
            },
            {
                "daysOfWeek": ["thu", "fri"],
                "availableStartTime": "09:00:00",
                "availableEndTime": "12:00:00",
            },
        ],
        "notAvailable": [
            {
                "description": "Adam will be on extended leave during May 2017",
                "during": {"start": "2017-05-01", "end": "2017-05-20"},
            }
        ],
        "availabilityExceptions": "Adam is generally unavailable on public holidays and during the Christmas/New Year break",
    }

    resp = client.post(
        "/practitioner_roles",
        data=json.dumps(role),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 202

    doctor_role = json.loads(resp.data)["practitioner_role"]
    return Doctor(doctor.uid, doctor_role)


@given("a patient", target_fixture="patient")
def get_patient(client):
    patient = auth.create_user(
        email=f"patient-{uuid.uuid4()}@fake.umed.jp",
        email_verified=True,
        password=f"password-{uuid.uuid4()}",
        display_name="Test Doctor",
        disabled=False,
    )
    token = get_token(patient.uid)

    patient_fhir_data = {
        "resourceType": "Patient",
        "id": "example",
        "active": True,
        "name": [
            {"use": "official", "family": "Chalmers", "given": ["Peter", "James"]}
        ],
        "gender": "male",
        "birthDate": "1990-01-01",
        "deceasedBoolean": False,
        "address": [
            {
                "use": "home",
                "type": "both",
                "text": "534 Erewhon St PeasantVille, Rainbow, Vic  3999",
                "line": ["534 Erewhon St"],
                "city": "PleasantVille",
                "district": "Rainbow",
                "state": "Vic",
                "postalCode": "3999",
                "period": {"start": "1974-12-25"},
            }
        ],
    }
    resp = client.post(
        "/patients",
        data=json.dumps(patient_fhir_data),
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
