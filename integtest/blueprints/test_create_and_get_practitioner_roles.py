import json

from pytest_bdd import parsers, scenarios, then, when

from integtest.characters import Practitioner
from integtest.conftest import Client
from integtest.utils import create_practitioner, create_user, get_token

scenarios("../features/create_and_get_practitioner_roles.feature")


@when("a practitioner role is created", target_fixture="practitioner")
def get_practitioner(client: Client):
    user = create_user()
    return create_practitioner(client, user)


@when(
    parsers.parse("a practitioner role is created with {visit_type_param} visit type"),
    target_fixture="practitioner",
)
def create_practitioner_with_visit_type(visit_type_param: str, client: Client):
    user = create_user()
    return create_practitioner(client, user, visit_type=visit_type_param)


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

    resp_data = json.loads(resp.data)
    assert any([p["id"] == practitioner.fhir_data["id"] for p in resp_data])


@then("the practitioner role can be get by specifying the id")
def get_practitioner_by_id(client: Client, practitioner: Practitioner):
    token = get_token(practitioner.uid)
    resp = client.get(
        f"/practitioner_roles/{practitioner.fhir_data['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    role = json.loads(resp.data)
    assert resp.status_code == 200
    assert role["id"] == practitioner.fhir_data["id"]


@then(parsers.parse("the practitioner role has the {visit_type} visit type code"))
def practitioner_role_has_visit_type(
    visit_type: str,
    client: Client,
    practitioner: Practitioner,
):
    token = get_token(practitioner.uid)
    resp = client.get(
        f"/practitioner_roles/{practitioner.fhir_data['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    role = json.loads(resp.data)
    assert resp.status_code == 200
    assert role["id"] == practitioner.fhir_data["id"]

    assert any([c["coding"][0]["code"] == visit_type for c in role["code"]])


@then("the practitioner role can NOT be found in the default GET practitioners calls")
def practitioner_role_not_in_list_practitioner_role_response(
    client: Client, practitioner: Practitioner
):
    token = get_token(practitioner.uid)
    resp = client.get(
        "/practitioner_roles/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    resp_data = json.loads(resp.data)
    assert not any([p["id"] == practitioner.fhir_data["id"] for p in resp_data])


@then("the practitioner role can be found if specify walk-in visit type")
def practitioner_role_can_be_found_if_specify_walk_in_visit_type(
    client: Client, practitioner: Practitioner
):
    token = get_token(practitioner.uid)
    resp = client.get(
        "/practitioner_roles?visit_type=walk-in",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    resp_data = json.loads(resp.data)
    assert any([p["id"] == practitioner.fhir_data["id"] for p in resp_data])

    role_id = practitioner.fhir_data["id"]
    resp = client.patch(
        f"/practitioner_roles/{role_id}?active=false",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204
