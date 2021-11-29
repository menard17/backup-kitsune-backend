import json

from pytest_bdd import given, scenarios, then, when

from integtest.characters import Practitioner
from integtest.conftest import Client
from integtest.utils import create_practitioner, create_user, get_token

scenarios("../features/practitioner_role_can_be_updated.feature")

ALWAYS_WORKING_HOUR = [
    {
        "daysOfWeek": ["mon", "tue", "wed", "thu", "fri"],
        "availableStartTime": "00:00:00",
        "availableEndTime": "23:59:00",
    }
]


@given("a doctor", target_fixture="practitioner")
def get_doctor(client: Client):
    user = create_user()
    return create_practitioner(client, user)


@when("the doctor updates the working hour")
def doctor_update_working_schedule(client: Client, practitioner: Practitioner):
    role = practitioner.fhir_data

    role["availableTime"] = ALWAYS_WORKING_HOUR

    token = get_token(practitioner.uid)
    resp = client.put(
        f"/practitioner_roles/{role['id']}",
        data=json.dumps(role),
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200


@then("the working hour is updated")
def check_working_hour(client: Client, practitioner: Practitioner):
    token = get_token(practitioner.uid)
    resp = client.get(
        f"/practitioner_roles/{practitioner.fhir_data['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    role = json.loads(resp.data)
    assert resp.status_code == 200
    assert role["availableTime"] == ALWAYS_WORKING_HOUR
