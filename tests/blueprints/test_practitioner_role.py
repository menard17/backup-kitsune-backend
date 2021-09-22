import json

from fhir.resources import construct_fhir_element
from helper import FakeRequest, MockResourceClient

from blueprints.practitioner_roles import PractitionerRoleController

TEST_PRACTITIONER_ID = "dummy-practitioner-id"
TEST_PRACTITIONER_ROLE_ID = "dummy-role-id"
TEST_SCHEDULE_ID = "dummy-schedule-id"

PRACTITIONER_ROLE_DATA = {
    "resourceType": "PractitionerRole",
    "id": TEST_PRACTITIONER_ROLE_ID,
    "active": True,
    "period": {"start": "2012-01-01", "end": "2012-03-31"},
    "practitioner": {
        "reference": f"Practitioner/{TEST_PRACTITIONER_ID}",
        "display": "Dr Adam Careful",
    },
    "availableTime": [
        {
            "daysOfWeek": ["mon", "tue", "wed"],
            "availableStartTime": "09:00:00",
            "availableEndTime": "16:30:00",
        },
        {
            "daysOfWeek": ["thu", "fri"],
            "availableStartTime": "09:00:00",
            "availableEndTime": "12:00:00",
        },
    ],
}

SCHEDULE_DATA = {
    "resourceType": "Schedule",
    "id": TEST_SCHEDULE_ID,
    "active": True,
    "actor": [
        {
            "reference": "PractitionerRole/" + TEST_PRACTITIONER_ROLE_ID,
            "display": "PractitionerRole: " + TEST_PRACTITIONER_ROLE_ID,
        }
    ],
    "planningHorizon": {
        "start": PRACTITIONER_ROLE_DATA["period"]["start"],
        "end": PRACTITIONER_ROLE_DATA["period"]["end"],
    },
    "comment": "auto generated schedule on practitioner role creation",
}

SCHEDULE_SEARCH_DATA = {
    "entry": [
        {
            "fullUrl": "https://dummy-search-url",
            "resource": SCHEDULE_DATA,
            "search": {"mode": "match"},
        }
    ],
    "link": [],
    "total": 1,
    "type": "searchset",
    "resourceType": "Bundle",
}


def test_update_practitioner_role():
    def mock_search(resource_type, search):
        assert resource_type == "Schedule"
        assert ("actor", TEST_PRACTITIONER_ROLE_ID) in search
        assert ("active", str(True)) in search
        return construct_fhir_element("Bundle", SCHEDULE_SEARCH_DATA)

    def mock_put_resource(resource_id, resource):
        if resource.resource_type == "Schedule":
            assert resource_id == TEST_SCHEDULE_ID
            return construct_fhir_element("Schedule", SCHEDULE_DATA)
        if resource.resource_type == "PractitionerRole":
            assert resource_id == TEST_PRACTITIONER_ROLE_ID
            return construct_fhir_element("PractitionerRole", PRACTITIONER_ROLE_DATA)
        assert False, "not expected resource type"

    resource_client = MockResourceClient()
    resource_client.search = mock_search
    resource_client.put_resource = mock_put_resource
    controller = PractitionerRoleController(resource_client)

    role = PRACTITIONER_ROLE_DATA
    request = FakeRequest(
        data=role,
        claims={
            "roles": {
                "Practitioner": {
                    "id": TEST_PRACTITIONER_ID,
                },
            },
        },
    )
    resp = controller.update_practitioner_role(request, role["id"])
    assert resp.status_code == 200

    resp_data = json.loads(resp.data)
    assert resp_data["practitioner_role"] == PRACTITIONER_ROLE_DATA
    assert resp_data["schedule"] == SCHEDULE_DATA


def test_update_practitioner_role_return_400_if_role_id_in_url_mismatch():
    resource_client = MockResourceClient()
    controller = PractitionerRoleController(resource_client)

    role = PRACTITIONER_ROLE_DATA
    mismatch_id = "mismatch-id"
    request = FakeRequest(
        data=role,
        claims={
            "roles": {
                "Practitioner": {
                    "id": TEST_PRACTITIONER_ID,
                },
            },
        },
    )
    resp = controller.update_practitioner_role(request, mismatch_id)
    assert resp.status_code == 400
    assert resp.data == b"role_id mismatch"


def test_update_practitioner_role_return_401_when_updating_others_practitioner_role():
    resource_client = MockResourceClient()
    controller = PractitionerRoleController(resource_client)

    role = PRACTITIONER_ROLE_DATA
    mismatch_id = "mismatch-id"
    request = FakeRequest(
        data=role,
        claims={
            "roles": {
                "Practitioner": {
                    "id": mismatch_id,
                },
            },
        },
    )
    resp = controller.update_practitioner_role(request, role["id"])
    assert resp.status_code == 401
    assert (
        resp.data
        == b"can only change practitioner role referencing to the practitioner"
    )


def test_update_practitioner_role_returns_500_if_there_is_no_active_schedule_for_the_practitioner_role():
    def mock_search(resource_type, search):
        search_result = SCHEDULE_SEARCH_DATA
        search_result["entry"] = None
        return construct_fhir_element("Bundle", search_result)

    resource_client = MockResourceClient()
    resource_client.search = mock_search
    controller = PractitionerRoleController(resource_client)

    role = PRACTITIONER_ROLE_DATA
    request = FakeRequest(
        data=role,
        claims={
            "roles": {
                "Practitioner": {
                    "id": TEST_PRACTITIONER_ID,
                },
            },
        },
    )
    resp = controller.update_practitioner_role(request, role["id"])
    assert resp.status_code == 500
    assert resp.data == b"(unexpected) the practitioner role is missing active schedule"
