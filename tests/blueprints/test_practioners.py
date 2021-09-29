import json
from unittest.mock import patch

from fhir.resources import construct_fhir_element
from helper import MockResourceClient

from blueprints.practitioners import PractitionerController

PRACTITIONER_DATA = {
    "resourceType": "Practitioner",
    "id": "dummy-practitioner-id",
    "meta": {
        "lastUpdated": "2021-08-25T12:54:12.931026+00:00",
        "versionId": "MTYyOTg5NjA1MjkzMTAyNjAwMA",
    },
    "gender": "male",
    "birthDate": "1971-11-01",
    "active": "true",
    "telecom": [{"system": "email", "value": "test@umed.jp", "use": "work"}],
    "name": [
        {
            "family": "水田",
            "given": ["万理"],
            "extension": [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/iso21090-EN-representation",
                    "valueCode": "IDE",
                }
            ],
        },
        {
            "family": "みずた",
            "given": ["まり"],
            "extension": [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/iso21090-EN-representation",
                    "valueCode": "SYL",
                }
            ],
        },
        {
            "family": "Mizuta",
            "given": ["Mari"],
            "extension": [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/iso21090-EN-representation",
                    "valueCode": "ABC",
                }
            ],
        },
    ],
}


PRACTITIONER_SEARCH_DATA = {
    "entry": [
        {
            "fullUrl": "https://healthcare.googleapis.com/v1/projects/dummy-fhir-path",
            "resource": PRACTITIONER_DATA,
            "search": {"mode": "match"},
        }
    ],
    "link": [
        {
            "relation": "search",
            "url": "https://healthcare.googleapis.com/v1/projects/dummy-fhir-path/Practitioner/?actor=9e477534-b74a-4139-9338-90977e81bc34&date=ge2021-08-25",  # noqa: E501
        },
        {
            "relation": "first",
            "url": "https://healthcare.googleapis.com/v1/projects/dummy-fhir-path/fhirStores/phat-fhir-store-id/fhir/Practitioner/?actor=9e477534-b74a-4139-9338-90977e81bc34&date=ge2021-08-25",  # noqa: E501
        },
        {
            "relation": "self",
            "url": "https://healthcare.googleapis.com/v1/projects/dummy-fhir-path/fhirStores/phat-fhir-store-id/fhir/Practitioner/?actor=9e477534-b74a-4139-9338-90977e81bc34&date=ge2021-08-25",  # noqa: E501
        },
    ],
    "total": 1,
    "type": "searchset",
    "resourceType": "Bundle",
}


def test_create_practioner(mocker):
    request = FakeRequest(
        data=PRACTITIONER_DATA, claims={"uid": "test-uid", "email_verified": True}
    )
    mock_resource = MockResourceClient()

    with patch("blueprints.practitioners.role_auth") as mock_role_auth:
        controller = PractitionerController(mock_resource)

        practitioner = controller.create_practitioner(request)

        assert practitioner.id == "id1"
        mock_role_auth.grant_role.assert_called_once_with(
            {"uid": "test-uid", "email_verified": True}, "Practitioner", "id1"
        )


def test_search_practitioner(mocker):
    email = "test@umed.jp"

    def mock_search(resource_type, search):
        assert resource_type == "Practitioner"
        assert ("email", email) in search
        return construct_fhir_element("Bundle", PRACTITIONER_SEARCH_DATA)

    resource_client = MockResourceClient()
    resource_client.search = mock_search

    request = FakeRequest(args={"email": email})
    controller = PractitionerController(resource_client)
    resp = controller.search_practitioners(request)
    resp_data = resp.data.decode("utf-8")

    assert resp.status_code == 200
    assert (
        json.loads(resp_data)["data"][0]["id"]
        == PRACTITIONER_SEARCH_DATA["entry"][0]["resource"]["id"]
    )


class FakeRequest:
    def __init__(self, data={}, args={}, claims=None):
        self.data = data
        self.claims = claims
        self.args = args

    def get_json(self):
        return self.data

    def args(self):
        return self.args
