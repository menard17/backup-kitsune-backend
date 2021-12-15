import uuid
from datetime import datetime

import pytz
from fhir.resources import construct_fhir_element
from helper import FakeRequest, MockResourceClient

from blueprints.document_references import DocumentReferenceController
from tests.blueprints.test_appointments import BOOKED_APPOINTMENT_DATA

TEST_PATIENT_ID = "ec39753c-0f63-4c8b-b654-011ec5c0295f"
DOCUMENT_REFERENCE_POST_REQUEST = {
    "subject": f"Patient/{TEST_PATIENT_ID}",
    "document_type": "medical_record",
    "pages": [
        {
            "url": "http://example.org/xds/mhd/Binary/07a6483f-732b-461e-86b6-edb665c45510",
            "title": "Page 1",
        },
        {
            "url": "http://example.org/xds/mhd/Binary/07a6483f-732b-461e-86b6-edb665c45510",
            "title": "Page 2",
        },
        {
            "url": "http://example.org/xds/mhd/Binary/07a6483f-732b-461e-86b6-edb665c45510",
            "title": "Page 3",
        },
        {
            "url": "http://example.org/xds/mhd/Binary/07a6483f-732b-461e-86b6-edb665c45510",
            "title": "Page 4",
        },
    ],
}

DOCUMENT_REFERENCE_DATA = {
    "resourceType": "DocumentReference",
    "status": "current",
    "subject": {"reference": f"Patient/{TEST_PATIENT_ID}"},
    "date": "2018-12-24T09:43:41+11:00",
    "type": {"coding": [{"code": "34108-1", "display": "Outpatient Note"}]},
    "content": [
        {
            "attachment": {
                "contentType": "application/hl7-v3+xml",
                "language": "en-US",
                "url": "http://example.org/xds/mhd/Binary/07a6483f-732b-461e-86b6-edb665c45510",
                "size": 3654,
                "hash": "2jmj7l5rSw0yVb/vlWAYkK/YBwk=",
                "title": "Physical",
                "creation": "2005-12-24T09:35:00+11:00",
            },
            "format": {
                "system": "urn:oid:1.3.6.1.4.1.19376.1.2.3",
                "code": "urn:ihe:pcc:handp:2008",
                "display": "History and Physical Specification",
            },
        }
    ],
}

DOCUMENT_REFERENCE_SEARCH_DATA = {
    "entry": [
        {
            "fullUrl": "https://healthcare.googleapis.com/v1/projects/dummy-fhir-path",
            "resource": DOCUMENT_REFERENCE_DATA,
            "search": {"mode": "match"},
        }
    ],
    "link": [],
    "total": 1,
    "type": "searchset",
    "resourceType": "Bundle",
}


def test_create_document_reference_for_oneself():
    def mock_create_resource(uid, resource):
        return resource

    def mock_search_resource(resource_type, search):
        return construct_fhir_element("Bundle", DOCUMENT_REFERENCE_SEARCH_DATA)

    def mock_patch_resource(uid, type, valuset):
        return BOOKED_APPOINTMENT_DATA

    resource_client = MockResourceClient()
    resource_client.create_source = mock_create_resource
    resource_client.search = mock_search_resource
    resource_client.patch_resource = mock_patch_resource

    controller = DocumentReferenceController(resource_client)
    req = FakeRequest(
        data=DOCUMENT_REFERENCE_POST_REQUEST,
        claims={"roles": {"Patient": {"id": TEST_PATIENT_ID}}},
    )
    resp = controller.create_document_reference(req)

    assert resp.status_code == 201


def test_create_document_reference_for_oneself_no_old_documents():
    def mock_create_resource(uid, resource):
        return resource

    def mock_search_resource(resource_type, search):
        return construct_fhir_element(
            "Bundle",
            {
                "entry": [],
                "link": [],
                "total": 1,
                "type": "searchset",
                "resourceType": "Bundle",
            },
        )

    def mock_patch_resource(uid, type, valuset):
        return BOOKED_APPOINTMENT_DATA

    resource_client = MockResourceClient()
    resource_client.create_source = mock_create_resource
    resource_client.search = mock_search_resource
    resource_client.patch_resource = mock_patch_resource

    controller = DocumentReferenceController(resource_client)
    req = FakeRequest(
        data=DOCUMENT_REFERENCE_POST_REQUEST,
        claims={"roles": {"Patient": {"id": TEST_PATIENT_ID}}},
    )
    resp = controller.create_document_reference(req)

    assert resp.status_code == 201


def test_create_document_reference_for_someoneelse():
    def mock_create_resource(uid, resource):
        return resource

    def mock_search_resource(resource_type, search):
        return construct_fhir_element("Bundle", DOCUMENT_REFERENCE_SEARCH_DATA)

    def mock_patch_resource(uid, type, valuset):
        return BOOKED_APPOINTMENT_DATA

    resource_client = MockResourceClient()
    resource_client.create_source = mock_create_resource
    resource_client.search = mock_search_resource
    resource_client.patch_resource = mock_patch_resource

    controller = DocumentReferenceController(resource_client)
    req = FakeRequest(
        data=DOCUMENT_REFERENCE_POST_REQUEST,
        claims={"roles": {"Patient": {"id": str(uuid.uuid4())}}},
    )
    resp = controller.create_document_reference(req)

    assert resp.status_code == 403
    assert resp.data == b"patient can only create document references for him/herself"


def test_search_document_reference_for_oneself():

    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    expected_search_date = now.date().isoformat()  # defaults to current date

    def mock_search_resource(resource_type, search):
        return construct_fhir_element("Bundle", DOCUMENT_REFERENCE_SEARCH_DATA)

    resource_client = MockResourceClient()
    resource_client.search = mock_search_resource

    controller = DocumentReferenceController(resource_client)
    req = FakeRequest(
        args={
            "date": f"le{expected_search_date}",
            "subject": f"Patient/{TEST_PATIENT_ID}",
            "documentation_type": "insurance_card",
        },
        claims={"roles": {"Patient": {"id": TEST_PATIENT_ID}}},
    )
    resp = controller.search_document_reference(req)

    assert resp.status_code == 200


def test_search_document_reference_for_someoneelese():

    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    expected_search_date = now.date().isoformat()  # defaults to current date

    def mock_search_resource(resource_type, search):
        return construct_fhir_element("Bundle", DOCUMENT_REFERENCE_SEARCH_DATA)

    resource_client = MockResourceClient()
    resource_client.search = mock_search_resource

    controller = DocumentReferenceController(resource_client)
    req = FakeRequest(
        args={
            "date": f"le{expected_search_date}",
            "subject": f"Patient/{str(uuid.uuid4())}",
            "documentation_type": "insurance_card",
        },
        claims={"roles": {"Patient": {"id": TEST_PATIENT_ID}}},
    )
    resp = controller.search_document_reference(req)

    assert resp.status_code == 403
    assert resp.data == b"patient can only search document references for him/herself"


def test_search_document_reference_without_subject():

    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    expected_search_date = now.date().isoformat()  # defaults to current date

    def mock_search_resource(resource_type, search):
        return construct_fhir_element("Bundle", DOCUMENT_REFERENCE_SEARCH_DATA)

    resource_client = MockResourceClient()
    resource_client.search = mock_search_resource

    controller = DocumentReferenceController(resource_client)
    req = FakeRequest(
        args={
            "date": f"le{expected_search_date}",
            "subject": "XXXXXX",
            "documentation_type": "insurance_card",
        },
        claims={"roles": {"Patient": {"id": TEST_PATIENT_ID}}},
    )
    resp = controller.search_document_reference(req)

    assert resp.status_code == 400


def test_search_document_reference_with_invalid_subject():

    tokyo_timezone = pytz.timezone("Asia/Tokyo")
    now = tokyo_timezone.localize(datetime.now())
    expected_search_date = now.date().isoformat()  # defaults to current date

    def mock_search_resource(resource_type, search):
        return construct_fhir_element("Bundle", DOCUMENT_REFERENCE_SEARCH_DATA)

    resource_client = MockResourceClient()
    resource_client.search = mock_search_resource

    controller = DocumentReferenceController(resource_client)
    req = FakeRequest(
        args={
            "date": f"le{expected_search_date}",
            "documentation_type": "insurance_card",
        },
        claims={"roles": {"Patient": {"id": TEST_PATIENT_ID}}},
    )
    resp = controller.search_document_reference(req)

    assert resp.status_code == 400
