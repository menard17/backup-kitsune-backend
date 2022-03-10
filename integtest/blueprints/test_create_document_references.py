import json

from pytest_bdd import given, scenarios, then, when

from integtest.characters import Patient, Practitioner
from integtest.conftest import Client
from integtest.utils import (
    create_document_reference,
    create_patient,
    create_practitioner,
    create_user,
    get_token,
)

scenarios("../features/create_document_references.feature")


@given("a user", target_fixture="user")
def get_user():
    return create_user()


@given("patient A", target_fixture="patientA")
def get_patient_a(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


@given("patient B", target_fixture="patientB")
def get_patient_b(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


@given("patient C", target_fixture="patientC")
def get_patientA(client: Client, user):
    return create_patient(client, user)


@given("doctor D", target_fixture="doctorD")
def get_doctor(client: Client):
    user = create_user()
    return create_practitioner(client, user)


@given("doctor E is created with the same user as patientC", target_fixture="doctorE")
def get_doctor(client: Client, user):
    return create_practitioner(client, user)


@when("patient A creates a document reference", target_fixture="document_reference")
def patient_create_document_reference(client: Client, patientA: Patient):
    return create_document_reference(client, patientA)


@then("patient A, the creator, can access the document reference")
def check_access_of_self(client: Client, patientA: Patient):
    token = get_token(patientA.uid)

    patient_id = patientA.fhir_data["id"]
    resp_a = client.get(
        f"/document_references?subject=Patient/{patient_id}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp_a.status_code == 200

    data = json.loads(resp_a.data)
    assert len(data["data"]) == 1

    data = data["data"][0]
    assert data["subject"]["reference"] == f"Patient/{patient_id}"


@then("doctor D can access the document reference")
def check_access_of_doctor(client: Client, patientA: Patient, doctorD: Practitioner):
    token = get_token(doctorD.uid)

    patient_id = patientA.fhir_data["id"]
    resp_a = client.get(
        f"/document_references?subject=Patient/{patient_id}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp_a.status_code == 200

    data = json.loads(resp_a.data)
    assert len(data["data"]) == 1

    data = data["data"][0]
    assert data["subject"]["reference"] == f"Patient/{patient_id}"


@then("patient B, another patient, cannot access the document reference")
def check_access_of_doctor_for_patient_b(
    client: Client, patientA: Patient, patientB: Patient
):
    token = get_token(patientB.uid)

    patient_id = patientA.fhir_data["id"]
    resp_a = client.get(
        f"/document_references?subject=Patient/{patient_id}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp_a.status_code == 403


@then("doctor E, who is also a patient, can access the document reference")
def check_access_of_doctor(client: Client, patientA: Patient, doctorE: Practitioner):
    token = get_token(doctorE.uid)

    patient_id = patientA.fhir_data["id"]
    resp_a = client.get(
        f"/document_references?subject=Patient/{patient_id}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp_a.status_code == 200

    data = json.loads(resp_a.data)
    assert len(data["data"]) == 1

    data = data["data"][0]
    assert data["subject"]["reference"] == f"Patient/{patient_id}"
