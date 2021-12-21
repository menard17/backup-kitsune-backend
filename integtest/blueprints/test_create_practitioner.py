import json

from pytest_bdd import given, scenarios, then, when

from integtest.characters import Practitioner
from integtest.conftest import Client
from integtest.utils import User, create_practitioner, create_user

scenarios("../features/create_practitioner.feature")


@given("a user", target_fixture="user")
def get_user() -> User:
    return create_user()


@when("a doctor is created", target_fixture="practitioner")
def create_doctor(client: Client, user: User) -> str:
    return create_practitioner(client, user)


@when("a doctor is tried to be created with jpeg")
def fail_to_create_doctor(client: Client, user: User) -> str:
    base64_prefix = "data:image/png;base64,"
    with open("./artifact/image_base64") as f:
        photo_base64 = f.readlines()[0]
    photo_base64 = "data:image/jpeg;base64," + photo_base64[len(base64_prefix) :]
    resp = client.post(
        "/practitioner_roles",
        data=json.dumps(
            {
                "is_doctor": "true",
                "start": "2021-08-15T13:55:57.967345+09:00",
                "end": "2021-08-15T14:55:57.967345+09:00",
                "family_name": "Last name",
                "given_name": "Given name",
                "zoom_id": "zoom id",
                "zoom_password": "zoom password",
                "available_time": [
                    {
                        "daysOfWeek": ["mon", "tue", "wed"],
                        "availableStartTime": "09:00:00",
                        "availableEndTime": "16:30:00",
                    },
                ],
                "email": "",
                "photo": photo_base64,
            }
        ),
        headers={"Authorization": f"Bearer {user.token}"},
        content_type="application/json",
    )
    assert resp.status_code == 400


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
