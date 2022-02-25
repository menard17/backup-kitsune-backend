import json

from pytest_bdd import given, parsers, scenarios, then, when

from integtest.characters import Patient
from integtest.conftest import Client
from integtest.utils import create_patient, create_user, get_token

scenarios("../features/create_patient.feature")


@given("a patient", target_fixture="patient")
def get_patient(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


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


@then(parsers.parse("patient returns correct updated birthday format: {birthday}"))
@then(parsers.parse("patient returns correct non-updated birthday format: {birthday}"))
def returns_patient(patient_json: json, birthday: str):
    assert patient_json["birthDate"] == birthday
