import json
import os
import uuid

import requests
from firebase_admin import auth

from integtest.blueprints.characters import Doctor, Patient
from integtest.blueprints.fhir_input_constants import PATIENT_DATA, PRACTITIONER_DATA
from integtest.blueprints.helper import get_role
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


def create_doctor(client: Client):
    doctor = auth.create_user(
        email=f"doctor-{uuid.uuid4()}@fake.umed.jp",
        email_verified=True,
        password=f"password-{uuid.uuid4()}",
        display_name="Test Doctor",
        disabled=False,
    )
    token = auth.create_custom_token(doctor.uid)
    token = get_token(doctor.uid)

    practitioner_resp = client.post(
        "/practitioners",
        data=json.dumps(PRACTITIONER_DATA),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert practitioner_resp.status_code == 202
    practitioner = json.loads(practitioner_resp.data.decode("utf-8"))
    practitioner_roles_resp = client.post(
        "/practitioner_roles",
        data=json.dumps(get_role(practitioner["id"])),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert practitioner_roles_resp.status_code == 202

    doctor_role = json.loads(practitioner_roles_resp.data)["practitioner_role"]
    return Doctor(doctor.uid, doctor_role, practitioner)


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

    assert resp.status_code == 202
    return Patient(patient.uid, json.loads(resp.data))
