import json

from fhir.resources import construct_fhir_element
from helper import FakeRequest, MockResourceClient

from blueprints.consents import ConsentsController

PRIMARY_PATIENT_ID = "3b07bb42-a7cf-4ca2-b7f9-4f1d6cd0e2ef"
SECONDARY_PATIENT_ID = "b9748438-fd5f-4999-8d5a-109e537ff7d7"
CONSENT_SEARCH_DATA = {
    "entry": [
        {
            "fullUrl": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/Consent/892bf5d9-a568-4914-9bf4-1bb87b32f921",  # noqa
            "resource": {
                "id": "892bf5d9-a568-4914-9bf4-1bb87b32f921",
                "meta": {
                    "lastUpdated": "2022-11-06T01:27:17.388690+00:00",
                    "versionId": "MTY2NzY5ODAzNzM4ODY5MDAwMA",
                },
                "category": [
                    {
                        "coding": [
                            {
                                "code": "ACALL",
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                            }
                        ]
                    }
                ],
                "patient": {"reference": f"Patient/{SECONDARY_PATIENT_ID}"},
                "policyRule": {
                    "coding": [
                        {
                            "code": "ACALL",
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                        }
                    ]
                },
                "provision": {
                    "actor": [
                        {
                            "reference": {"reference": f"Patient/{PRIMARY_PATIENT_ID}"},
                            "role": {"text": "grantee"},
                        }
                    ],
                    "type": "permit",
                },
                "scope": {"text": "all access"},
                "status": "active",
                "resourceType": "Consent",
            },
            "search": {"mode": "match"},
        }
    ],
    "link": [
        {
            "relation": "search",
            "url": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/Consent/?_count=300&actor=3b07bb42-a7cf-4ca2-b7f9-4f1d6cd0e2ef",  # noqa
        },
        {
            "relation": "first",
            "url": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/Consent/?_count=300&actor=3b07bb42-a7cf-4ca2-b7f9-4f1d6cd0e2ef",  # noqa
        },
        {
            "relation": "self",
            "url": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/Consent/?_count=300&actor=3b07bb42-a7cf-4ca2-b7f9-4f1d6cd0e2ef",  # noqa
        },
    ],
    "total": 1,
    "type": "searchset",
    "resourceType": "Bundle",
}
EMPTY_CONSENT_SEARCH_DATA = {
    "entry": [],
    "link": [
        {
            "relation": "search",
            "url": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/Consent/?_count=300&actor=3b07bb42-a7cf-4ca2-b7f9-4f1d6cd0e2ef",  # noqa
        },
        {
            "relation": "first",
            "url": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/Consent/?_count=300&actor=3b07bb42-a7cf-4ca2-b7f9-4f1d6cd0e2ef",  # noqa
        },
        {
            "relation": "self",
            "url": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/Consent/?_count=300&actor=3b07bb42-a7cf-4ca2-b7f9-4f1d6cd0e2ef",  # noqa
        },
    ],
    "total": 0,
    "type": "searchset",
    "resourceType": "Bundle",
}


def test_search_consents_with_grantee_only():
    def mock_search(resource_type: str, search: list):
        assert resource_type == "Consent"
        assert ("actor", PRIMARY_PATIENT_ID) in search
        return construct_fhir_element("Bundle", CONSENT_SEARCH_DATA)

    resource_client = MockResourceClient()
    resource_client.search = mock_search

    request = FakeRequest(
        args={"grantee": PRIMARY_PATIENT_ID},
        claims={
            "roles": {
                "Patient": {
                    "id": PRIMARY_PATIENT_ID,
                    "delegates": [SECONDARY_PATIENT_ID],
                },
            },
        },
    )

    controller = ConsentsController(resource_client)
    resp = controller.search(request)
    assert resp.status_code == 200

    data = json.loads(resp.data)["data"]
    secondary_ref_id = f"Patient/{SECONDARY_PATIENT_ID}"
    assert data[0]["patient"]["reference"] == secondary_ref_id


def test_search_consents_with_grantee_and_patient():
    def mock_search(resource_type: str, search: list):
        assert resource_type == "Consent"
        assert ("actor", PRIMARY_PATIENT_ID) in search
        assert ("patient", SECONDARY_PATIENT_ID) in search
        return construct_fhir_element("Bundle", CONSENT_SEARCH_DATA)

    resource_client = MockResourceClient()
    resource_client.search = mock_search

    request = FakeRequest(
        args={"grantee": PRIMARY_PATIENT_ID, "patient": SECONDARY_PATIENT_ID},
        claims={
            "roles": {
                "Patient": {
                    "id": PRIMARY_PATIENT_ID,
                    "delegates": [SECONDARY_PATIENT_ID],
                },
            },
        },
    )

    controller = ConsentsController(resource_client)
    resp = controller.search(request)
    assert resp.status_code == 200

    data = json.loads(resp.data)["data"]
    secondary_ref_id = f"Patient/{SECONDARY_PATIENT_ID}"
    assert data[0]["patient"]["reference"] == secondary_ref_id


def test_search_consents_when_empty_result():
    dummy_grantee = "dummy-grantee-id"

    def mock_search(resource_type: str, search: list):
        assert resource_type == "Consent"
        assert ("actor", dummy_grantee) in search
        return construct_fhir_element("Bundle", EMPTY_CONSENT_SEARCH_DATA)

    resource_client = MockResourceClient()
    resource_client.search = mock_search

    request = FakeRequest(
        args={"grantee": dummy_grantee},
        claims={
            "roles": {
                "Patient": {
                    "id": dummy_grantee,
                },
            },
        },
    )

    controller = ConsentsController(resource_client)
    resp = controller.search(request)
    assert resp.status_code == 200

    data = json.loads(resp.data)["data"]
    assert len(data) == 0


def test_search_consents_returns_bad_request_when_no_grantee_and_no_patient():
    resource_client = MockResourceClient()

    request = FakeRequest(
        args={},
        claims={
            "roles": {
                "Patient": {
                    "id": PRIMARY_PATIENT_ID,
                    "delegates": [SECONDARY_PATIENT_ID],
                },
            },
        },
    )

    controller = ConsentsController(resource_client)
    resp = controller.search(request)
    assert resp.status_code == 400
    assert resp.data == b"grantee or patient must be provided"


def test_search_consents_not_authorized_for_patient_id():
    resource_client = MockResourceClient()
    non_authorized_patient_id = "non-authorized-patient-id"

    request = FakeRequest(
        args={"patient": non_authorized_patient_id},
        claims={
            "roles": {
                "Patient": {
                    "id": PRIMARY_PATIENT_ID,
                    "delegates": [SECONDARY_PATIENT_ID],
                },
            },
        },
    )

    controller = ConsentsController(resource_client)
    resp = controller.search(request)
    assert resp.status_code == 401
    assert resp.data == b"Not Authorized for Consent Search (patient_id)"


def test_search_consents_not_authorized_for_grantee():
    resource_client = MockResourceClient()
    non_authorized_grantee = "non-authorized-grantee"

    request = FakeRequest(
        args={"grantee": non_authorized_grantee},
        claims={
            "roles": {
                "Patient": {
                    "id": PRIMARY_PATIENT_ID,
                    "delegates": [SECONDARY_PATIENT_ID],
                },
            },
        },
    )

    controller = ConsentsController(resource_client)
    resp = controller.search(request)
    assert resp.status_code == 401
    assert resp.data == b"Not Authorized for Consent Search (grantee_id)"
