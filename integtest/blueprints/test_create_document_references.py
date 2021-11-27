import json

from firebase_admin import auth
from pytest_bdd import given, scenarios, then, when

from integtest.blueprints.characters import DocumentReference, Patient, Practitioner
from integtest.conftest import Client
from integtest.utils import (
    create_document_reference,
    create_patient,
    create_practitioner,
    get_token,
)

scenarios("../features/create_document_references.feature")


@given("patient A", target_fixture="patientA")
def get_patient(client: Client) -> Patient:
    return create_patient(client)


@given("patient B", target_fixture="patientB")
def get_patient(client: Client) -> Patient:
    return create_patient(client)


@given("a doctor", target_fixture="practitioner")
def get_doctor(client: Client):
    return create_practitioner(client)


@when("patient A creates a document reference", target_fixture="document_reference")
def patient_create_document_reference(
    client: Client, practitioner: Practitioner, patientA: Patient
):
    return create_document_reference(client, patientA)


@then("patient A can access the document reference")
def check_access_of_self(client: Client, patientA: Patient):
    token = auth.create_custom_token(patientA.uid)
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

    data = json.loads(data["data"][0])
    assert data["subject"]["reference"] == f"Patient/{patient_id}"


@then("doctor can access the document reference")
def check_access_of_doctor(
    client: Client, patientA: Patient, practitioner: Practitioner
):
    token = auth.create_custom_token(practitioner.uid)
    token = get_token(practitioner.uid)

    patient_id = patientA.fhir_data["id"]
    resp_a = client.get(
        f"/document_references?subject=Patient/{patient_id}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp_a.status_code == 200

    data = json.loads(resp_a.data)
    assert len(data["data"]) == 1

    data = json.loads(data["data"][0])
    assert data["subject"]["reference"] == f"Patient/{patient_id}"


@then("patient B cannot access the document reference")
def check_access_of_doctor(client: Client, patientA: Patient, patientB: Patient):
    token = auth.create_custom_token(patientB.uid)
    token = get_token(patientB.uid)

    patient_id = patientA.fhir_data["id"]
    resp_a = client.get(
        f"/document_references?subject=Patient/{patient_id}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp_a.status_code == 403
