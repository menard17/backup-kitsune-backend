import json

from firebase_admin import auth
from pytest_bdd import given, parsers, scenarios, then, when

from integtest.characters import Patient, Practitioner
from integtest.conftest import Client
from integtest.utils import create_patient, create_practitioner, create_user, get_token

scenarios("../features/create_patient.feature")


@given("a patient", target_fixture="patient")
def get_patient(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


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


@given("get all inactive patients", target_fixture="num_paitents")
def return_all_patients(client: Client, staff: Practitioner) -> int:
    token = get_token(staff.uid)
    patients = client.get(
        "/patients?active=false",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert patients.status_code == 200
    data = json.loads(patients.data)
    num_paitents = data["data"]["total"]
    assert num_paitents > 0
    return num_paitents


@when(
    parsers.parse("patient updates birthday to {updated}"),
    target_fixture="patient_json",
)
def patch_birthday(client: Client, patient: Patient, updated: str) -> json:
    token = get_token(patient.uid)
    patient_resp = client.patch(
        f"/patients/{patient.fhir_data['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
        data=json.dumps([{"op": "add", "path": "/birthDate", "value": updated}]),
    )
    assert patient_resp.status_code == 200
    return json.loads(patient_resp.data)


@when("patient get call is called", target_fixture="patient_json")
def get_birthday(client: Client, patient: Patient) -> json:
    token = get_token(patient.uid)
    patient_resp = client.get(
        f"/patients/{patient.fhir_data['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert patient_resp.status_code == 200
    return json.loads(patient_resp.data)["data"]


@when("inactivate patient")
def inactivate_patient(client: Client, patient: Patient):
    token = get_token(patient.uid)
    patient_resp = client.patch(
        f"/patients/{patient.fhir_data['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
        data=json.dumps([{"op": "add", "path": "/active", "value": False}]),
    )
    assert patient_resp.status_code == 200


@then("patient is inactive")
def patient_is_inactive(client: Client, patient: Patient):
    token = get_token(patient.uid)
    patient_resp = client.get(
        f"/patients/{patient.fhir_data['id']}?active=false",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert patient_resp.status_code == 200
    assert not json.loads(patient_resp.data)["data"]["active"]


@then(parsers.parse("patient returns correct updated birthday format: {birthday}"))
@then(parsers.parse("patient returns correct non-updated birthday format: {birthday}"))
def returns_patient(patient_json: json, birthday: str):
    assert patient_json["birthDate"] == birthday


@then("get all inactive patients")
def return_all_active_patients(client: Client, staff: Practitioner, num_paitents: int):
    token = get_token(staff.uid)
    patients = client.get(
        "/patients?active=false",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert patients.status_code == 200
    data = json.loads(patients.data)
    assert data["data"]["total"] > num_paitents
