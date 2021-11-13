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
from integtest.utils import (
    create_appointment,
    create_encounter,
    create_patient,
    create_practitioner,
    get_token,
)

scenarios("../features/create_encounter.feature")


@given("a doctor", target_fixture="practitioner")
def get_doctor(client: Client):
    return create_practitioner(client)


@given("patient A", target_fixture="patientA")
def get_patient_a(client: Client):
    return create_patient(client)


@given("patient B", target_fixture="patientB")
def get_patient_b(client: Client):
    return create_patient(client)


@when("patient A makes an appointment", target_fixture="appointment")
def book_appointment(client: Client, practitioner: Practitioner, patientA: Patient):
    return create_appointment(client, practitioner, patientA)


@when("the doctor creates an encounter", target_fixture="encounter")
def get_encounter(
    client: Client,
    practitioner: Practitioner,
    patientA: Patient,
    appointment: Appointment,
):
    return create_encounter(client, practitioner, patientA, appointment)


@when("the doctor starts the encounter")
def start_encounter(
    client, practitioner: Practitioner, patientA: Patient, encounter: Encounter
):
    token = auth.create_custom_token(practitioner.uid)
    token = get_token(practitioner.uid)
    resp_patch = client.patch(
        f"/patients/{patientA.fhir_data['id']}/encounters/{encounter['id']}?status=in-progress",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp_patch.status_code == 200

    resp = client.get(
        f"/patients/{patientA.fhir_data['id']}/encounters/{encounter['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 200
    assert json.loads(resp.data)["data"][0]["status"] == "in-progress"


@then("the doctor can finish the encounter")
def finish_encounter(
    client: Client, practitioner: Practitioner, patientA: Patient, encounter: Encounter
):
    token = auth.create_custom_token(practitioner.uid)
    token = get_token(practitioner.uid)
    resp = client.patch(
        f"/patients/{patientA.fhir_data['id']}/encounters/{encounter['id']}?status=finished",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200

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


@then("appointment status is changed to fulfilled")
def get_appointment_status(client: Client, patientA: Patient):
    token = auth.create_custom_token(patientA.uid)
    token = get_token(patientA.uid)
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    yesterday = tokyo_timezone.localize(datetime.now() - timedelta(days=1))

    url = f'/appointments?date={yesterday.date().isoformat()}&actor_id={patientA.fhir_data["id"]}'
    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})

    appointments = json.loads(resp.data)["data"]
    assert appointments[0]["status"] == "fulfilled"
