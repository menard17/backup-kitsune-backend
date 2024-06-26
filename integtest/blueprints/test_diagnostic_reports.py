import json

from pytest_bdd import given, scenarios, then, when

from integtest.characters import (
    Appointment,
    DiagnosticReport,
    Encounter,
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

scenarios("../features/create_diagnostic_reports.feature")


@given("a doctor", target_fixture="practitioner")
def get_doctor(client: Client):
    user = create_user()
    return create_practitioner(client, user)


@given("patient A", target_fixture="patientA")
def get_patient_a(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


@given("patient B", target_fixture="patientB")
def get_patient_b(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


@when("patient A makes an appointment", target_fixture="appointment")
def book_appointment(client: Client, practitioner: Practitioner, patientA: Patient):
    return create_appointment(client, practitioner, patientA)


@when("the doctor creates an encounter", target_fixture="encounter")
def get_encounter(
    client: Client,
    practitioner: Practitioner,
    patientA: Patient,
    appointment: Appointment,
):
    return create_encounter(client, practitioner, patientA, appointment)


@when(
    "the doctor creates another diagnostic report", target_fixture="diagnostic_report"
)
@when("the doctor creates a diagnostic report", target_fixture="diagnostic_report")
def create_diagnostic_report(
    client: Client, practitioner: Practitioner, patientA: Patient, encounter: Encounter
):
    token = get_token(practitioner.uid)
    diagnostic_report_resp = client.post(
        "/diagnostic_reports",
        data=json.dumps(
            {
                "patient_id": patientA.fhir_data["id"],
                "role_id": practitioner.fhir_data["id"],
                "encounter_id": encounter["id"],
                "conclusion": "conclusion",
            }
        ),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    data = json.loads(diagnostic_report_resp.data)
    assert data["conclusion"] == "conclusion"
    assert diagnostic_report_resp.status_code == 201
    diagnostic_report = json.loads(diagnostic_report_resp.data)
    return diagnostic_report


@when("the doctor updates diagnostic report")
def update_diagnostic_report(
    client: Client, practitioner: Practitioner, diagnostic_report: DiagnosticReport
):
    doctor_token = get_token(practitioner.uid)

    resp_patch = client.patch(
        f"/diagnostic_reports/{diagnostic_report['id']}",
        headers={"Authorization": f"Bearer {doctor_token}"},
        data=json.dumps({"conclusion": "conclusion updated"}),
        content_type="application/json",
    )

    assert resp_patch.status_code == 201


@then(
    "the doctor and patient A can access diagnostic report but patient B cannot access diagnostic report",
)
def check_diagnostic_report_access(
    client: Client,
    practitioner: Practitioner,
    patientA: Patient,
    patientB: Patient,
    diagnostic_report: DiagnosticReport,
):
    doctor_token = get_token(practitioner.uid)

    resp = client.get(
        f"/patients/{patientA.fhir_data['id']}/diagnostic_reports/{diagnostic_report['id']}",
        headers={"Authorization": f"Bearer {doctor_token}"},
        content_type="application/json",
    )

    assert resp.status_code == 200

    resp_all = client.get(
        f"/practitioners/{practitioner.practitioner_id}/diagnostic_reports",
        headers={"Authorization": f"Bearer {doctor_token}"},
        content_type="application/json",
    )

    assert len(json.loads(resp_all.data)) == 1

    patienta_token = get_token(patientA.uid)

    resp_a = client.get(
        f"/patients/{patientA.fhir_data['id']}/diagnostic_reports/{diagnostic_report['id']}",
        headers={"Authorization": f"Bearer {patienta_token}"},
        content_type="application/json",
    )

    assert resp_a.status_code == 200

    patientb_token = get_token(patientB.uid)

    resp_b = client.get(
        f"/patients/{patientA.fhir_data['id']}/diagnostic_reports/{diagnostic_report['id']}",
        headers={"Authorization": f"Bearer {patientb_token}"},
        content_type="application/json",
    )

    assert resp_b.status_code == 401


@then("the diagnostic report gets updated")
def get_updated_diagnostic_report(
    client: Client, patientA: Patient, diagnostic_report: DiagnosticReport
):

    patienta_token = get_token(patientA.uid)

    resp_a = client.get(
        f"/patients/{patientA.fhir_data['id']}/diagnostic_reports/{diagnostic_report['id']}",
        headers={"Authorization": f"Bearer {patienta_token}"},
        content_type="application/json",
    )

    data = json.loads(resp_a.data)
    assert data["data"][0]["conclusion"] == "conclusion updated"
    assert resp_a.status_code == 200


@then("the diagnostic report can be fetched by encounter id")
def get_diagnostic_report_by_encounter(
    client: Client,
    patientA: Patient,
    encounter: Encounter,
    diagnostic_report: DiagnosticReport,
):
    patienta_token = get_token(patientA.uid)

    resp_a = client.get(
        f"/patients/{patientA.fhir_data['id']}/encounters/{encounter['id']}/diagnostic_reports",
        headers={"Authorization": f"Bearer {patienta_token}"},
        content_type="application/json",
    )

    assert resp_a.status_code == 200
    data = json.loads(resp_a.data)
    assert data["data"][0]["id"] == diagnostic_report["id"]
    assert len(data["data"]) == 1
