import json

from pytest_bdd import given, scenarios, then, when

from integtest.characters import (
    Appointment,
    DocumentReference,
    Encounter,
    Patient,
    Practitioner,
    User,
)
from integtest.conftest import Client
from integtest.utils import (
    create_appointment,
    create_document_reference,
    create_encounter,
    create_patient,
    create_practitioner,
    create_user,
    get_token,
)

scenarios("../features/create_document_references.feature")


@given("a user", target_fixture="user")
def get_user() -> User:
    return create_user()


@given("patient A", target_fixture="patient_a")
def get_patient_a(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


@given("patient B", target_fixture="patient_b")
def get_patient_b(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


@given("patient C", target_fixture="patient_c")
def get_patient_c(client: Client, user) -> Patient:
    return create_patient(client, user)


@given("doctor D", target_fixture="doctor_d")
def get_doctor(client: Client) -> Practitioner:
    user = create_user()
    return create_practitioner(client, user)


@given("doctor E is created with the same user as patientC", target_fixture="doctor_e")
def get_another_doctor(client: Client, user: User) -> Practitioner:
    return create_practitioner(client, user)


@when("patient A creates a document reference", target_fixture="document_reference")
def patient_creates_document_reference(
    client: Client, patient_a: Patient
) -> DocumentReference:
    return create_document_reference(client, get_token(patient_a.uid), patient_a)


@when("patient A creates an appointment with doctor D", target_fixture="appointment")
def patient_creates_an_appointment(
    client: Client, patient_a: Patient, doctor_d: Practitioner
) -> Appointment:
    return create_appointment(client, doctor_d, patient_a)


@when(
    "patient A creates different appointment with doctor D",
    target_fixture="another_appointment",
)
def patient_creates_another_appointment(
    client: Client, patient_a: Patient, doctor_d: Practitioner
) -> Appointment:
    return create_appointment(client, doctor_d, patient_a, days=5)


@when("doctor D creates an encounter", target_fixture="encounter")
def doctor_creates_encounter(
    client: Client, doctor_d: Practitioner, patient_a: Patient, appointment: Appointment
) -> Encounter:
    return create_encounter(client, doctor_d, patient_a, appointment)


@when("doctor D creates another encounter", target_fixture="another_encounter")
def doctor_creates_another_encounter(
    client: Client,
    doctor_d: Practitioner,
    patient_a: Patient,
    another_appointment: Appointment,
) -> Encounter:
    return create_encounter(client, doctor_d, patient_a, another_appointment)


@when(
    "doctor D creates three clinical note for patient A", target_fixture="clinical_note"
)
def doctor_creates_clinical_note(
    client: Client,
    patient_a: Patient,
    doctor_d: Practitioner,
    encounter: Encounter,
) -> str:
    token = get_token(doctor_d.uid)
    patient_id = patient_a.fhir_data["id"]
    clinical_note = "PGh0bWw+Cjx0aXRsZT4gVGVzdCBEb2N1bWVudCA8L3RpdGxlPgoKRG9jdW1lbnQgY29udGVudCEKCjwvaHRtbD4="

    document_ref = {
        "subject": f"Patient/{patient_id}",
        "document_type": "clinical_note",
        "encounter_id": encounter["id"],
        "pages": [
            {
                "data": clinical_note,
                "title": "page1",
            }
        ],
    }
    resp = client.post(
        "/document_references",
        data=json.dumps(document_ref),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 201
    return clinical_note


@when("doctor D creates different clinical note for patient A")
def doctor_creates_different_clinical_note(
    client: Client,
    patient_a: Patient,
    doctor_d: Practitioner,
    another_encounter: Encounter,
    clinical_note: str,
) -> str:
    token = get_token(doctor_d.uid)
    patient_id = patient_a.fhir_data["id"]

    document_ref = {
        "subject": f"Patient/{patient_id}",
        "document_type": "clinical_note",
        "encounter_id": another_encounter["id"],
        "pages": [
            {
                "data": clinical_note,
                "title": "page1",
            }
        ],
    }
    resp = client.post(
        "/document_references",
        data=json.dumps(document_ref),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 201


@then("patient A, the creator, can access the document reference")
def check_access_of_self(client: Client, patient_a: Patient):
    token = get_token(patient_a.uid)

    patient_id = patient_a.fhir_data["id"]
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
def check_access_of_doctor_for_document_ref(
    client: Client, patient_a: Patient, doctor_d: Practitioner
):
    token = get_token(doctor_d.uid)

    patient_id = patient_a.fhir_data["id"]
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
    client: Client, patient_a: Patient, patient_b: Patient
):
    token = get_token(patient_b.uid)

    patient_id = patient_a.fhir_data["id"]
    resp_a = client.get(
        f"/document_references?subject=Patient/{patient_id}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp_a.status_code == 403


@then("doctor E, who is also a patient, can access the document reference")
def check_access_of_doctor(client: Client, patient_a: Patient, doctor_e: Practitioner):
    token = get_token(doctor_e.uid)

    patient_id = patient_a.fhir_data["id"]
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


@then("doctor D can access two clinical note")
def doctor_can_access_clinical_note(
    client: Client, doctor_d: Practitioner, patient_a: Patient, clinical_note: str
):
    token = get_token(doctor_d.uid)

    patient_id = patient_a.fhir_data["id"]
    resp = client.get(
        f"/document_references?subject=Patient/{patient_id}&document_type=clinical_note",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data["data"]) == 2

    data = data["data"][0]
    assert data["content"][0]["attachment"]["data"] == clinical_note
