from unittest.mock import Mock

import pytest
from fhir.resources.account import Account
from fhir.resources.appointment import Appointment
from fhir.resources.documentreference import DocumentReference
from fhir.resources.medicationrequest import MedicationRequest
from fhir.resources.patient import Patient
from fhir.resources.practitionerrole import PractitionerRole
from fhir.resources.servicerequest import ServiceRequest
from pydantic import AnyUrl

from services.notion_service import NotionService

ACCOUNT_DATA = {
    "guarantor": [
        {
            "onHold": False,
            "party": {"reference": "Patient/02989bec-b084-47d9-99fd-259ac6f3360c"},
        }
    ],
    "id": "393631e9-7a1d-48ac-a733-0bd649ca3d68",
    "meta": {
        "lastUpdated": "2022-09-05T13:15:57.277240+00:00",
        "versionId": "MTY2MjM4Mzc1NzI3NzI0MDAwMA",
    },
    "resourceType": "Account",
    "status": "active",
    "subject": [{"reference": "Patient/02989bec-b084-47d9-99fd-259ac6f3360c"}],
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
}

APPOINTMENT_DATA = {
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
    "end": "2022-09-05T10:40:00+09:00",
    "id": "8ed8a19a-e04e-43f2-8da1-beaae3dd4d97",
    "meta": {
        "lastUpdated": "2022-09-05T13:15:57.719856+00:00",
        "versionId": "MTY2MjM4Mzc1NzcxOTg1NjAwMA",
    },
    "participant": [
        {
            "actor": {"reference": "Patient/02989bec-b084-47d9-99fd-259ac6f3360c"},
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
    "resourceType": "Appointment",
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
    "start": "2022-09-05T10:28:00+09:00",
    "status": "fulfilled",
}

PATIENT_DATA = {
    "address": [
        {
            "city": "港区",
            "country": "JP",
            "line": ["1-1-1"],
            "postalCode": "111-1111",
            "state": "東京都",
            "type": "both",
            "use": "home",
        },
        {
            "city": "港区",
            "country": "JP",
            "line": ["2-2-2"],
            "postalCode": "222-2222",
            "state": "東京都",
            "type": "both",
            "use": "work",
        },
    ],
    "birthDate": "2020-08-20",
    "extension": [
        {"url": "stripe-customer-id", "valueString": "test-customer-id"},
        {
            "url": "stripe-payment-method-id",
            "valueString": "test-payment-method-id",
        },
        {
            "url": "fcm-token",
            "valueString": "test-fcm-token",
        },
    ],
    "gender": "female",
    "id": "02989bec-b084-47d9-99fd-259ac6f3360c",
    "meta": {
        "lastUpdated": "2022-09-15T14:04:19.651495+00:00",
        "versionId": "MTY2MzI1MDY1OTY1MTQ5NTAwMA",
    },
    "name": [
        {
            "family": "Official",
            "given": ["Name"],
            "use": "official",
            "extension": [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/iso21090-EN-representation",
                    "valueString": "IDE",
                },
            ],
        },
        {
            "family": "Unofficial",
            "given": ["Name"],
            "use": "temp",
            "extension": [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/iso21090-EN-representation",
                    "valueString": "ABC",
                },
            ],
        },
        {
            "family": "kanaFamilyName",
            "given": ["kanaGivenName"],
            "extension": [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/iso21090-EN-representation",
                    "valueString": "SYL",
                },
            ],
        },
    ],
    "resourceType": "Patient",
    "telecom": [
        {
            "extension": [{"url": "verified", "valueString": "true"}],
            "system": "email",
            "use": "home",
            "value": "home-email@gmail.com",
        },
        {
            "extension": [{"url": "verified", "valueString": "true"}],
            "system": "email",
            "use": "work",
            "value": "work-email@gmail.com",
        },
        {"system": "phone", "use": "mobile", "value": "08011111111"},
    ],
}

PATIENT_DATA_WITHOUT_DOB_AND_GENDER = {
    "address": [
        {
            "city": "港区",
            "country": "JP",
            "line": ["1-1-1"],
            "postalCode": "111-1111",
            "state": "東京都",
            "type": "both",
            "use": "home",
        },
        {
            "city": "港区",
            "country": "JP",
            "line": ["2-2-2"],
            "postalCode": "222-2222",
            "state": "東京都",
            "type": "both",
            "use": "work",
        },
    ],
    "extension": [
        {"url": "stripe-customer-id", "valueString": "test-customer-id"},
        {
            "url": "stripe-payment-method-id",
            "valueString": "test-payment-method-id",
        },
        {
            "url": "fcm-token",
            "valueString": "test-fcm-token",
        },
    ],
    "id": "02989bec-b084-47d9-99fd-259ac6f3360c",
    "meta": {
        "lastUpdated": "2022-09-15T14:04:19.651495+00:00",
        "versionId": "MTY2MzI1MDY1OTY1MTQ5NTAwMA",
    },
    "name": [
        {"family": "Official", "given": ["Name"], "use": "official"},
        {"family": "Unofficial", "given": ["Name"], "use": "temp"},
    ],
    "resourceType": "Patient",
    "telecom": [
        {
            "extension": [{"url": "verified", "valueString": "true"}],
            "system": "email",
            "use": "home",
            "value": "home-email@gmail.com",
        },
        {
            "extension": [{"url": "verified", "valueString": "true"}],
            "system": "email",
            "use": "work",
            "value": "work-email@gmail.com",
        },
        {"system": "phone", "use": "mobile", "value": "08011111111"},
    ],
}

PRACTITIONER_ROLE_DATA = {
    "active": False,
    "availableTime": [
        {
            "availableEndTime": "17:00:00",
            "availableStartTime": "00:00:00",
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
    "id": "9de70669-1d0d-4d54-a241-3cb4047631e0",
    "meta": {
        "lastUpdated": "2022-09-08T01:14:54.547531+00:00",
        "versionId": "MTY2MjU5OTY5NDU0NzUzMTAwMA",
    },
    "period": {"end": "2022-08-27", "start": "2022-08-24"},
    "practitioner": {
        "display": "Taro Yamada",
        "reference": "Practitioner/8e4c7788-a439-42f7-a7fb-bf88a70ddc18",
    },
    "resourceType": "PractitionerRole",
}

CLINICAL_NOTE_DATA = {
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
                "creation": "2022-09-05T13:16:12.281864+00:00",
                "data": "VEVTVF9DTElOSUNBTF9OT1RFCg==",
                "title": "page1",
            }
        }
    ],
    "context": {
        "encounter": [{"reference": "Encounter/579fa116-251d-4a9b-9a69-3ab03b573452"}]
    },
    "date": "2022-09-05T13:16:12.281870+00:00",
    "id": "db6a5d6b-ec83-470b-b780-90d2eea2c73f",
    "meta": {
        "lastUpdated": "2022-09-05T13:16:12.583785+00:00",
        "versionId": "MTY2MjM4Mzc3MjU4Mzc4NTAwMA",
    },
    "resourceType": "DocumentReference",
    "status": "current",
    "subject": {"reference": "Patient/02989bec-b084-47d9-99fd-259ac6f3360c"},
    "type": {
        "coding": [
            {
                "code": "55110-1",
                "display": "Conclusions Document",
                "system": "http://loinc.org",
            }
        ]
    },
}

MEDICATION_REQUEST_DATA = {
    "encounter": {"reference": "Encounter/579fa116-251d-4a9b-9a69-3ab03b573452"},
    "id": "251149b1-ba7f-4305-a784-dc5154ccacda",
    "intent": "order",
    "medicationCodeableConcept": {
        "coding": [
            {"code": "Loxonin", "display": "ロキソニン&セルベックス"},
            {"code": "Transamin", "display": "トランサミン"},
        ]
    },
    "meta": {
        "lastUpdated": "2022-09-05T13:16:12.602208+00:00",
        "versionId": "MTY2MjM4Mzc3MjYwMjIwODAwMA",
    },
    "priority": "urgent",
    "requester": {"reference": "PractitionerRole/9de70669-1d0d-4d54-a241-3cb4047631e0"},
    "resourceType": "MedicationRequest",
    "status": "completed",
    "subject": {"reference": "Patient/02989bec-b084-47d9-99fd-259ac6f3360c"},
}

SERVICE_REQUEST_DATA = {
    "code": {
        "coding": [
            {
                "code": "Allplex SARS-CoV-2 Assay",
                "display": "PCR検査施行",
                "system": "ServiceRequest",
            }
        ]
    },
    "encounter": {"reference": "Encounter/579fa116-251d-4a9b-9a69-3ab03b573452"},
    "id": "8c08b7ef-4b24-43c5-a65d-321350d22f14",
    "intent": "order",
    "meta": {
        "lastUpdated": "2022-09-05T13:16:12.553194+00:00",
        "versionId": "MTY2MjM4Mzc3MjU1MzE5NDAwMA",
    },
    "priority": "urgent",
    "requester": {"reference": "PractitionerRole/9de70669-1d0d-4d54-a241-3cb4047631e0"},
    "resourceType": "ServiceRequest",
    "status": "completed",
    "subject": {"reference": "Patient/02989bec-b084-47d9-99fd-259ac6f3360c"},
}

INSURANCE_CARD_DATA = {
    "content": [
        {
            "attachment": {
                "creation": "2022-08-24T11:43:59.724241+00:00",
                "title": "front",
                "url": "https://test-front-url",
            }
        },
    ],
    "date": "2022-08-24T11:43:59.724248+00:00",
    "id": "cebbdc53-9e44-4947-b45a-359dab89e8ea",
    "meta": {
        "lastUpdated": "2022-08-24T11:44:00.075720+00:00",
        "versionId": "MTY2MTM0MTQ0MDA3NTcyMDAwMA",
    },
    "resourceType": "DocumentReference",
    "status": "current",
    "subject": {"reference": "Patient/02989bec-b084-47d9-99fd-259ac6f3360c"},
    "type": {
        "coding": [
            {
                "code": "64290-0",
                "display": "Insurance Card",
                "system": "http://loinc.org",
            }
        ]
    },
}

MEDICAL_CARD_DATA = {
    "content": [
        {
            "attachment": {
                "creation": "2023-01-30T07:49:13.315173+00:00",
                "title": "Page 0",
                "url": "https://test-medical-card-url",
            },
        },
    ],
    "date": "2023-01-30T07:49:13.315208+00:00",
    "id": "66ee2c78-7878-4823-9da2-4cfb5321ff54",
    "meta": {
        "lastUpdated": "2023-01-30T07:49:14.368052+00:00",
        "versionId": "MTY3NTA2NDk1NDM2ODA1MjAwMA",
    },
    "resourceType": "DocumentReference",
    "status": "current",
    "subject": {
        "reference": "Patient/02989bec-b084-47d9-99fd-259ac6f3360c",
    },
    "type": {
        "coding": [
            {
                "code": "00001-1",
                "display": "Medical Card",
                "system": "http://loinc.org",
            },
        ],
    },
}

TEST_ACCOUNT = Account(**ACCOUNT_DATA)
TEST_APPOINTMENT = Appointment(**APPOINTMENT_DATA)
TEST_PATIENT = Patient(**PATIENT_DATA)
TEST_PRACTITIONER_ROLE = PractitionerRole(**PRACTITIONER_ROLE_DATA)
TEST_CLINICAL_NOTE = DocumentReference(**CLINICAL_NOTE_DATA)
TEST_MEDICATION_REQUEST = MedicationRequest(**MEDICATION_REQUEST_DATA)
TEST_SERIVCE_REQUEST = ServiceRequest(**SERVICE_REQUEST_DATA)
TEST_INSURANCE_CARD = DocumentReference(**INSURANCE_CARD_DATA)
TEST_MEDICAL_CARD = DocumentReference(**MEDICAL_CARD_DATA)

TEST_ENCOUNTER_DATABASE_ID = "test-encounter-database-id"
TEST_ENCOUNTER_PAGE_ID = "test-encounter-page-id"
# Use a correct ID to match with the test data retrieved from Kitsune Dev
TEST_ENCOUNTER_ID = "579fa116-251d-4a9b-9a69-3ab03b573452"


def test_query_encounter_page_happy_path(notion_client):
    notion_service = NotionService(notion_client, TEST_ENCOUNTER_DATABASE_ID)

    notion_service.query_encounter_page(TEST_ENCOUNTER_ID)

    notion_client.databases.query.assert_called_once_with(
        database_id=TEST_ENCOUNTER_DATABASE_ID,
        filter={"property": "encounter_id", "rich_text": {"equals": TEST_ENCOUNTER_ID}},
    )


def test_create_encounter_page_happy_path(notion_client):
    notion_service = NotionService(notion_client, TEST_ENCOUNTER_DATABASE_ID)

    notion_service.create_encounter_page(TEST_ENCOUNTER_ID)

    notion_client.pages.create.assert_called_once_with(
        parent={"database_id": TEST_ENCOUNTER_DATABASE_ID},
        properties={
            "encounter_id": {
                "title": [{"type": "text", "text": {"content": TEST_ENCOUNTER_ID}}]
            }
        },
    )


def test_sync_encounter_to_notion_when_gender_and_dob_is_missing(notion_client):
    notion_service = NotionService(notion_client, TEST_ENCOUNTER_DATABASE_ID)
    TEST_PATIENT_WITHOUT_DOB_AND_GENDER = Patient(**PATIENT_DATA_WITHOUT_DOB_AND_GENDER)
    notion_service.sync_encounter_to_notion(
        encounter_page_id=TEST_ENCOUNTER_PAGE_ID,
        account=TEST_ACCOUNT,
        appointment=TEST_APPOINTMENT,
        patient=TEST_PATIENT_WITHOUT_DOB_AND_GENDER,
        practitioner_role=TEST_PRACTITIONER_ROLE,
        clinical_note=TEST_CLINICAL_NOTE,
        medication_request=TEST_MEDICATION_REQUEST,
        service_request=TEST_SERIVCE_REQUEST,
        insurance_card=TEST_INSURANCE_CARD,
        medical_card=TEST_MEDICAL_CARD,
    )

    notion_client.pages.update.assert_called_once_with(
        page_id="test-encounter-page-id",
        properties={
            "delivery_date": {"date": {"start": "2022-09-05T10:28:00+09:00"}},
            "email": {"rich_text": [{"text": {"content": "home-email@gmail.com"}}]},
            "user_name": {"rich_text": [{"text": {"content": "Official Name"}}]},
            "user_name_kana": {"rich_text": [{"text": {"content": ""}}]},
            "dob": {"rich_text": [{"text": {"content": ""}}]},
            "phone_number": {"rich_text": [{"text": {"content": "08011111111"}}]},
            "address": {"rich_text": [{"text": {"content": "111-1111 東京都 港区 1-1-1"}}]},
            "emr": {"rich_text": [{"text": {"content": "TEST_CLINICAL_NOTE\n"}}]},
            "prescription": {
                "rich_text": [{"text": {"content": "ロキソニン&セルベックス\nトランサミン"}}]
            },
            "tests": {"rich_text": [{"text": {"content": "PCR検査施行"}}]},
            "doctor": {"rich_text": [{"text": {"content": "Taro Yamada"}}]},
            "insurance_card_front": {
                "rich_text": [
                    {
                        "text": {
                            "content": AnyUrl(
                                "https://test-front-url",
                                scheme="https",
                                host="test-front-url",
                                host_type="int_domain",
                            )
                        }
                    }
                ]
            },
            "medical_card": {
                "rich_text": [
                    {
                        "text": {
                            "content": "https://test-medical-card-url\n",
                        }
                    }
                ]
            },
            "gender": {"rich_text": [{"text": {"content": ""}}]},
            "account_id": {
                "rich_text": [
                    {"text": {"content": "393631e9-7a1d-48ac-a733-0bd649ca3d68"}}
                ]
            },
        },
    )


def test_sync_encounter_to_notion_address_without_use_as_home(notion_client):
    """
    Sometimes the patient data do not have the address with a specific "use" type.
    It is likely older version of the app do not have it automatically set.
    """
    notion_service = NotionService(notion_client, TEST_ENCOUNTER_DATABASE_ID)

    patient_data = PATIENT_DATA
    patient_data["address"] = [
        {
            "city": "港区",
            "line": ["1-1-1"],
            "postalCode": "111-1111",
            "state": "東京都",
        }
    ]
    test_patient = Patient(**patient_data)

    notion_service.sync_encounter_to_notion(
        encounter_page_id=TEST_ENCOUNTER_PAGE_ID,
        account=TEST_ACCOUNT,
        appointment=TEST_APPOINTMENT,
        patient=test_patient,
        practitioner_role=TEST_PRACTITIONER_ROLE,
        clinical_note=TEST_CLINICAL_NOTE,
        medication_request=TEST_MEDICATION_REQUEST,
        service_request=TEST_SERIVCE_REQUEST,
        insurance_card=TEST_INSURANCE_CARD,
        medical_card=TEST_MEDICAL_CARD,
    )

    notion_client.pages.update.assert_called_once_with(
        page_id="test-encounter-page-id",
        properties={
            "delivery_date": {"date": {"start": "2022-09-05T10:28:00+09:00"}},
            "email": {"rich_text": [{"text": {"content": "home-email@gmail.com"}}]},
            "user_name": {"rich_text": [{"text": {"content": "Official Name"}}]},
            "user_name_kana": {
                "rich_text": [{"text": {"content": "kanaFamilyName kanaGivenName"}}]
            },
            "dob": {"rich_text": [{"text": {"content": "2020-08-20"}}]},
            "phone_number": {"rich_text": [{"text": {"content": "08011111111"}}]},
            "address": {"rich_text": [{"text": {"content": "111-1111 東京都 港区 1-1-1"}}]},
            "emr": {"rich_text": [{"text": {"content": "TEST_CLINICAL_NOTE\n"}}]},
            "prescription": {
                "rich_text": [{"text": {"content": "ロキソニン&セルベックス\nトランサミン"}}]
            },
            "tests": {"rich_text": [{"text": {"content": "PCR検査施行"}}]},
            "doctor": {"rich_text": [{"text": {"content": "Taro Yamada"}}]},
            "insurance_card_front": {
                "rich_text": [{"text": {"content": "https://test-front-url"}}]
            },
            "medical_card": {
                "rich_text": [{"text": {"content": "https://test-medical-card-url\n"}}]
            },
            "gender": {"rich_text": [{"text": {"content": "female"}}]},
            "account_id": {
                "rich_text": [
                    {"text": {"content": "393631e9-7a1d-48ac-a733-0bd649ca3d68"}}
                ]
            },
        },
    )


def test_sync_encounter_to_notion_happy_path(notion_client):
    notion_service = NotionService(notion_client, TEST_ENCOUNTER_DATABASE_ID)

    notion_service.sync_encounter_to_notion(
        encounter_page_id=TEST_ENCOUNTER_PAGE_ID,
        account=TEST_ACCOUNT,
        appointment=TEST_APPOINTMENT,
        patient=TEST_PATIENT,
        practitioner_role=TEST_PRACTITIONER_ROLE,
        clinical_note=TEST_CLINICAL_NOTE,
        medication_request=TEST_MEDICATION_REQUEST,
        service_request=TEST_SERIVCE_REQUEST,
        insurance_card=TEST_INSURANCE_CARD,
        medical_card=TEST_MEDICAL_CARD,
    )

    notion_client.pages.update.assert_called_once_with(
        page_id="test-encounter-page-id",
        properties={
            "delivery_date": {"date": {"start": "2022-09-05T10:28:00+09:00"}},
            "email": {"rich_text": [{"text": {"content": "home-email@gmail.com"}}]},
            "user_name": {"rich_text": [{"text": {"content": "Official Name"}}]},
            "user_name_kana": {
                "rich_text": [{"text": {"content": "kanaFamilyName kanaGivenName"}}]
            },
            "dob": {"rich_text": [{"text": {"content": "2020-08-20"}}]},
            "phone_number": {"rich_text": [{"text": {"content": "08011111111"}}]},
            "address": {"rich_text": [{"text": {"content": "111-1111 東京都 港区 1-1-1"}}]},
            "emr": {"rich_text": [{"text": {"content": "TEST_CLINICAL_NOTE\n"}}]},
            "prescription": {
                "rich_text": [{"text": {"content": "ロキソニン&セルベックス\nトランサミン"}}]
            },
            "tests": {"rich_text": [{"text": {"content": "PCR検査施行"}}]},
            "doctor": {"rich_text": [{"text": {"content": "Taro Yamada"}}]},
            "insurance_card_front": {
                "rich_text": [{"text": {"content": "https://test-front-url"}}]
            },
            "medical_card": {
                "rich_text": [{"text": {"content": "https://test-medical-card-url\n"}}]
            },
            "gender": {"rich_text": [{"text": {"content": "female"}}]},
            "account_id": {
                "rich_text": [
                    {"text": {"content": "393631e9-7a1d-48ac-a733-0bd649ca3d68"}}
                ]
            },
        },
    )


@pytest.fixture
def notion_client(mocker):
    mocker.databases = Mock()
    mocker.pages = Mock()
    yield mocker
