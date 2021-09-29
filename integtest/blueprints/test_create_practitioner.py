import json
import uuid

from firebase_admin import auth
from pytest_bdd import given, scenarios, then, when

from integtest.blueprints.characters import Practitioner
from integtest.conftest import Client
from integtest.utils import get_token

scenarios("../features/create_practitioner.feature")


class User:
    def __init__(self, uid, email, token):
        self.uid = uid
        self.email = email
        self.token = token


def get_practitioner_data_with_email(email):
    return {
        "resourceType": "Practitioner",
        "active": True,
        "name": [{"family": "Email", "given": ["Cool"], "prefix": ["Dr"]}],
        "telecom": [{"system": "email", "value": email, "use": "work"}],
    }


@given("a user", target_fixture="user")
def create_user(client: Client) -> User:
    email = f"user-{uuid.uuid4()}@fake.umed.jp"
    practitioner = auth.create_user(
        email=email,
        email_verified=True,
        password=f"password-{uuid.uuid4()}",
        display_name="Test User",
        disabled=False,
    )
    token = auth.create_custom_token(practitioner.uid)
    token = get_token(practitioner.uid)
    return User(practitioner.uid, email, token)


@when("a doctor is created", target_fixture="doctor")
def create_doctor(client: Client, user: User) -> str:
    resp = client.post(
        "/practitioners",
        data=json.dumps(get_practitioner_data_with_email(user.email)),
        headers={"Authorization": f"Bearer {user.token}"},
        content_type="application/json",
    )
    assert resp.status_code == 201
    return Practitioner(user.uid, practitioner=json.loads(resp.data.decode("utf-8")))


@then("the doctor can be searched by email")
def get_doctor(client: Client, user: User, doctor: Practitioner) -> str:
    resp = client.get(
        f"/practitioners?email={user.email}",
        headers={"Authorization": f"Bearer {user.token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["data"][0]["id"] == doctor.fhir_practitioner_data["id"]
