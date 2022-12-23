import copy
import json

from fhir.resources import construct_fhir_element
from helper import MockResourceClient

from blueprints.lists import ListsController

LIST_DATA = {
    "resourceType": "List",
    "id": "test-id-98712653",
    "status": "current",
    "mode": "working",
    "title": "Patient Queue",
}


SEARCH_LIST_DATA = {
    "entry": [
        {
            "fullUrl": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/List/8e16a8b7-060a-4ff2-b45a-0ffbaba2b415",  # noqa
            "resource": {
                "id": "8e16a8b7-060a-4ff2-b45a-0ffbaba2b415",
                "meta": {
                    "lastUpdated": "2022-11-06T01:27:17.388690+00:00",
                    "versionId": "MTY3MTI4ODYyMjYwNzAxMzAwMA",
                },
                "mode": "working",
                "status": "current",
                "title": "Patient Queue",
                "resourceType": "List",
            },
            "search": {"mode": "match"},
        }
    ],
    "link": [
        {
            "relation": "search",
            "url": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/List/?_count=300",  # noqa
        },
        {
            "relation": "first",
            "url": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/List/?_count=300",  # noqa
        },
        {
            "relation": "self",
            "url": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/List/?_count=300",  # noqa
        },
    ],
    "total": 1,
    "type": "searchset",
    "resourceType": "Bundle",
}


def test_create_list():
    def mock_create_resource(fhir_list):
        assert fhir_list.status == "current"
        assert fhir_list.mode == "working"
        assert fhir_list.title == "Patient Queue"
        return construct_fhir_element("List", LIST_DATA)

    resource_client = MockResourceClient()
    resource_client.create_resource = mock_create_resource

    controller = ListsController(resource_client)
    resp = controller.create()
    assert resp.status_code == 201
    assert json.loads(resp.data)["id"] == LIST_DATA["id"]


def test_get_lists():
    def mock_get_resources(resource_type):
        assert resource_type == "List"
        return construct_fhir_element("Bundle", SEARCH_LIST_DATA)

    resource_client = MockResourceClient()
    resource_client.get_resources = mock_get_resources

    controller = ListsController(resource_client)
    resp = controller.get_lists()
    assert resp.status_code == 200

    expected_id = SEARCH_LIST_DATA["entry"][0]["resource"]["id"]
    results = json.loads(resp.data)["data"]["entry"]
    assert results[0]["resource"]["id"] == expected_id


def test_get_a_list():
    def mock_get_resource(list_id, resource_type):
        assert resource_type == "List"
        assert list_id == LIST_DATA["id"]
        return construct_fhir_element("List", LIST_DATA)

    resource_client = MockResourceClient()
    resource_client.get_resource = mock_get_resource

    controller = ListsController(resource_client)
    resp = controller.get_a_list(LIST_DATA["id"])
    assert resp.status_code == 200
    result = json.loads(resp.data)["data"]
    assert result["id"] == LIST_DATA["id"]


def test_create_entry():
    test_etag = "w/23"
    patient_id = "dummy-patient-id"

    def mock_get_resource(list_id, resource_type):
        assert resource_type == "List"
        assert list_id == LIST_DATA["id"]
        return construct_fhir_element("List", LIST_DATA)

    def mock_put_resource(list_id, fhir_list, lock_header):
        assert lock_header == test_etag
        assert fhir_list.entry[0]["item"]["reference"] == f"Patient/{patient_id}"
        assert list_id == LIST_DATA["id"]
        return construct_fhir_element("List", fhir_list)

    resource_client = MockResourceClient()
    resource_client.last_seen_etag = test_etag
    resource_client.get_resource = mock_get_resource
    resource_client.put_resource = mock_put_resource

    controller = ListsController(resource_client)
    resp = controller.create_entry(LIST_DATA["id"], patient_id)
    assert resp.status_code == 201
    result = json.loads(resp.data)["data"]
    assert result["id"] == LIST_DATA["id"]
    assert result["entry"][0]["item"]["reference"] == f"Patient/{patient_id}"


def test_create_entry_returns_bad_request_when_patient_already_in_list():
    test_list = copy.deepcopy(LIST_DATA)
    patient_id = "dummy-patient-id"
    test_list["entry"] = [{"item": {"reference": f"Patient/{patient_id}"}}]

    def mock_get_resource(list_id, resource_type):
        assert resource_type == "List"
        assert list_id == LIST_DATA["id"]
        return construct_fhir_element("List", test_list)

    resource_client = MockResourceClient()
    resource_client.get_resource = mock_get_resource

    controller = ListsController(resource_client)
    controller = ListsController(resource_client)
    resp = controller.create_entry(LIST_DATA["id"], patient_id)
    assert resp.status_code == 400
    assert resp.data == b"Patient already in the list"


def test_delete_entry():
    test_etag = "w/23"
    test_list = copy.deepcopy(LIST_DATA)
    patient_id = "dummy-patient-id"
    test_list["entry"] = [{"item": {"reference": f"Patient/{patient_id}"}}]

    def mock_get_resource(list_id, resource_type):
        assert resource_type == "List"
        assert list_id == LIST_DATA["id"]
        return construct_fhir_element("List", test_list)

    def mock_put_resource(list_id, fhir_list, lock_header):
        assert lock_header == test_etag
        assert list_id == LIST_DATA["id"]
        return construct_fhir_element("List", fhir_list)

    resource_client = MockResourceClient()
    resource_client.last_seen_etag = test_etag
    resource_client.get_resource = mock_get_resource
    resource_client.put_resource = mock_put_resource

    controller = ListsController(resource_client)
    resp = controller.delete_entry(LIST_DATA["id"], patient_id)
    assert resp.status_code == 200
    result = json.loads(resp.data)["data"]
    assert result["id"] == LIST_DATA["id"]
    assert len(result["entry"]) == 0


def test_delete_entry_returns_bad_request_when_patient_not_in_list():
    test_etag = "w/23"
    test_list = copy.deepcopy(LIST_DATA)
    patient_id = "dummy-patient-id"
    another_patient_id = "another-patient-id"
    test_list["entry"] = [{"item": {"reference": f"Patient/{patient_id}"}}]

    def mock_get_resource(list_id, resource_type):
        assert resource_type == "List"
        assert list_id == LIST_DATA["id"]
        return construct_fhir_element("List", test_list)

    resource_client = MockResourceClient()
    resource_client.last_seen_etag = test_etag
    resource_client.get_resource = mock_get_resource

    controller = ListsController(resource_client)
    resp = controller.delete_entry(LIST_DATA["id"], another_patient_id)
    assert resp.status_code == 400
    assert resp.data == b"Patient not in the list"
