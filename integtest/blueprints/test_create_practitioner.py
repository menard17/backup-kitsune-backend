import json

from pytest_bdd import given, scenarios, then, when

from integtest.characters import Practitioner
from integtest.conftest import Client
from integtest.utils import User, create_practitioner, create_user

scenarios("../features/create_practitioner.feature")


def get_practitioner_data_with_email(email):
    return {
        "resourceType": "Practitioner",
        "active": True,
        "name": [{"family": "Email", "given": ["Cool"], "prefix": ["Dr"]}],
        "telecom": [{"system": "email", "value": email, "use": "work"}],
    }


@given("a user", target_fixture="user")
def get_user() -> User:
    return create_user()


@when("a doctor is created", target_fixture="practitioner")
def create_doctor(client: Client, user: User) -> str:
    return create_practitioner(client, user)


@then("the doctor can be searched by email")
def get_doctor_email(client: Client, user: User, practitioner: Practitioner) -> str:
    resp = client.get(
        f"/practitioners?email={user.email}",
        headers={"Authorization": f"Bearer {user.token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert (
        f"Practitioner/{data['data'][0]['id']}"
        == practitioner.fhir_data["practitioner"]["reference"]
    )
