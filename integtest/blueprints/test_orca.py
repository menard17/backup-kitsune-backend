import json

from pytest_bdd import given, scenarios, then, when
from firebase_admin import auth
from integtest.characters import Patient, Practitioner
from integtest.conftest import Client
from integtest.utils import (
    create_patient,
    create_practitioner,
    create_user,
    get_token,
)

scenarios("../features/orca.feature")


@given("a back-office staff", target_fixture="staff")
def get_back_office_staff(client: Client) -> Practitioner:
    user = create_user()

    # Assign required role for staff
    firebase_user = auth.get_user_by_email(user.email)
    custom_claims = firebase_user.custom_claims or {}
    current_roles = custom_claims.get("roles", {})
    current_roles["Staff"] = {}
    auth.set_custom_user_claims(user.uid, {"roles": current_roles})

    return create_practitioner(client, user, role_type="staff")


@given("a patient", target_fixture="patient")
def get_patient(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


@when("put orca id for patient details", target_fixture="patient_json")
def put_orca_id_for_patient(client: Client, patient: Patient, staff: Practitioner) -> json:
    token = get_token(staff.uid)
    patient_id = patient.fhir_data["id"]

    resp = client.put(
        f"/patients/{patient_id}/orca",
        data=json.dumps(
            {
                "orca_id": "111",
            }
        ),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    return json.loads(resp.data)["data"]


@when("change orca id for patient already have orca id", target_fixture="patient_json")
def change_orca_id_for_patient_have_orca_id(client: Client, patient: Patient, staff: Practitioner) -> json:
    token = get_token(staff.uid)
    patient_id = patient.fhir_data["id"]

    resp = client.put(
        f"/patients/{patient_id}/orca",
        data=json.dumps(
            {
                "orca_id": "123",
            }
        ),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    return json.loads(resp.data)["data"]


@then("patient details have orca id and orca code")
def patient_details(client: Client, patient: Patient, patient_json: json, staff: Practitioner):
    token = get_token(staff.uid)
    patient_id = patient.fhir_data["id"]
    resp = client.get(
        f"/patients/{patient_id}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)["data"]
    assert data["extension"][0]["url"] == patient_json["extension"][0]["url"]
    assert data["extension"][0]["valueString"] == patient_json["extension"][0]["valueString"]
