from firebase_admin import auth
from pytest_bdd import given, scenarios, then

from integtest.blueprints.characters import Patient, Practitioner
from integtest.conftest import Client
from integtest.utils import create_patient, create_practitioner, get_token

scenarios("../features/claims.feature")


@given("a doctor", target_fixture="doctor")
def get_doctor(client: Client):
    return create_practitioner(client)


@given("a patient", target_fixture="patient")
def get_patient(client: Client):
    return create_patient(client)


@then("all patients can be access by the practitioner")
def access_all_patients(client: Client, doctor: Practitioner):
    token = auth.create_custom_token(doctor.uid)
    token = get_token(doctor.uid)

    resp = client.get(
        "/patients",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 200


@then("only one patient can be accessed")
def access_only_one_patient(client: Client, patient: Patient):
    token = auth.create_custom_token(patient.uid)
    token = get_token(patient.uid)

    all_resp = client.get(
        "/patients",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert all_resp.status_code == 401

    patient_resp = client.get(
        f"/patients/{patient.fhir_data['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert patient_resp.status_code == 200
