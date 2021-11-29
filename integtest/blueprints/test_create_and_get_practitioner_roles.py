import json

from pytest_bdd import scenarios, then, when

from integtest.characters import Practitioner
from integtest.conftest import Client
from integtest.utils import create_practitioner, create_user, get_token

scenarios("../features/create_and_get_practitioner_roles.feature")


@when("a practitioner role is created", target_fixture="practitioner")
def get_practitioner(client: Client):
    user = create_user()
    return create_practitioner(client, user)


@then("the practitioner role can be found in all practitioners")
def practitioner_role_in_list_practitioner_role_response(
    client: Client, practitioner: Practitioner
):
    token = get_token(practitioner.uid)
    resp = client.get(
        "/practitioner_roles/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    has_found = False
    resp_data = json.loads(resp.data)
    for p in resp_data:
        if p["id"] == practitioner.fhir_data["id"]:
            has_found = True
    assert has_found is True


@then("the practitioner role can be get by specifying the id")
def check_working_hour(client: Client, practitioner: Practitioner):
    token = get_token(practitioner.uid)
    resp = client.get(
        f"/practitioner_roles/{practitioner.fhir_data['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    role = json.loads(resp.data)
    assert resp.status_code == 200
    assert role["id"] == practitioner.fhir_data["id"]
