import json

import pytest
from fhir.resources import construct_fhir_element
from fhir.resources.domainresource import DomainResource

from services.practitioner_role_service import PractitionerRoleService
from services.practitioner_service import Biography, HumanName

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
