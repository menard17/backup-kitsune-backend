import json
from datetime import datetime, timedelta

import pytz
from pytest_bdd import given, scenarios, then, when

from integtest.blueprints.helper import (
    get_diagnostic_report_data,
    get_service_request_data,
)
from integtest.characters import (
    Appointment,
    DiagnosticReport,
    Encounter,
    Patient,
    Practitioner,
    ServiceRequest,
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

scenarios("../features/create_service_request.feature")


@given("a doctor", target_fixture="doctor")
def get_doctor(client: Client) -> Practitioner:
    user = create_user()
    return create_practitioner(client, user)


@given("a nurse", target_fixture="nurse")
def get_nurse(client: Client) -> Practitioner:
    user = create_user()
    return create_practitioner(client, user, role_type="nurse")


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


@when("the doctor creates a diagnostic report", target_fixture="service_request")
def create_service_request(
    client: Client,
    patient: Patient,
    doctor: Practitioner,
    nurse: Practitioner,
    encounter: Encounter,
) -> DiagnosticReport:
    token = get_token(doctor.uid)
    diagnostic_report_resp = client.post(
        "/diagnostic_reports",
        data=json.dumps(
            get_diagnostic_report_data(
                patient.fhir_data["id"],
                doctor.fhir_practitioner_data["id"],
                encounter["id"],
            )
        ),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert diagnostic_report_resp.status_code == 201
    servie_request_resp = client.post(
        "service_requests",
        data=json.dumps(
            get_service_request_data(
                patient.fhir_data["id"],
                doctor.fhir_practitioner_data["id"],
                nurse.fhir_practitioner_data["id"],
            )
        ),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert servie_request_resp.status_code == 201
    return json.loads(servie_request_resp.data)


@when(
    "the doctor creates appointment for nurse with service request",
    target_fixture="nurse_appointment",
)
def create_appointment_for_nurse(
    client: Client,
    nurse: Practitioner,
    doctor: Practitioner,
    patient: Patient,
    service_request: ServiceRequest,
) -> Appointment:
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    start = now.isoformat()
    end = (now + timedelta(hours=1)).isoformat()

    appointment_data = {
        "practitioner_role_id": nurse.fhir_data["id"],
        "patient_id": patient.fhir_data["id"],
        "start": start,
        "end": end,
        "service_request_id": service_request["id"],
    }

    token = get_token(doctor.uid)
    resp = client.post(
        "/appointments",
        data=json.dumps(appointment_data),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 201

    appointment = json.loads(resp.data)
    return appointment


@then("patient can fetch next appointment from doctor encounter")
def get_next_appointment(
    client: Client,
    patient: Patient,
    encounter: Encounter,
    nurse_appointment: Appointment,
):
    token = get_token(patient.uid)

    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    yesterday = tokyo_timezone.localize(datetime.now() - timedelta(days=1))
    url = f"/appointments?date={yesterday.date().isoformat()}&actor_id={patient.fhir_data['id']}&encounter_id={encounter['id']}"

    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert json.loads(resp.data)["data"][0]["id"] == nurse_appointment["id"]


@then("the nurse can fethc service request with given id")
def get_service_request_by_id(
    client: Client, nurse: Practitioner, service_request: ServiceRequest
):
    token = get_token(nurse.uid)

    resp = client.get(
        f"service_requests/{service_request['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 200
    assert json.loads(resp.data)["data"][0]["id"] == service_request["id"]
