import json

from pytest_bdd import given, scenarios, then

from integtest.characters import Appointment, DocumentReference, Patient, Practitioner
from integtest.conftest import Client
from integtest.utils import (
    create_appointment,
    create_document_reference,
    create_patient,
    create_practitioner,
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


@given("a doctor", target_fixture="practitioner")
def get_doctor(client: Client) -> Practitioner:
    user = create_user()
    return create_practitioner(client, user, role_type="doctor")


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
        f"/consents?grantee={patient.fhir_data['id']}&include_patient=true",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200

    data = json.loads(resp.data)["data"]

    # check that the consents includes the reference to the patients
    # the reference IDs will be the format of "Patient/[:patient-id]"
    consents = [d for d in data if d["resourceType"] == "Consent"]
    consents_ref_ids = [c["patient"]["reference"].split("/")[1] for c in consents]
    assert secondary_patient.fhir_data["id"] in consents_ref_ids
    assert secondary_patient_2.fhir_data["id"] in consents_ref_ids

    # check that `include_patient=true` parameter gets the patient data
    patients = [d for d in data if d["resourceType"] == "Patient"]
    patient_ids = [p["id"] for p in patients]
    assert secondary_patient.fhir_data["id"] in patient_ids
    assert secondary_patient_2.fhir_data["id"] in patient_ids

    # the ID list should be the same
    assert sorted(consents_ref_ids) == sorted(patient_ids)

    return patient_ids


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


@then("primary patient can update secondary patient information")
def update_patients(
    client: Client,
    patient: Patient,
    secondary_patient: Patient,
):
    token = get_token(patient.uid)
    updated_content = {
        "given_name": ["Given", "Name"],
        "family_name": "Family",
        "gender": "female",
        "phone": "123",
        "dob": "1993-01-01",
        "address": [
            {
                "use": "home",
                "type": "both",
                "line": ["Test"],
                "city": "Test City",
                "state": "Test State",
                "postalCode": "3999",
                "country": "JP",
            }
        ],
    }
    resp = client.put(
        f"/patients/{secondary_patient.fhir_data['id']}",
        data=json.dumps(updated_content),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200


@then("primary patient can create insurance for the secondary patient")
def primary_patient_creates_secondary_patient_document_reference(
    client: Client,
    patient: Patient,
    secondary_patient: Patient,
) -> DocumentReference:
    primary_patient_token = get_token(patient.uid)
    return create_document_reference(client, primary_patient_token, secondary_patient)


@then("primary patient can access the insurance for the secondary patient")
def primary_patient_acess_secondary_patient_document_reference(
    client: Client,
    patient: Patient,
    secondary_patient: Patient,
):
    token = get_token(patient.uid)

    secondary_patient_id = secondary_patient.fhir_data["id"]
    resp_a = client.get(
        f"/document_references?subject=Patient/{secondary_patient_id}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp_a.status_code == 200

    data = json.loads(resp_a.data)
    assert len(data["data"]) == 1

    data = data["data"][0]
    assert data["subject"]["reference"] == f"Patient/{secondary_patient_id}"


@then("primary patient can book appointment for the seondary patient")
def primary_patient_book_appointment_for_secondary_patient(
    client: Client,
    practitioner: Practitioner,
    patient: Patient,
    secondary_patient: Patient,
) -> Appointment:
    return create_appointment(
        client,
        practitioner,
        secondary_patient,
        auth_token=get_token(patient.uid),
    )
