import json
import os
import uuid
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Tuple

import pytz
import requests
from firebase_admin import auth

from integtest.blueprints.fhir_input_constants import (
    DOCUMENT_REFERENCE_DATA,
    PATIENT_DATA,
)
from integtest.characters import (
    Appointment,
    DocumentReference,
    Encounter,
    Patient,
    Practitioner,
    User,
)
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


def create_user() -> User:
    email = f"user-{uuid.uuid4()}@fake.umed.jp"
    user = auth.create_user(
        email=email,
        email_verified=True,
        password=f"password-{uuid.uuid4()}",
        display_name="Test User",
        disabled=False,
    )
    token = get_token(user.uid)
    return User(user.uid, email, token)


def make_admin(user: User) -> User:
    """Make an user admin.
    Note that this overrides the claims so please use this before setting other roles.
    """
    auth.set_custom_user_claims(user.uid, {"roles": {"Admin": {}}})
    return user


def create_practitioner(
    client: Client,
    user: User,
    language=["en"],
    role_type="doctor",
    practitioner_name: Tuple = ("Last Name", "Given Name"),
    available_time: list = [
        {
            "daysOfWeek": ["mon", "tue", "wed"],
            "availableStartTime": "09:00:00",
            "availableEndTime": "16:30:00",
        },
    ],
):
    base64_prefix = "data:image/png;base64,"
    with open("artifact/image_base64") as f:
        photo_base64 = f.readlines()[0]
    assert photo_base64.startswith(base64_prefix)
    param_data = {
        "role_type": role_type,
        "start": "2021-08-15",
        "end": "2099-08-15",
        "family_name_en": practitioner_name[0],
        "given_name_en": practitioner_name[1],
        "bio_en": "My background ...",
        "gender": "male",
        "email": user.email,
        "photo": photo_base64,
    }
    if role_type == "doctor":
        if "ja" in language:
            param_data["family_name_ja"]
            param_data["given_name_ja"]
            param_data["bio_ja"]
        param_data["zoom_password"] = "zoom password"
        param_data["zoom_id"] = "zoom id"
        param_data["available_time"] = available_time

    resp = client.post(
        "/practitioner_roles",
        data=json.dumps(param_data),
        headers={"Authorization": f"Bearer {user.token}"},
        content_type="application/json",
    )
    assert resp.status_code == 201
    practitioner_id = json.loads(resp.data)["practitioner"]["reference"].split("/")[1]

    return Practitioner(
        user.uid,
        json.loads(resp.data),
        practitioner_id,
        practitioner_name=practitioner_name,
    )


def create_patient(client: Client, user: User, override_name: list = []):
    if override_name:
        patient_data = deepcopy(PATIENT_DATA)
        patient_data["name"] = override_name
    else:
        patient_data = PATIENT_DATA
    resp = client.post(
        "/patients",
        data=json.dumps(patient_data),
        headers={"Authorization": f"Bearer {user.token}"},
        content_type="application/json",
    )

    assert resp.status_code == 201
    return Patient(user.uid, json.loads(resp.data))


def create_secondary_patient(client: Client, patient: Patient):
    """
    If there is a patient ID attached to the Firebase token already,
    the further call to create the patient will be treat as creating
    the secondary patient(s).
    """
    token = get_token(patient.uid)
    resp = client.post(
        "/patients",
        data=json.dumps(PATIENT_DATA),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert resp.status_code == 201
    # secondary patient does not have firebase id
    return Patient(None, json.loads(resp.data))


def create_appointment(
    client: Client,
    practitioner: Practitioner,
    patient: Patient,
    days=0,
    service="online",
    auth_token: str = "",
) -> Appointment:
    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    start = (now - timedelta(days=days)).isoformat()
    end = (now - timedelta(days=days) + timedelta(hours=1)).isoformat()

    appointment_data = {
        "practitioner_role_id": practitioner.fhir_data["id"],
        "patient_id": patient.fhir_data["id"],
        "start": start,
        "end": end,
        "service_type": "walkin",
        "service": service,
        "email_notification": "false",
    }

    token = auth_token or get_token(patient.uid)
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
    client: Client,
    practitioner: Practitioner,
    patient: Patient,
    appointment: Appointment,
) -> Encounter:
    token = get_token(practitioner.uid)

    resp = client.post(
        f"/patients/{patient.fhir_data['id']}/encounters",
        data=json.dumps(
            {
                "patient_id": patient.fhir_data["id"],
                "role_id": practitioner.fhir_data["id"],
                "appointment_id": appointment["id"],
            }
        ),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 201
    output = json.loads(resp.data)["data"]
    encounter = next(filter(lambda item: item["resourceType"] == "Encounter", output))
    return encounter


def create_document_reference(
    client: Client,
    auth_token: str,
    patient: Patient,
) -> DocumentReference:
    patient_id = patient.fhir_data["id"]
    DOCUMENT_REFERENCE_DATA["subject"] = f"Patient/{patient_id}"
    resp = client.post(
        "/document_references",
        data=json.dumps(DOCUMENT_REFERENCE_DATA),
        headers={"Authorization": f"Bearer {auth_token}"},
        content_type="application/json",
    )

    assert resp.status_code == 201

    document_reference = json.loads(resp.data)
    return document_reference
