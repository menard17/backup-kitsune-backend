import copy
import json
from datetime import datetime

import pytest
from fhir.resources import construct_fhir_element
from fhir.resources.domainresource import DomainResource

from adapters.fhir_store import ResourceClient
from services.practitioner_role_service import PractitionerRoleService
from services.practitioner_service import Biography, HumanName
from utils.system_code import ServiceURL

practitioner = {
    "active": True,
    "id": "1",
    "name": [
        {
            "extension": [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/iso21090-EN-representation",
                    "valueString": "IDE",
                }
            ],
            "family": "Family",
            "given": ["Given"],
            "text": "Family Given",
        },
        {
            "extension": [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/iso21090-EN-representation",
                    "valueString": "ABC",
                }
            ],
            "family": "Family_EN",
            "given": ["Given_EN"],
            "text": "Family Given",
        },
    ],
    "resourceType": "Practitioner",
}

practitioner_role = {
    "active": True,
    "availableTime": [
        {
            "availableEndTime": "20:00:00",
            "availableStartTime": "09:00:00",
            "daysOfWeek": ["mon"],
        },
    ],
    "id": "1",
    "period": {"end": "2099-03-31", "start": "2021-01-01"},
    "practitioner": {"reference": "Practitioner/1"},
    "code": [
        {
            "coding": [
                {
                    "system": ServiceURL.practitioner_type,
                    "code": "doctor",
                }
            ],
        }
    ],
    "resourceType": "PractitionerRole",
}


class MockClient:
    def __init__(self, mocker=None):
        self.mocker = mocker
        self.resource = {
            "Practitioner": construct_fhir_element(
                "Practitioner", json.dumps(practitioner)
            ),
            "PractitionerRole": construct_fhir_element(
                "PractitionerRole", json.dumps(practitioner_role)
            ),
        }

    def get_resource(self, id: str, resource_type: str) -> DomainResource:
        return self.resource.get(resource_type)

    def search(self, resource_type: str, search: list) -> DomainResource:
        self.mocker.entry = [self.practitioner, self.practitioner_role]
        self.mocker.total = 2
        return self.mocker


def test_human_name_english():
    # Given
    given_name = "Test given"
    family_name = "Test family"
    language = "en"
    expected = {
        "family": family_name,
        "given": [given_name],
        "text": f"{given_name} {family_name}",
        "extension": [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/iso21090-EN-representation",
                "valueString": "ABC",
            },
        ],
        "prefix": ["MD"],
    }

    # When
    actual = HumanName(given_name, family_name, language).get_name_with_lang()

    # Then
    assert expected == actual


def test_human_name_japanese():
    # Given
    given_name = "テスト"
    family_name = "苗字"
    language = "ja"
    expected = {
        "family": family_name,
        "given": [given_name],
        "text": f"{given_name} {family_name}",
        "extension": [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/iso21090-EN-representation",
                "valueString": "IDE",
            },
        ],
        "prefix": ["医師"],
    }

    # When
    actual = HumanName(given_name, family_name, language).get_name_with_lang()

    # Then
    assert expected == actual


def test_human_name_not_implemented():
    # Given
    given_name = "essai"
    family_name = "nom"
    language = "fr"

    # When and Then
    with pytest.raises(NotImplementedError):
        HumanName(given_name, family_name, language).get_name_with_lang()


def test_bio_english():
    # Given
    content = "bio"
    language = "en"
    expected = {
        "url": "bio",
        "valueString": content,
        "extension": [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/translation",
                "valueString": language,
            }
        ],
    }

    # When
    actual = Biography(content, language).get_bio_with_lang()

    # Then
    assert expected == actual


def test_bio_japanese():
    # Given
    content = "私は、"
    language = "ja"
    expected = {
        "url": "bio",
        "valueString": content,
        "extension": [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/translation",
                "valueString": language,
            }
        ],
    }

    # When
    actual = Biography(content, language).get_bio_with_lang()

    # Then
    assert expected == actual


def test_bio_not_implemented():
    # Given
    content = "Je suis"
    language = "fr"

    # When and Then
    with pytest.raises(NotImplementedError):
        Biography(content, language).get_bio_with_lang()


def test_get_en_practitioner_name(mocker):
    # Given
    language = "ABC"
    expected_family = "Family_EN"
    expected_given = "Given_EN"
    mock_resource_client = MockClient(mocker)
    role_service = PractitionerRoleService(mock_resource_client)

    # When
    _, actual_name = role_service.get_practitioner_name(language, "1")

    # Then
    assert expected_family == actual_name["family"]
    assert expected_given == actual_name["given"][0]


def test_get_ja_practitioner_name(mocker):
    # Given
    language = "IDE"
    expected_family = "Family"
    expected_given = "Given"
    mock_resource_client = MockClient(mocker)
    role_service = PractitionerRoleService(mock_resource_client)

    # When
    _, actual_name = role_service.get_practitioner_name(language, "1")

    # Then
    assert expected_family == actual_name["family"]
    assert expected_given == actual_name["given"][0]


def test_get_radnom_loc_practitioner_name(mocker):
    # Given
    language = "AAA"
    expected_family = "Family_EN"
    expected_given = "Given_EN"
    mock_resource_client = MockClient(mocker)
    role_service = PractitionerRoleService(mock_resource_client)

    # When
    _, actual_name = role_service.get_practitioner_name(language, "1")

    # Then
    assert expected_family == actual_name["family"]
    assert expected_given == actual_name["given"][0]


def test_create_practitioner_role():
    service = PractitionerRoleService(ResourceClient())
    err, bundle = service.create_practitioner_role(
        identity="test-id",
        role_type="doctor",
        start="2021-01-01",
        end="2022-01-01",
        practitioner_id="test-practitioner-id",
        practitioner_name="Dr. Test",
        available_time=[
            {
                "daysOfWeek": ["mon", "fri"],
                "availableStartTime": "00:00:00",
                "availableEndTime": "16:59:59",
            },
        ],
    )

    assert err is None
    assert bundle["request"]["method"] == "POST"

    role = bundle["resource"]
    assert role.resource_type == "PractitionerRole"
    assert any([c.coding[0].code == "doctor" for c in role.code])
    assert role.practitioner.reference == "test-practitioner-id"
    assert role.period.start == datetime.strptime("2021-01-01", "%Y-%m-%d").date()
    assert role.period.end == datetime.strptime("2022-01-01", "%Y-%m-%d").date()


def test_create_practitioner_role_with_visit_type():
    service = PractitionerRoleService(ResourceClient())
    err, bundle = service.create_practitioner_role(
        identity="test-id",
        role_type="doctor",
        start="2021-01-01",
        end="2022-01-01",
        practitioner_id="test-practitioner-id",
        practitioner_name="Dr. Test",
        visit_type="walk-in",
        available_time=[
            {
                "daysOfWeek": ["mon", "fri"],
                "availableStartTime": "00:00:00",
                "availableEndTime": "16:59:59",
            },
        ],
    )

    assert err is None

    role = bundle["resource"]
    assert role.resource_type == "PractitionerRole"
    assert any([c.coding[0].code == "walk-in" for c in role.code])


def test_update_visit_type_of_practitioner_role_from_none():
    service = PractitionerRoleService(ResourceClient())

    role = construct_fhir_element("PractitionerRole", json.dumps(practitioner_role))
    assert not any([c.coding[0].code == "walk-in" for c in role.code])

    err, bundle = service.update_practitioner_role(role, visit_type="walk-in")

    assert err is None
    assert bundle["request"]["method"] == "PUT"

    role = bundle["resource"]
    assert role.resource_type == "PractitionerRole"
    assert any([c.coding[0].code == "walk-in" for c in role.code])


def test_update_visit_type_of_practitioner_role_from_another_type():
    service = PractitionerRoleService(ResourceClient())

    # given a practitioner role with the appointment visit type
    role_data = copy.deepcopy(practitioner_role)
    role_data["code"].append(
        {
            "coding": [
                {
                    "system": ServiceURL.practitioner_visit_type,
                    "code": "appointment",
                }
            ],
        }
    )
    role = construct_fhir_element("PractitionerRole", json.dumps(role_data))
    assert any([c.coding[0].code == "appointment" for c in role.code])

    err, bundle = service.update_practitioner_role(role, visit_type="walk-in")

    assert err is None
    assert bundle["request"]["method"] == "PUT"

    role = bundle["resource"]
    assert role.resource_type == "PractitionerRole"
    assert any([c.coding[0].code == "walk-in" for c in role.code])
    assert not any([c.coding[0].code == "appointment" for c in role.code])


def test_update_visit_type_of_practitioner_role_returns_error_when_not_doctor():
    service = PractitionerRoleService(ResourceClient())

    # given a nurse
    role_data = copy.deepcopy(practitioner_role)
    role_data["code"][0]["coding"][0]["code"] = "nurse"

    role = construct_fhir_element("PractitionerRole", json.dumps(role_data))

    err, _ = service.update_practitioner_role(role, visit_type="walk-in")
    assert err.args[0] == "Can only update visit type for doctor"
