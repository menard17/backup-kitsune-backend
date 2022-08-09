import json
from datetime import datetime, timedelta

import pytz
from firebase_admin import auth
from pytest_bdd import given, scenarios, then, when

from integtest.characters import Appointment, Encounter, Patient, Practitioner
from integtest.conftest import Client
from integtest.utils import (
    create_appointment,
    create_encounter,
    create_patient,
    create_practitioner,
    create_user,
    get_token,
)

scenarios("../features/create_encounter.feature")


@given("a doctor", target_fixture="practitioner")
def get_doctor(client: Client):
    user = create_user()
    return create_practitioner(client, user)


@given("patient A", target_fixture="patient_a")
def get_patient_a(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


@given("patient B", target_fixture="patient_b")
def get_patient_b(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


@when("patient A makes an appointment", target_fixture="appointment")
def book_appointment(client: Client, practitioner: Practitioner, patient_a: Patient):
    return create_appointment(client, practitioner, patient_a)


@when("patient A makes another appointment", target_fixture="another_appointment")
def book_anouter_appointment(
    client: Client, practitioner: Practitioner, patient_a: Patient
):
    return create_appointment(client, practitioner, patient_a, days=5)


@when("the doctor creates an encounter", target_fixture="encounter")
def get_encounter(
    client: Client,
    practitioner: Practitioner,
    patient_a: Patient,
    appointment: Appointment,
):
    return create_encounter(client, practitioner, patient_a, appointment)


@when("the doctor creates another encounter", target_fixture="another_encounter")
def get_another_encounter(
    client: Client,
    practitioner: Practitioner,
    patient_a: Patient,
    another_appointment: Appointment,
):
    return create_encounter(client, practitioner, patient_a, another_appointment)


@when("the doctor starts the encounter")
def start_encounter(
    client, practitioner: Practitioner, patient_a: Patient, encounter: Encounter
):
    token = get_token(practitioner.uid)
    resp_patch = client.patch(
        f"/patients/{patient_a.fhir_data['id']}/encounters/{encounter['id']}?status=in-progress",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp_patch.status_code == 200

    resp = client.get(
        f"/patients/{patient_a.fhir_data['id']}/encounters/{encounter['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 200
    assert json.loads(resp.data)["data"][0]["status"] == "in-progress"


@then("the doctor can finish the encounter")
def finish_encounter(
    client: Client, practitioner: Practitioner, patient_a: Patient, encounter: Encounter
):
    token = get_token(practitioner.uid)
    resp = client.patch(
        f"/patients/{patient_a.fhir_data['id']}/encounters/{encounter['id']}?status=finished",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200

    get_resp = client.get(
        f"/patients/{patient_a.fhir_data['id']}/encounters/{encounter['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert get_resp.status_code == 200

    assert json.loads(get_resp.data)["data"][0]["status"] == "finished"


@then("patient A can see the encounter but patient B cannnot see the encounter")
def permission_for_patient(
    client: Client, patient_a: Patient, patient_b: Patient, encounter: Encounter
):
    token_a = auth.create_custom_token(patient_a.uid)
    token_a = get_token(patient_a.uid)

    token_b = auth.create_custom_token(patient_b.uid)
    token_b = get_token(patient_b.uid)

    resp_a = client.get(
        f"/patients/{patient_a.fhir_data['id']}/encounters",
        headers={"Authorization": f"Bearer {token_a}"},
        content_type="application/json",
    )

    assert resp_a.status_code == 200
    assert json.loads(resp_a.data)["data"][0]["id"] == encounter["id"]

    resp_b = client.get(
        f"/patients/{patient_a.fhir_data['id']}/encounters",
        headers={"Authorization": f"Bearer {token_b}"},
        content_type="application/json",
    )

    assert resp_b.status_code == 401


@then("patient A cannot change the status of encounter")
def cannot_update_status(client: Client, patient_a: Patient, encounter: Encounter):
    token = get_token(patient_a.uid)
    resp = client.patch(
        f"/patients/{patient_a.fhir_data['id']}/encounters/{encounter['id']}?status=finished",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 401


@then("patient A can see encounter by appointment id")
def get_encounter_by_appointment_id(
    client: Client, patient_a: Patient, appointment: Appointment, encounter: Encounter
):
    token = get_token(patient_a.uid)
    resp = client.get(
        f"/patients/{patient_a.fhir_data['id']}/encounters?appointment_id={appointment['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    assert json.loads(resp.data)["data"][0]["id"] == encounter["id"]


@then("appointment status is changed to fulfilled")
def get_appointment_status(client: Client, patient_a: Patient):
    token = get_token(patient_a.uid)
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    yesterday = tokyo_timezone.localize(datetime.now() - timedelta(days=1))

    url = f'/appointments?date={yesterday.date().isoformat()}&actor_id={patient_a.fhir_data["id"]}'
    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})

    appointments = json.loads(resp.data)["data"]
    assert appointments[0]["status"] == "fulfilled"


@then("the doctor cannot create another encounter for the same appointment")
def create_another_(
    client: Client,
    practitioner: Practitioner,
    patient_a: Patient,
    appointment: Appointment,
):
    token = get_token(practitioner.uid)
    resp = client.post(
        f"/patients/{patient_a.fhir_data['id']}/encounters",
        data=json.dumps(
            {
                "patient_id": patient_a.fhir_data["id"],
                "role_id": practitioner.fhir_data["id"],
                "appointment_id": appointment["id"],
            }
        ),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 400


@then("the encounter can be fetched by id")
def get_encounter_by_id(
    client: Client,
    practitioner: Practitioner,
    patient_a: Patient,
    encounter: Encounter,
    another_encounter: Encounter,
):
    token = get_token(practitioner.uid)
    resp = client.get(
        f"/patients/{patient_a.fhir_data['id']}/encounters/{encounter['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert json.loads(resp.data)["data"][0]["id"] == encounter["id"]

    resp = client.get(
        f"/patients/{patient_a.fhir_data['id']}/encounters/{another_encounter['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert json.loads(resp.data)["data"][0]["id"] == another_encounter["id"]
