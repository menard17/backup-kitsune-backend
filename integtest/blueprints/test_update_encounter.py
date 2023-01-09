import json

from pytest_bdd import given, scenarios, then, when

from integtest.characters import Patient, Practitioner, Appointment, Encounter
from integtest.conftest import Client
from integtest.utils import (
    create_patient,
    create_practitioner,
    create_user,
    get_token,
    create_encounter,
    create_appointment
)

scenarios("../features/update_encounter.feature")


@given("a patient", target_fixture="patient")
def get_patient(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


@given("a practitioner", target_fixture="practitioner")
def get_practitioner(client: Client) -> Practitioner:
    user = create_user()
    return create_practitioner(client, user)


@when("patient makes an appointment", target_fixture="appointment")
def book_appointment(client: Client, practitioner: Practitioner, patient: Patient):
    return create_appointment(client, practitioner, patient)


@when("the doctor creates an encounter", target_fixture="encounter")
def get_encounter(
    client: Client,
    practitioner: Practitioner,
    patient: Patient,
    appointment: Appointment,
):
    return create_encounter(client, practitioner, patient, appointment)


@when("the doctor cancels the encounter")
def cancel_encounter(
    client: Client, practitioner: Practitioner, patient: Patient, encounter: Encounter
):
    token = get_token(practitioner.uid)
    resp = client.patch(
        f"/patients/{patient.fhir_data['id']}/encounters/{encounter['id']}?status=cancelled",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200

    get_resp = client.get(
        f"/patients/{patient.fhir_data['id']}/encounters/{encounter['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert get_resp.status_code == 200

    assert json.loads(get_resp.data)["data"][0]["status"] == "cancelled"


@then("account should be inactivated")
def account_cancelled(
    client: Client, practitioner: Practitioner, patient: Patient, encounter: Encounter
):
    token = get_token(practitioner.uid)
    account_id = encounter["account"][0]["reference"].split("/")[1]

    get_resp = client.get(
        f"/accounts/{account_id}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    account_status = json.loads(json.loads(get_resp.data)["data"])["status"]

    assert get_resp.status_code == 200
    assert account_status == "inactive"
