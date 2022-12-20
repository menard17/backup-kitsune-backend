import json

from pytest_bdd import given, parsers, scenarios, then, when

from integtest.characters import Patient, Practitioner
from integtest.conftest import Client
from integtest.utils import create_patient, create_practitioner, create_user, get_token

scenarios("../features/update_patient.feature")


# Note that this patient has following profile:
# {
#     "family_name": "Chalmers"
#     "given_name": ["Peter", "James"]
#     "gender": "male",
#     "phone": "00000000000",
#     "dob": ""1990-01-01",
#     "address": [{
#         "use": "home",
#         "type": "both",
#         "text": "534 Erewhon St PeasantVille, Rainbow, Vic  3999",
#         "line": ["534 Erewhon St"],
#         "city": "PleasantVille",
#         "district": "Rainbow",
#         "state": "Vic",
#         "postalCode": "3999",
#         "period": {"start": "1974-12-25"},
#         "country": "US",
#     }]
# }
@given("a patient", target_fixture="patient")
def get_patient(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


@given("a practitioner", target_fixture="practitioner")
def get_practitioner(client: Client) -> Practitioner:
    user = create_user()
    return create_practitioner(client, user)


@when("practitioner tries to update patient with empty request")
def update_patient_with_empty_request(
    client: Client, patient: Patient, practitioner: Practitioner
) -> json:
    token = get_token(practitioner.uid)
    patient_resp = client.put(
        f"/patients/{patient.fhir_data['id']}",
        data=json.dumps({}),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert patient_resp.status_code == 200


@when("the practitioner updates patients name, gender, phone number, dob, and address")
def update_patients(client: Client, patient: Patient, practitioner: Practitioner):
    token = get_token(practitioner.uid)
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
        f"/patients/{patient.fhir_data['id']}",
        data=json.dumps(updated_content),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200


@then("patient will remain to have the same value")
def patient_without_changes(client: Client, patient: Patient):
    token = get_token(patient.uid)
    patient_resp = client.get(
        f"/patients/{patient.fhir_data['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert patient_resp.status_code == 200
    assert json.loads(patient_resp.data)["data"]["name"][0]["family"] == "Chalmers"


@then("patient returns correct updated profile")
def updated_patients(client: Client, patient: Patient):
    token = get_token(patient.uid)
    patient_resp = client.get(
        f"/patients/{patient.fhir_data['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert patient_resp.status_code == 200
    output = json.loads(patient_resp.data)["data"]
    assert output["name"][0]["given"] == ["Given", "Name"]
    assert output["name"][0]["family"] == "Family"
    assert output["gender"] == "female"
    expected_telecom = {"system": "phone", "use": "mobile", "value": "123"}
    assert expected_telecom in output["telecom"]
    assert output["birthDate"] == "1993-01-01"
    assert output["address"][0]["country"] == "JP"


@when(parsers.parse("orca id, {orca_id}, is added"))
def add_orca_id(client: Client, patient: Patient, orca_id: str):
    token = get_token(patient.uid)
    updated_content = {
        "orca_id": orca_id,
    }
    resp = client.put(
        f"/patients/{patient.fhir_data['id']}",
        data=json.dumps(updated_content),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200


@then(parsers.parse("patient can have one orca id: {orca_id}"))
def get_orca_id(client: Client, patient: Patient, orca_id: str):
    token = get_token(patient.uid)
    patient_resp = client.get(
        f"/patients/{patient.fhir_data['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert patient_resp.status_code == 200
    output = json.loads(patient_resp.data)["data"]
    assert output["extension"][0]["valueString"] == orca_id
