import copy
import datetime
import json

from fhir.resources import construct_fhir_element
from helper import MockResourceClient

from blueprints.lists import ListsController, get_spot_counts

LIST_DATA = {
    "resourceType": "List",
    "id": "test-id-98712653",
    "status": "current",
    "mode": "working",
    "title": "Patient Queue",
}

LIST_DATA_WITH_TWO_ITEMS = {
    "resourceType": "List",
    "id": "test-id-98712653",
    "status": "current",
    "mode": "working",
    "title": "Patient Queue",
    "entry": [
        {"item": {"reference": "Patient/1"}},
        {"item": {"reference": "Patient/2"}},
    ],
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


PRACTITIONER_ROLE_DATA = {
    "entry": [
        {
            "fullUrl": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/PractitionerRole/d163509d-82c1-4c75-aab6-bf55c4c5bf9f",  # noqa
            "resource": {
                "id": "d163509d-82c1-4c75-aab6-bf55c4c5bf9f",
                "meta": {
                    "lastUpdated": datetime.datetime(
                        2023, 1, 5, 9, 34, 20, 678898, tzinfo=datetime.timezone.utc
                    ),
                    "versionId": "MTY3MjkxMTI2MDY3ODg5ODAwMA",
                },
                "active": True,
                "availableTime": [
                    {
                        "availableEndTime": datetime.time(16, 30),
                        "availableStartTime": datetime.time(9, 0),
                        "daysOfWeek": ["mon", "tue", "wed"],
                    },
                    {
                        "availableEndTime": datetime.time(12, 0),
                        "availableStartTime": datetime.time(9, 0),
                        "daysOfWeek": ["thu", "fri"],
                    },
                ],
                "code": [
                    {
                        "coding": [
                            {
                                "code": "doctor",
                                "system": "http://terminology.hl7.org/CodeSystem/practitioner-role",
                            }
                        ]
                    },
                    {
                        "coding": [
                            {
                                "code": "walk-in",
                                "display": "Walk In",
                                "system": "https://www.notion.so/umed-group/code-system/practitioner-role",
                            }
                        ]
                    },
                ],
                "period": {
                    "end": datetime.date(2099, 8, 15),
                    "start": datetime.date(2021, 8, 15),
                },
                "practitioner": {
                    "display": "Given Name Last Name",
                    "reference": "Practitioner/0becdf18-5347-43e8-9578-347c667dabfd",
                },
                "resourceType": "PractitionerRole",
            },
            "search": {"mode": "match"},
        }
    ],
    "link": [
        {
            "relation": "search",
            "url": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/PractitionerRole/?_count=1&active=true&date=lt2023-01-05&date=gt2023-01-05&role=walk-in&role=doctor",  # noqa
        },
        {
            "relation": "next",
            "url": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/PractitionerRole/?_count=1&active=true&date=lt2023-01-05&date=gt2023-01-05&role=walk-in&role=doctor&_page_token=AbToyDv_FHrLG7A55xg3xwI77746CSmPhW90r9i9Pl7HjAQU0R-OhW8D-8HWfqbbccnOrv9sDzhpheLajoXmmqC3VSaMyGj5CJX1lMY9le3K0HQZ1wyRuav_UeczQwitRy0hvfIcvZrhO3bsbvRTSUV_tWewXrzek_GUaTTO2vzOkBwABNLMli0VkjMJtq_WVDuxMz4%3D",  # noqa
        },
        {
            "relation": "first",
            "url": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/PractitionerRole/?_count=1&active=true&date=lt2023-01-05&date=gt2023-01-05&role=walk-in&role=doctor",  # noqa
        },
        {
            "relation": "self",
            "url": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/PractitionerRole/?_count=1&active=true&date=lt2023-01-05&date=gt2023-01-05&role=walk-in&role=doctor",  # noqa
        },
    ],
    "total": 130,
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


def test_get_list_len():
    def mock_get_resource(list_id, resource_type):
        assert resource_type == "List"
        return construct_fhir_element("List", LIST_DATA_WITH_TWO_ITEMS)

    resource_client = MockResourceClient()
    resource_client.get_resource = mock_get_resource

    controller = ListsController(resource_client)
    expected_entry_len = 2
    resp = controller.get_list_len(LIST_DATA_WITH_TWO_ITEMS["id"])
    assert resp.status_code == 200
    result = json.loads(resp.data)["data"]
    assert result == expected_entry_len


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


def test_get_spot_counts():
    roles = construct_fhir_element("Bundle", PRACTITIONER_ROLE_DATA)
    # 2012/2/6 is Monday
    time = datetime.datetime(2012, 2, 6, 10, 0, 0).time()
    actual_total_spots = get_spot_counts(420, "mon", time, roles.entry)

    # (16:30(availableEndTime) - 10:00)//420
    expected_total_spots = 55

    assert actual_total_spots == expected_total_spots
