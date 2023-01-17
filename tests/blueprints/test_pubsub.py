import base64
import datetime
from unittest import mock
from unittest.mock import Mock

import pytest
from fhir.resources.bundle import Bundle

from blueprints.pubsub import PubsubController
from tests.blueprints.helper import FakeRequest, MockResourceClient

ENCOUNTER_BUNDLE_DATA = {
    "entry": [
        {
            "fullUrl": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/Encounter/579fa116-251d-4a9b-9a69-3ab03b573452",  # noqa: E501
            "resource": {
                "id": "579fa116-251d-4a9b-9a69-3ab03b573452",
                "meta": {
                    "lastUpdated": datetime.datetime(
                        2022, 9, 5, 13, 15, 57, 277240, tzinfo=datetime.timezone.utc
                    ),
                    "versionId": "MTY2MjM4Mzc1NzI3NzI0MDAwMA",
                },
                "account": [
                    {"reference": "Account/393631e9-7a1d-48ac-a733-0bd649ca3d68"}
                ],
                "appointment": [
                    {"reference": "Appointment/8ed8a19a-e04e-43f2-8da1-beaae3dd4d97"}
                ],
                "class": {
                    "code": "HH",
                    "display": "home health",
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                },
                "participant": [
                    {
                        "individual": {
                            "reference": "PractitionerRole/9de70669-1d0d-4d54-a241-3cb4047631e0"
                        }
                    }
                ],
                "status": "in-progress",
                "subject": {
                    "reference": "Patient/02989bec-b084-47d9-99fd-259ac6f3360c"
                },
                "resourceType": "Encounter",
            },
            "search": {"mode": "match"},
        },
        {
            "fullUrl": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/Account/393631e9-7a1d-48ac-a733-0bd649ca3d68",  # noqa: E501
            "resource": {
                "id": "393631e9-7a1d-48ac-a733-0bd649ca3d68",
                "meta": {
                    "lastUpdated": datetime.datetime(
                        2022, 9, 5, 13, 15, 57, 277240, tzinfo=datetime.timezone.utc
                    ),
                    "versionId": "MTY2MjM4Mzc1NzI3NzI0MDAwMA",
                },
                "guarantor": [
                    {
                        "onHold": False,
                        "party": {
                            "reference": "Patient/02989bec-b084-47d9-99fd-259ac6f3360c"
                        },
                    }
                ],
                "status": "active",
                "subject": [
                    {"reference": "Patient/02989bec-b084-47d9-99fd-259ac6f3360c"}
                ],
                "type": {
                    "coding": [
                        {
                            "code": "PBILLACCT",
                            "display": "patient billing account",
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                        }
                    ],
                    "text": "patient",
                },
                "resourceType": "Account",
            },
            "search": {"mode": "include"},
        },
        {
            "fullUrl": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/Appointment/8ed8a19a-e04e-43f2-8da1-beaae3dd4d97",  # noqa: E501
            "resource": {
                "id": "8ed8a19a-e04e-43f2-8da1-beaae3dd4d97",
                "meta": {
                    "lastUpdated": datetime.datetime(
                        2022, 9, 5, 13, 15, 57, 719856, tzinfo=datetime.timezone.utc
                    ),
                    "versionId": "MTY2MjM4Mzc1NzcxOTg1NjAwMA",
                },
                "appointmentType": {
                    "coding": [
                        {
                            "code": "FOLLOWUP",
                            "display": "A follow up visit from a previous appointment",
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0276",
                        }
                    ]
                },
                "description": "Booking practitioner role",
                "end": datetime.datetime(
                    2022,
                    9,
                    5,
                    10,
                    40,
                    tzinfo=datetime.timezone(datetime.timedelta(seconds=32400)),
                ),
                "participant": [
                    {
                        "actor": {
                            "reference": "Patient/02989bec-b084-47d9-99fd-259ac6f3360c"
                        },
                        "required": "required",
                        "status": "accepted",
                    },
                    {
                        "actor": {
                            "reference": "PractitionerRole/9de70669-1d0d-4d54-a241-3cb4047631e0"
                        },
                        "required": "required",
                        "status": "accepted",
                    },
                ],
                "serviceCategory": [
                    {
                        "coding": [
                            {
                                "code": "17",
                                "display": "General Practice",
                                "system": "http://hl7.org/fhir/codesystem-service-category.html",
                            }
                        ]
                    }
                ],
                "serviceType": [
                    {
                        "coding": [
                            {
                                "code": "540",
                                "display": "Online Service",
                                "system": "http://hl7.org/fhir/valueset-service-type.html",
                            }
                        ]
                    }
                ],
                "slot": [{"reference": "Slot/2fabe0fd-2f26-4eee-8c40-21684f5c8e2d"}],
                "start": datetime.datetime(
                    2022,
                    9,
                    5,
                    10,
                    28,
                    tzinfo=datetime.timezone(datetime.timedelta(seconds=32400)),
                ),
                "status": "fulfilled",
                "resourceType": "Appointment",
            },
            "search": {"mode": "include"},
        },
        {
            "fullUrl": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/Patient/02989bec-b084-47d9-99fd-259ac6f3360c",  # noqa: E501
            "resource": {
                "id": "02989bec-b084-47d9-99fd-259ac6f3360c",
                "meta": {
                    "lastUpdated": datetime.datetime(
                        2022, 9, 15, 14, 4, 19, 651495, tzinfo=datetime.timezone.utc
                    ),
                    "versionId": "MTY2MzI1MDY1OTY1MTQ5NTAwMA",
                },
                "extension": [
                    {"url": "stripe-customer-id", "valueString": "test-cusomter-id"},
                    {
                        "url": "stripe-payment-method-id",
                        "valueString": "test-payment-method-id",
                    },
                    {
                        "url": "fcm-token",
                        "valueString": "test-fcm-token",
                    },
                ],
                "address": [
                    {
                        "city": "港区",
                        "country": "JP",
                        "line": ["1-1-1"],
                        "postalCode": "111-1111",
                        "state": "東京都",
                        "type": "both",
                        "use": "home",
                    }
                ],
                "birthDate": datetime.date(2020, 8, 20),
                "gender": "female",
                "name": [{"family": "Official", "given": ["Name"], "use": "official"}],
                "telecom": [
                    {
                        "extension": [{"url": "verified", "valueString": "true"}],
                        "system": "email",
                        "use": "home",
                        "value": "home-meil@gmail.com",
                    },
                    {"system": "phone", "use": "mobile", "value": "08011111111"},
                ],
                "resourceType": "Patient",
            },
            "search": {"mode": "include"},
        },
        {
            "fullUrl": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/PractitionerRole/9de70669-1d0d-4d54-a241-3cb4047631e0",  # noqa: E501
            "resource": {
                "id": "9de70669-1d0d-4d54-a241-3cb4047631e0",
                "meta": {
                    "lastUpdated": datetime.datetime(
                        2022, 9, 8, 1, 14, 54, 547531, tzinfo=datetime.timezone.utc
                    ),
                    "versionId": "MTY2MjU5OTY5NDU0NzUzMTAwMA",
                },
                "active": False,
                "availableTime": [
                    {
                        "availableEndTime": datetime.time(17, 0),
                        "availableStartTime": datetime.time(0, 0),
                        "daysOfWeek": ["tue", "wed", "thu"],
                    }
                ],
                "code": [
                    {
                        "coding": [
                            {
                                "code": "doctor",
                                "system": "http://terminology.hl7.org/CodeSystem/practitioner-role",
                            }
                        ]
                    }
                ],
                "period": {
                    "end": datetime.date(2022, 8, 27),
                    "start": datetime.date(2022, 8, 24),
                },
                "practitioner": {
                    "display": "Taro Yamada",
                    "reference": "Practitioner/8e4c7788-a439-42f7-a7fb-bf88a70ddc18",
                },
                "resourceType": "PractitionerRole",
            },
            "search": {"mode": "include"},
        },
        {
            "fullUrl": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/DocumentReference/db6a5d6b-ec83-470b-b780-90d2eea2c73f",  # noqa: E501
            "resource": {
                "id": "db6a5d6b-ec83-470b-b780-90d2eea2c73f",
                "meta": {
                    "lastUpdated": datetime.datetime(
                        2022, 9, 5, 13, 16, 12, 583785, tzinfo=datetime.timezone.utc
                    ),
                    "versionId": "MTY2MjM4Mzc3MjU4Mzc4NTAwMA",
                },
                "category": [
                    {
                        "coding": [
                            {
                                "code": "clinical-note",
                                "display": "Clinical Note",
                                "system": "http://fhir.org/guides/argonaut-clinicalnotes/CodeSystem/documentreference-category",
                            }
                        ]
                    }
                ],
                "content": [
                    {
                        "attachment": {
                            "contentType": "text/xml;charset=utf-8",
                            "creation": datetime.datetime(
                                2022,
                                9,
                                5,
                                13,
                                16,
                                12,
                                281864,
                                tzinfo=datetime.timezone.utc,
                            ),
                            "data": "VEVTVF9DTElOSUNBTF9OT1RFCg==",
                            "title": "page1",
                        }
                    }
                ],
                "context": {
                    "encounter": [
                        {"reference": "Encounter/579fa116-251d-4a9b-9a69-3ab03b573452"}
                    ]
                },
                "date": datetime.datetime(
                    2022, 9, 5, 13, 16, 12, 281870, tzinfo=datetime.timezone.utc
                ),
                "status": "current",
                "subject": {
                    "reference": "Patient/02989bec-b084-47d9-99fd-259ac6f3360c"
                },
                "type": {
                    "coding": [
                        {
                            "code": "55110-1",
                            "display": "Conclusions Document",
                            "system": "http://loinc.org",
                        }
                    ]
                },
                "resourceType": "DocumentReference",
            },
            "search": {"mode": "include"},
        },
        {
            "fullUrl": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/MedicationRequest/251149b1-ba7f-4305-a784-dc5154ccacda",  # noqa: E501
            "resource": {
                "id": "251149b1-ba7f-4305-a784-dc5154ccacda",
                "meta": {
                    "lastUpdated": datetime.datetime(
                        2022, 9, 5, 13, 16, 12, 602208, tzinfo=datetime.timezone.utc
                    ),
                    "versionId": "MTY2MjM4Mzc3MjYwMjIwODAwMA",
                },
                "encounter": {
                    "reference": "Encounter/579fa116-251d-4a9b-9a69-3ab03b573452"
                },
                "intent": "order",
                "medicationCodeableConcept": {
                    "coding": [
                        {"code": "Loxonin", "display": "ロキソニン&セルベックス"},
                        {"code": "Transamin", "display": "トランサミン"},
                    ]
                },
                "priority": "urgent",
                "requester": {
                    "reference": "PractitionerRole/9de70669-1d0d-4d54-a241-3cb4047631e0"
                },
                "status": "completed",
                "subject": {
                    "reference": "Patient/02989bec-b084-47d9-99fd-259ac6f3360c"
                },
                "resourceType": "MedicationRequest",
            },
            "search": {"mode": "include"},
        },
        {
            "fullUrl": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/ServiceRequest/8c08b7ef-4b24-43c5-a65d-321350d22f14",  # noqa: E501
            "resource": {
                "id": "8c08b7ef-4b24-43c5-a65d-321350d22f14",
                "meta": {
                    "lastUpdated": datetime.datetime(
                        2022, 9, 5, 13, 16, 12, 553194, tzinfo=datetime.timezone.utc
                    ),
                    "versionId": "MTY2MjM4Mzc3MjU1MzE5NDAwMA",
                },
                "code": {
                    "coding": [
                        {
                            "code": "Allplex SARS-CoV-2 Assay",
                            "display": "PCR検査施行",
                            "system": "ServiceRequest",
                        }
                    ]
                },
                "encounter": {
                    "reference": "Encounter/579fa116-251d-4a9b-9a69-3ab03b573452"
                },
                "intent": "order",
                "priority": "urgent",
                "requester": {
                    "reference": "PractitionerRole/9de70669-1d0d-4d54-a241-3cb4047631e0"
                },
                "status": "completed",
                "subject": {
                    "reference": "Patient/02989bec-b084-47d9-99fd-259ac6f3360c"
                },
                "resourceType": "ServiceRequest",
            },
            "search": {"mode": "include"},
        },
    ],
    "link": [
        {
            "relation": "search",
            "url": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/Encounter/?_count=300&_id=579fa116-251d-4a9b-9a69-3ab03b573452&_include=Encounter%3Aaccount&_include=Encounter%3Aappointment&_include=Encounter%3Apatient&_include=Encounter%3Apractitioner&_revinclude=DocumentReference%3Aencounter&_revinclude=MedicationRequest%3Aencounter&_revinclude=ServiceRequest%3Aencounter",  # noqa: E501
        },
        {
            "relation": "first",
            "url": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/Encounter/?_count=300&_id=579fa116-251d-4a9b-9a69-3ab03b573452&_include=Encounter%3Aaccount&_include=Encounter%3Aappointment&_include=Encounter%3Apatient&_include=Encounter%3Apractitioner&_revinclude=DocumentReference%3Aencounter&_revinclude=MedicationRequest%3Aencounter&_revinclude=ServiceRequest%3Aencounter",  # noqa: E501
        },
        {
            "relation": "self",
            "url": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/Encounter/?_count=300&_id=579fa116-251d-4a9b-9a69-3ab03b573452&_include=Encounter%3Aaccount&_include=Encounter%3Aappointment&_include=Encounter%3Apatient&_include=Encounter%3Apractitioner&_revinclude=DocumentReference%3Aencounter&_revinclude=MedicationRequest%3Aencounter&_revinclude=ServiceRequest%3Aencounter",  # noqa: E501
        },
    ],
    "total": 1,
    "type": "searchset",
    "resourceType": "Bundle",
}

INSURANCE_CARD_BUNDLE_DATA = {
    "entry": [
        {
            "fullUrl": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/DocumentReference/cebbdc53-9e44-4947-b45a-359dab89e8ea",  # noqa: E501
            "resource": {
                "id": "cebbdc53-9e44-4947-b45a-359dab89e8ea",
                "meta": {
                    "lastUpdated": datetime.datetime(
                        2022, 8, 24, 11, 44, 0, 75720, tzinfo=datetime.timezone.utc
                    ),
                    "versionId": "MTY2MTM0MTQ0MDA3NTcyMDAwMA",
                },
                "content": [
                    {
                        "attachment": {
                            "creation": datetime.datetime(
                                2022,
                                8,
                                24,
                                11,
                                43,
                                59,
                                724241,
                                tzinfo=datetime.timezone.utc,
                            ),
                            "title": "front",
                            "url": "https://test-front-url",
                        }
                    },
                    {
                        "attachment": {
                            "creation": datetime.datetime(
                                2022,
                                8,
                                24,
                                11,
                                43,
                                59,
                                724246,
                                tzinfo=datetime.timezone.utc,
                            ),
                            "title": "back",
                            "url": "https://test-back-url",
                        }
                    },
                ],
                "date": datetime.datetime(
                    2022, 8, 24, 11, 43, 59, 724248, tzinfo=datetime.timezone.utc
                ),
                "status": "current",
                "subject": {
                    "reference": "Patient/02989bec-b084-47d9-99fd-259ac6f3360c"
                },
                "type": {
                    "coding": [
                        {
                            "code": "64290-0",
                            "display": "Insurance Card",
                            "system": "http://loinc.org",
                        }
                    ]
                },
                "resourceType": "DocumentReference",
            },
            "search": {"mode": "match"},
        }
    ],
    "link": [
        {
            "relation": "search",
            "url": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/DocumentReference/?_count=300&patient=02989bec-b084-47d9-99fd-259ac6f3360c&status=current&type=64290-0",  # noqa: E501
        },
        {
            "relation": "first",
            "url": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/DocumentReference/?_count=300&patient=02989bec-b084-47d9-99fd-259ac6f3360c&status=current&type=64290-0",  # noqa: E501
        },
        {
            "relation": "self",
            "url": "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/DocumentReference/?_count=300&patient=02989bec-b084-47d9-99fd-259ac6f3360c&status=current&type=64290-0",  # noqa: E501
        },
    ],
    "total": 1,
    "type": "searchset",
    "resourceType": "Bundle",
}
# Use correct id for assertion
TEST_ENCOUNTER_ID = "579fa116-251d-4a9b-9a69-3ab03b573452"
TEST_PATIENT_ID = "02989bec-b084-47d9-99fd-259ac6f3360c"
TEST_ENCOUNTER_PAGE_ID = "test-encounter-page-id"


def test_fhir_when_no_envelope_then_return_204(
    resource_client, notion_service, orca_service, firestore_service
):
    request = FakeRequest(
        data=_generate_pubsub_message(
            action="CreateResource",
            payload_type="NameOnly",
            resource_type="Appointment",
            resource_id="test-resource-id",
        )
    )
    controller = PubsubController(
        resource_client,
        notion_service,
        orca_service,
        is_syncing_to_notion_enabled="false",
        firestore_service=firestore_service,
    )

    response = controller.fhir(request)

    assert response.status_code == 204


def test_fhir_when_no_envelope_then_return_400(
    resource_client, notion_service, orca_service, firestore_service
):
    request = FakeRequest(data={})
    controller = PubsubController(
        resource_client,
        notion_service,
        orca_service,
        is_syncing_to_notion_enabled="true",
        firestore_service=firestore_service,
    )

    response = controller.fhir(request)

    assert response.status_code == 400


def test_fhir_when_no_message_in_envelope_then_return_400(
    resource_client, notion_service, orca_service, firestore_service
):
    request = FakeRequest(data={"invalid": "data"})
    controller = PubsubController(
        resource_client,
        notion_service,
        orca_service,
        is_syncing_to_notion_enabled="true",
        firestore_service=firestore_service,
    )

    response = controller.fhir(request)

    assert response.status_code == 400


def test_fhir_when_no_attributes_in_message_then_return_400(
    resource_client, notion_service, orca_service, firestore_service
):
    request = FakeRequest(data={"message": {"data": "data"}})
    controller = PubsubController(
        resource_client,
        notion_service,
        orca_service,
        is_syncing_to_notion_enabled="true",
        firestore_service=firestore_service,
    )

    response = controller.fhir(request)

    assert response.status_code == 400


def test_fhir_when_no_data_in_message_then_return_400(
    resource_client, notion_service, orca_service, firestore_service
):
    request = FakeRequest(data={"message": {"attributes": "attributes"}})
    controller = PubsubController(
        resource_client,
        notion_service,
        orca_service,
        is_syncing_to_notion_enabled="true",
        firestore_service=firestore_service,
    )

    response = controller.fhir(request)

    assert response.status_code == 400


@pytest.mark.parametrize(
    "resource", ["Appointment", "Patient", "Practitioner", "PractitionerRole"]
)
def test_fhir_when_no_operation_match_then_return_204(
    resource_client, notion_service, orca_service, firestore_service, resource
):
    request = FakeRequest(
        data=_generate_pubsub_message(
            action="CreateResource",
            payload_type="NameOnly",
            resource_type=resource,
            resource_id="test-resource-id",
        )
    )
    controller = PubsubController(
        resource_client,
        notion_service,
        orca_service,
        is_syncing_to_notion_enabled="true",
        firestore_service=firestore_service,
    )

    response = controller.fhir(request)

    assert response.status_code == 204


@pytest.mark.parametrize(
    "resource",
    ["Encounter", "MedicationRequest", "ServiceRequest", "DocumentReference"],
)
def test_post_encounter_when_no_existing_page_then_create_page_and_return_200(
    resource_client, notion_service, orca_service, firestore_service, resource
):
    notion_service.query_encounter_page.return_value = {"results": []}
    notion_service.create_encounter_page.return_value = {"id": TEST_ENCOUNTER_PAGE_ID}
    request = FakeRequest(
        data=_generate_pubsub_message(
            action="CreateResource",
            payload_type="NameOnly",
            resource_type=resource,
            resource_id=TEST_ENCOUNTER_ID,
        )
    )
    controller = PubsubController(
        resource_client,
        notion_service,
        orca_service,
        is_syncing_to_notion_enabled="true",
        firestore_service=firestore_service,
    )

    response = controller.fhir(request)

    assert response.status_code == 200
    assert response.data.decode("utf-8") == TEST_ENCOUNTER_PAGE_ID
    notion_service.query_encounter_page.assert_called_once_with(
        encounter_id=TEST_ENCOUNTER_ID
    )
    notion_service.create_encounter_page.assert_called_once_with(
        encounter_id=TEST_ENCOUNTER_ID
    )
    notion_service.sync_encounter_to_notion.assert_called_once_with(
        encounter_page_id=TEST_ENCOUNTER_PAGE_ID,
        account=mock.ANY,
        appointment=mock.ANY,
        patient=mock.ANY,
        practitioner_role=mock.ANY,
        clinical_note=mock.ANY,
        medication_request=mock.ANY,
        service_request=mock.ANY,
        insurance_card=mock.ANY,
    )

    firestore_service.sync_encounter_to_firestore.assert_called_once_with(
        appointment=mock.ANY,
        encounter=mock.ANY,
        patient=mock.ANY,
        medication_request=mock.ANY,
        service_request=mock.ANY,
    )


@pytest.mark.parametrize(
    "resource",
    ["Encounter", "MedicationRequest", "ServiceRequest", "DocumentReference"],
)
def test_post_encounter_when_page_exists_then_update_page_and_return_200(
    resource_client, notion_service, orca_service, firestore_service, resource
):
    notion_service.query_encounter_page.return_value = {
        "results": [{"id": TEST_ENCOUNTER_PAGE_ID}]
    }
    request = FakeRequest(
        data=_generate_pubsub_message(
            action="CreateResource",
            payload_type="NameOnly",
            resource_type=resource,
            resource_id=TEST_ENCOUNTER_ID,
        )
    )
    controller = PubsubController(
        resource_client,
        notion_service,
        orca_service,
        is_syncing_to_notion_enabled="true",
        firestore_service=firestore_service,
    )

    response = controller.fhir(request)

    assert response.status_code == 200
    assert response.data.decode("utf-8") == TEST_ENCOUNTER_PAGE_ID
    notion_service.query_encounter_page.assert_called_once_with(
        encounter_id=TEST_ENCOUNTER_ID
    )
    assert not notion_service.create_encounter_page.called
    notion_service.sync_encounter_to_notion.assert_called_once_with(
        encounter_page_id=TEST_ENCOUNTER_PAGE_ID,
        account=mock.ANY,
        appointment=mock.ANY,
        patient=mock.ANY,
        practitioner_role=mock.ANY,
        clinical_note=mock.ANY,
        medication_request=mock.ANY,
        service_request=mock.ANY,
        insurance_card=mock.ANY,
    )

    firestore_service.sync_encounter_to_firestore.assert_called_once_with(
        appointment=mock.ANY,
        encounter=mock.ANY,
        patient=mock.ANY,
        medication_request=mock.ANY,
        service_request=mock.ANY,
    )

    orca_service.sync_patient_to_orca.assert_called_once_with(
        patient=mock.ANY,
    )


def _generate_pubsub_message(
    action: str, payload_type: str, resource_type: str, resource_id: str
):
    data_str = f"projects/unit-test/locations/unit-test/datasets/unit-test/fhirStores/unit-test/fhir/{resource_type}/{resource_id}"
    data = base64.b64encode(bytes(data_str, "utf-8")).decode("utf-8")
    return {
        "ackId": "test-ack-id",
        "message": {
            "attributes": {
                "action": action,
                "payloadType": payload_type,
                "resourceType": resource_type,
            },
            "data": data,
            "messageId": "test-message-id",
            "publishTime": "2022-09-26T06:19:06.898Z",
        },
    }


@pytest.fixture
def resource_client(mocker):
    def mock_search(resource_type, search):
        if resource_type == "Encounter":
            assert search == [
                ("_id", TEST_ENCOUNTER_ID),
                ("_include", "Encounter:account"),
                ("_include", "Encounter:appointment"),
                ("_include", "Encounter:patient"),
                ("_include", "Encounter:practitioner"),
                ("_revinclude", "DocumentReference:encounter"),
                ("_revinclude", "MedicationRequest:encounter"),
                ("_revinclude", "ServiceRequest:encounter"),
            ]
            return Bundle(**ENCOUNTER_BUNDLE_DATA)
        if resource_type == "DocumentReference":
            assert search == [
                ("patient", TEST_PATIENT_ID),
                ("status", "current"),
                ("type", "64290-0"),
            ]
            return Bundle(**INSURANCE_CARD_BUNDLE_DATA)

    mock_resouce_client = MockResourceClient()
    mock_resouce_client.search = mock_search

    yield mock_resouce_client


@pytest.fixture
def notion_service(mocker):
    yield Mock()


@pytest.fixture
def firestore_service(mocker):
    yield Mock()


@pytest.fixture
def orca_service(mocker):
    yield Mock()
