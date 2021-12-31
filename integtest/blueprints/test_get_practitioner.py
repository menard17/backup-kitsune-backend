import json

from pytest_bdd import given, scenarios, then

from integtest.characters import Patient, Practitioner
from integtest.conftest import Client
from integtest.utils import create_patient, create_practitioner, create_user, get_token

scenarios("../features/get_practitioner.feature")


@given("a doctor", target_fixture="doctor")
def get_doctor(client: Client):
    user = create_user()
    return create_practitioner(client, user)


@given("a nurse", target_fixture="nurse")
def get_nurse(client: Client) -> Practitioner:
    user = create_user()
    return create_practitioner(client, user, ["en"], role_type="nurse")


@given("a patient", target_fixture="patient")
def get_patient_a(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


@then("the patient can fetch all doctors info")
def get_doctor_details(
    client: Client, patient: Patient, doctor: Practitioner, nurse: Practitioner
):
    token = get_token(patient.uid)
    resp = client.get(
        "/practitioners?role_type=doctor",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    filtered_doctor = next(
        filter(lambda item: item["id"] == doctor.practitioner_id, data["data"])
    )
    assert filtered_doctor["id"] == doctor.practitioner_id
    assert filtered_doctor["extension"][0]["valueString"] == "My background ..."
    size_nurse = len(
        list(filter(lambda item: item["id"] == nurse.practitioner_id, data["data"]))
    )
    assert size_nurse == 0


@then("the patient can fetch all nurses info")
def get_nurse_details(
    client: Client, patient: Patient, doctor: Practitioner, nurse: Practitioner
):
    token = get_token(patient.uid)
    resp = client.get(
        "/practitioners?role_type=nurse",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    filtered_doctor_size = len(
        list(filter(lambda item: item["id"] == doctor.practitioner_id, data["data"]))
    )
    assert filtered_doctor_size == 0
    filtered_nurse = next(
        filter(lambda item: item["id"] == nurse.practitioner_id, data["data"])
    )
    assert filtered_nurse["extension"][0]["valueString"] == "My background ..."
