import json

from pytest_bdd import given, scenarios, then

from integtest.characters import Patient
from integtest.conftest import Client
from integtest.utils import (
    create_patient,
    create_secondary_patient,
    create_user,
    get_token,
)

scenarios("../features/secondary_patients.feature")


@given("a primary patient", target_fixture="patient")
def get_patient(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


@given("a secondary patient", target_fixture="secondary_patient")
def get_secondary_patient(client: Client, patient: Patient) -> Patient:
    return create_secondary_patient(client, patient)


@given("another secondary patient", target_fixture="secondary_patient_2")
def get_another_secondary_patient(client: Client, patient: Patient) -> Patient:
    return create_secondary_patient(client, patient)


@then(
    "primary patient can get the secondary patient data",
    target_fixture="secondary_patient_json",
)
def primary_patient_get_secondary_patient(
    client: Client,
    patient: Patient,
    secondary_patient: Patient,
) -> json:
    token = get_token(patient.uid)  # use the primary patients Firebase auth
    patient_resp = client.get(
        f"/patients/{secondary_patient.fhir_data['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert patient_resp.status_code == 200
    return json.loads(patient_resp.data)["data"]


@then("primary patient can search consents granted by the secondary patient")
def primary_patient_search_consent(
    client: Client,
    patient: Patient,
    secondary_patient: Patient,
):
    token = get_token(patient.uid)
    resp = client.get(
        f"/consents?grantee={patient.fhir_data['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200

    data = json.loads(resp.data)["data"]
    secondary_ref_id = f"Patient/{secondary_patient.fhir_data['id']}"
    assert data[0]["patient"]["reference"] == secondary_ref_id


@then(
    "primary patient can get the list of secondary patients",
    target_fixture="secondary_patients_ids",
)
def primary_patient_get_list_of_secondary_patients(
    client: Client,
    patient: Patient,
    secondary_patient: Patient,
    secondary_patient_2: Patient,
) -> json:
    token = get_token(patient.uid)
    resp = client.get(
        f"/consents?grantee={patient.fhir_data['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200

    data = json.loads(resp.data)["data"]

    # the reference IDs will be the format of "Patient/[:patient-id]"
    data_ids = [d["patient"]["reference"].split("/")[1] for d in data]

    assert secondary_patient.fhir_data["id"] in data_ids
    assert secondary_patient_2.fhir_data["id"] in data_ids
    return data_ids


@then("primary patient can get the appointments of each secondary patient")
def primary_patient_get_appointments_of_each_secondary_patient(
    client: Client, patient: Patient, secondary_patients_ids: list
):
    # sanity check
    assert len(secondary_patients_ids) > 0

    token = get_token(patient.uid)
    for id in secondary_patients_ids:
        resp = client.get(
            f"/appointments?actor_id={id}",
            headers={"Authorization": f"Bearer {token}"},
            content_type="application/json",
        )
        assert resp.status_code == 200
