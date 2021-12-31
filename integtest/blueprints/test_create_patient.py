import json

from pytest_bdd import given, scenarios, then

from integtest.characters import Patient
from integtest.conftest import Client
from integtest.utils import create_patient, create_user, get_token

scenarios("../features/create_patient.feature")


@given("a patient", target_fixture="patient")
def get_patient(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


@then("patient returns correct birthday format")
def returns_patient(client: Client, patient: Patient):
    token = get_token(patient.uid)

    patient_resp = client.get(
        f"/patients/{patient.fhir_data['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert patient_resp.status_code == 200
    data = json.loads(patient_resp.data)
    assert data["data"]["birthDate"] == "1990-01-01"
