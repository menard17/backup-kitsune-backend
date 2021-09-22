import json
import os
import uuid
from datetime import datetime, timedelta

import pytz
import requests
from firebase_admin import auth

from integtest.blueprints.characters import Appointment, Patient, Practitioner
from integtest.blueprints.fhir_input_constants import PATIENT_DATA, PRACTITIONER_DATA
from integtest.blueprints.helper import get_encounter_data, get_role
from integtest.conftest import Client

FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")


def get_token(uid):
    """Return a Firebase ID token dict from a user id (UID).
    Returns:
    dict: Keys are "kind", "idToken", "refreshToken", and "expiresIn".
    "expiresIn" is in seconds.
    The return dict matches the response payload described in
    https://firebase.google.com/docs/reference/rest/auth/#section-verify-custom-token
    The actual token is at get_token(uid)["idToken"].
    """
    token = auth.create_custom_token(uid)
    data = {"token": token.decode("utf-8"), "returnSecureToken": True}

    url = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyCustomToken?key={FIREBASE_API_KEY}"

    resp = requests.post(
        url, data=json.dumps(data), headers={"Content-Type": "application/json"}
    )
    return resp.json()["idToken"]


def create_practitioner(client: Client):
    practitioner = auth.create_user(
        email=f"practitioner-{uuid.uuid4()}@fake.umed.jp",
        email_verified=True,
        password=f"password-{uuid.uuid4()}",
        display_name="Test Practitioner",
        disabled=False,
    )
    token = auth.create_custom_token(practitioner.uid)
    token = get_token(practitioner.uid)

    practitioner_resp = client.post(
        "/practitioners",
        data=json.dumps(PRACTITIONER_DATA),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert practitioner_resp.status_code == 201
    practitioner_output = json.loads(practitioner_resp.data.decode("utf-8"))
    practitioner_roles_resp = client.post(
        "/practitioner_roles",
        data=json.dumps(get_role(practitioner_output["id"])),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert practitioner_roles_resp.status_code == 201

    doctor_role = json.loads(practitioner_roles_resp.data)["practitioner_role"]
    return Practitioner(practitioner.uid, doctor_role, practitioner_output)


def create_patient(client: Client):
    patient = auth.create_user(
        email=f"patient-{uuid.uuid4()}@fake.umed.jp",
        email_verified=True,
        password=f"password-{uuid.uuid4()}",
        display_name="Patient",
        disabled=False,
    )
    token = get_token(patient.uid)

    resp = client.post(
        "/patients",
        data=json.dumps(PATIENT_DATA),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 201
    return Patient(patient.uid, json.loads(resp.data))


def create_appointment(client: Client, doctor: Practitioner, patientA: Patient):
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    start = now.isoformat()
    end = (now + timedelta(hours=1)).isoformat()

    appointment_data = {
        "practitioner_role_id": doctor.fhir_data["id"],
        "patient_id": patientA.fhir_data["id"],
        "start": start,
        "end": end,
    }

    token = get_token(patientA.uid)
    resp = client.post(
        "/appointments",
        data=json.dumps(appointment_data),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 201

    appointment = json.loads(resp.data)
    return appointment


def create_encounter(
    client: Client, doctor: Practitioner, patient: Patient, appointment: Appointment
):
    token = auth.create_custom_token(doctor.uid)
    token = get_token(doctor.uid)

    resp = client.post(
        f"/patients/{patient.fhir_data['id']}/encounters",
        data=json.dumps(
            get_encounter_data(
                patient.fhir_data["id"],
                doctor.fhir_practitioner_data["id"],
                appointment["id"],
            )
        ),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 201

    encounter = json.loads(resp.data)
    return encounter
