import json
from datetime import datetime, timedelta

import pytz
from firebase_admin import auth
from pytest_bdd import given, scenarios, then, when

from integtest.blueprints.characters import (
    Appointment,
    Encounter,
    Patient,
    Practitioner,
)
from integtest.conftest import Client
from integtest.utils import create_patient, create_practitioner, get_token

scenarios("../features/create_encounter.feature")


def get_encounter_data(
    patient_id: str, practitioner_id: str, appointment_id: str
) -> dict:
    encounter = {
        "resourceType": "Encounter",
        "status": "in-progress",
        "appointment": [{"reference": f"Appointment/{appointment_id}"}],
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "HH",
            "display": "home health",
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "participant": [
            {
                "individual": {
                    "reference": f"Practitioner/{practitioner_id}",
                },
            }
        ],
    }
    return encounter


@given("a doctor", target_fixture="doctor")
def get_doctor(client: Client):
    return create_practitioner(client)


@given("patient A", target_fixture="patientA")
def get_patient_a(client: Client):
    return create_patient(client)


@given("patient B", target_fixture="patientB")
def get_patient_b(client: Client):
    return create_patient(client)


@when("patient A makes an appointment", target_fixture="appointment")
def book_appointment(client: Client, doctor: Practitioner, patientA: Patient):
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
def create_encounter(
    client: Client, doctor: Practitioner, patientA: Patient, appointment: Appointment
):
    token = auth.create_custom_token(doctor.uid)
    token = get_token(doctor.uid)

    resp = client.post(
        f"/patients/{patientA.fhir_data['id']}/encounters",
        data=json.dumps(
            get_encounter_data(
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
def start_encounter(
    client, doctor: Practitioner, patientA: Patient, encounter: Encounter
):
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
    assert json.loads(resp.data)["data"][0]["status"] == "in-progress"


@then("the doctor can finish the encounter")
def finish_encounter(
    client: Client, doctor: Practitioner, patientA: Patient, encounter: Encounter
):
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

    assert json.loads(get_resp.data)["data"][0]["status"] == "finished"


@then("patient A can see the encounter but patient B cannnot see the encounter")
def permission_for_patient(
    client: Client, patientA: Patient, patientB: Patient, encounter: Encounter
):
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
    assert json.loads(resp_a.data)["data"][0]["id"] == encounter["id"]

    resp_b = client.get(
        f"/patients/{patientA.fhir_data['id']}/encounters",
        headers={"Authorization": f"Bearer {token_b}"},
        content_type="application/json",
    )

    assert resp_b.status_code == 401


@then("patient A cannot change the status of encounter")
def cannot_update_status(client: Client, patientA: Patient, encounter: Encounter):
    token = auth.create_custom_token(patientA.uid)
    token = get_token(patientA.uid)
    resp = client.patch(
        f"/patients/{patientA.fhir_data['id']}/encounters/{encounter['id']}?status=finished",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 401


@then("patient A can see encounter by appointment id")
def get_encounter_by_appointment_id(
    client: Client, patientA: Patient, appointment: Appointment, encounter: Encounter
):
    token = auth.create_custom_token(patientA.uid)
    token = get_token(patientA.uid)
    resp = client.get(
        f"/patients/{patientA.fhir_data['id']}/encounters?appointment_id={appointment['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    assert json.loads(resp.data)["data"][0]["id"] == encounter["id"]
