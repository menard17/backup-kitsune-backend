import json

from pytest_bdd import given, scenarios, then, when

from integtest.characters import (
    Appointment,
    Encounter,
    MedicationRequest,
    Patient,
    Practitioner,
)
from integtest.conftest import Client
from integtest.utils import (
    create_appointment,
    create_encounter,
    create_patient,
    create_practitioner,
    create_user,
    get_token,
)

scenarios("../features/create_medication_requests.feature")


@given("a doctor", target_fixture="doctor")
def get_doctor(client: Client) -> Practitioner:
    user = create_user()
    return create_practitioner(client, user)


@given("a patient", target_fixture="patient")
def get_patient(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


@given("an appointment", target_fixture="appointment")
def get_appointment(
    client: Client, doctor: Practitioner, patient: Patient
) -> Appointment:
    return create_appointment(client, doctor, patient)


@when("the doctor creates an encounter", target_fixture="encounter")
def create_first_encounter(
    client: Client, doctor: Practitioner, patient: Patient, appointment: Appointment
) -> Encounter:
    encounter = create_encounter(client, doctor, patient, appointment)
    return encounter


@when(
    "the doctor creates medication requests",
    target_fixture="medication_request",
)
def create_medication_request(
    client: Client, patient: Patient, doctor: Practitioner, encounter: Encounter
) -> MedicationRequest:
    medication_request_data = {
        "patient_id": patient.fhir_data["id"],
        "requester_id": doctor.fhir_data["id"],
        "encounter_id": encounter["id"],
        "medications": [
            {
                "code": "ref 0",
                "display": "display 0",
            },
            {
                "code": "ref 1",
                "display": "display 1",
            },
        ],
        "status": "active",
        "priority": "urgent",
    }
    token = get_token(doctor.uid)
    # First POST call is created with active status
    # However second POST call updates the status to cancelled
    client.post(
        "/medication_requests",
        data=json.dumps(medication_request_data),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    resp = client.post(
        "/medication_requests",
        data=json.dumps(medication_request_data),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 201
    return json.loads(resp.data)


@then("the doctor can fetch medication requests for the encounter")
def get_service_request_by_encounter(
    client: Client,
    doctor: Practitioner,
    encounter: Encounter,
    medication_request: MedicationRequest,
):
    token = get_token(doctor.uid)
    resp = client.get(
        f"medication_requests/?encounter_id={encounter['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 200
    assert len(list(json.loads(resp.data)["data"])) == 1
    id1 = list(json.loads(resp.data)["data"])[0]["id"]
    assert id1 == medication_request[0]["id"]
