from pytest_bdd import given, scenarios, then

from integtest.characters import Patient, Practitioner
from integtest.conftest import Client
from integtest.utils import create_patient, create_practitioner, create_user, get_token

scenarios("../features/claims.feature")


@given("a doctor", target_fixture="practitioner")
def get_doctor(client: Client) -> Practitioner:
    user = create_user()
    return create_practitioner(client, user)


@given("a patient", target_fixture="patient")
def get_patient(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


@then("all patients can be access by the practitioner")
def access_all_patients(client: Client, practitioner: Practitioner):
    token = get_token(practitioner.uid)

    resp = client.get(
        "/patients",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 200


@then("only one patient can be accessed")
def access_only_one_patient(client: Client, patient: Patient):
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
