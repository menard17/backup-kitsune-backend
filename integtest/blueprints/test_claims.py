import json
import uuid

from firebase_admin import auth
from pytest_bdd import given, scenarios, then

from integtest.blueprints.characters import Doctor, Patient
from integtest.blueprints.fhir_input_constants import PATIENT_DATA, PRACTITIONER_DATA
from integtest.utils import get_token

scenarios("../features/claims.feature")


@given("a doctor", target_fixture="doctor")
def get_doctor(client):
    practitioner = auth.create_user(
        email=f"doctor-{uuid.uuid4()}@fake.umed.jp",
        email_verified=True,
        password=f"password-{uuid.uuid4()}",
        display_name="Test Doctor",
        disabled=False,
    )
    token = auth.create_custom_token(practitioner.uid)
    token = get_token(practitioner.uid)

    practitioner_resp = client.post(
        "/practitioners",
        data=json.dumps(PRACTITIONER_DATA),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert practitioner_resp.status_code == 202

    return Doctor(practitioner.uid)


@given("a patient", target_fixture="patient")
def get_patient(client):
    patient = auth.create_user(
        email=f"patient-{uuid.uuid4()}@fake.umed.jp",
        email_verified=True,
        password=f"password-{uuid.uuid4()}",
        display_name="Test Patient",
        disabled=False,
    )
    token = auth.create_custom_token(patient.uid)
    token = get_token(patient.uid)

    resp = client.post(
        "/patients",
        data=json.dumps(PATIENT_DATA),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 202
    return Patient(patient.uid, json.loads(resp.data))


@then("all patients can be access by the practitioner")
def access_all_patients(client, doctor):
    token = auth.create_custom_token(doctor.uid)
    token = get_token(doctor.uid)

    resp = client.get(
        "/patients",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 200


@then("only one patient can be accessed")
def access_only_one_patient(client, patient):
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
