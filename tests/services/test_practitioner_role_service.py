import pytest

from services.practitioner_service import Biography, HumanName


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
