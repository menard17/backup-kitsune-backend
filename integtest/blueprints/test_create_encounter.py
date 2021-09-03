import json
import uuid
from datetime import datetime, timedelta

import pytz
from firebase_admin import auth
from pytest_bdd import given, scenarios, then, when

from integtest.blueprints.characters import Doctor, Patient
from integtest.blueprints.fhir_input_constants import PATIENT_DATA, PRACTITIONER_DATA
from integtest.blueprints.helper import get_encounter, get_role
from integtest.utils import get_token

scenarios("../features/create_encounter.feature")


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
    practitioner = json.loads(practitioner_resp.data.decode("utf-8"))
    practitioner_roles_resp = client.post(
        "/practitioner_roles",
        data=json.dumps(get_role(practitioner["id"])),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert practitioner_roles_resp.status_code == 202

    doctor_role = json.loads(practitioner_roles_resp.data)["practitioner_role"]
    return Doctor(doctor.uid, doctor_role, practitioner)


@given("patient A", target_fixture="patientA")
def get_patient_a(client):
    patient = auth.create_user(
        email=f"patient-{uuid.uuid4()}@fake.umed.jp",
        email_verified=True,
        password=f"password-{uuid.uuid4()}",
        display_name="Patient A",
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


@given("patient B", target_fixture="patientB")
def get_patient_b(client):
    patient = auth.create_user(
        email=f"patient-{uuid.uuid4()}@fake.umed.jp",
        email_verified=True,
        password=f"password-{uuid.uuid4()}",
        display_name="Patient B",
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


@when("patient A makes an appointment", target_fixture="appointment")
def book_appointment(client, doctor, patientA):
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    start = now.isoformat()
    end = (now + timedelta(hours=1)).isoformat()

    appointment_data = {
        "practitioner_role_id": doctor.fhir_data["id"],
        "patient_id": patientA.fhir_data["id"],
        "start": start,
        "end": end,
    }

    token = get_token(patientA.uid)
    resp = client.post(
        "/appointments",
        data=json.dumps(appointment_data),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 202

    appointment = json.loads(resp.data)
    return appointment


@when("the doctor creates an encounter", target_fixture="encounter")
def create_encounter(appointment, patientA: Patient, doctor: Doctor, client):
    token = auth.create_custom_token(doctor.uid)
    token = get_token(doctor.uid)

    resp = client.post(
        f"/patients/{patientA.fhir_data['id']}/encounters",
        data=json.dumps(
            get_encounter(
                patientA.fhir_data["id"],
                doctor.fhir_practitioner_data["id"],
                appointment["id"],
            )
        ),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 200

    encounter = json.loads(resp.data)
    return encounter


@when("the doctor starts the encounter")
def start_encounter(encounter, doctor: Doctor, client, patientA: Patient):
    token = auth.create_custom_token(doctor.uid)
    token = get_token(doctor.uid)
    resp_patch = client.patch(
        f"/patients/{patientA.fhir_data['id']}/encounters/{encounter['id']}?status=in-progress",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp_patch.status_code == 202

    resp = client.get(
        f"/patients/{patientA.fhir_data['id']}/encounters/{encounter['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 200
    assert json.loads(resp.data)["data"]["status"] == "in-progress"


@then("the doctor can finish the encounter")
def finish_encounter(encounter, doctor: Doctor, client, patientA: Patient):
    token = auth.create_custom_token(doctor.uid)
    token = get_token(doctor.uid)
    resp = client.patch(
        f"/patients/{patientA.fhir_data['id']}/encounters/{encounter['id']}?status=finished",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 202

    get_resp = client.get(
        f"/patients/{patientA.fhir_data['id']}/encounters/{encounter['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert get_resp.status_code == 200
    assert json.loads(get_resp.data)["data"]["status"] == "finished"


@then("patient A can see the encounter but patient B cannnot see the encounter")
def permission_for_patient(patientA: Patient, patientB: Patient, client):
    token_a = auth.create_custom_token(patientA.uid)
    token_a = get_token(patientA.uid)

    token_b = auth.create_custom_token(patientB.uid)
    token_b = get_token(patientB.uid)

    resp_a = client.get(
        f"/patients/{patientA.fhir_data['id']}/encounters",
        headers={"Authorization": f"Bearer {token_a}"},
        content_type="application/json",
    )

    assert resp_a.status_code == 200

    resp_b = client.get(
        f"/patients/{patientA.fhir_data['id']}/encounters",
        headers={"Authorization": f"Bearer {token_b}"},
        content_type="application/json",
    )

    assert resp_b.status_code == 401


@then("patient A cannot change the status of encounter")
def cannot_update_status(patientA: Patient, encounter, client):
    token = auth.create_custom_token(patientA.uid)
    token = get_token(patientA.uid)
    resp = client.patch(
        f"/patients/{patientA.fhir_data['id']}/encounters/{encounter['id']}?status=finished",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 401
