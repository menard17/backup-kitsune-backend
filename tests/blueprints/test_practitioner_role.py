from helper import PRACTITIONER_ROLE_DATA, FakeRequest, MockResourceClient

from blueprints.practitioner_roles import (
    PractitionerRoleController,
    get_biographies_ext,
)


def test_update_practitioner_role_return_401_when_updating_others_practitioner_role():
    resource_client = MockResourceClient()
    controller = PractitionerRoleController(resource_client)

    role = PRACTITIONER_ROLE_DATA
    mismatch_id = "mismatch-id"
    request = FakeRequest(
        data=role,
        claims={
            "roles": {
                "Practitioner": {
                    "id": mismatch_id,
                },
            },
        },
    )
    resp = controller.update_practitioner_role(request, role["id"])
    assert resp.status_code == 401
    assert resp.data == b"practitioners can only update their themselves"


def test_bio_just_english_content():
    content = "biography contents"
    language_url = "http://hl7.org/fhir/StructureDefinition/translation"
    request_body = {
        "bio_en": content,
    }
    biography = get_biographies_ext(request_body, ["en"])
    expected = {
        "url": "bio",
        "valueString": content,
        "extension": [{"url": language_url, "valueString": "en"}],
    }
    assert biography[0].get_bio_with_lang() == expected


def test_bio_just_english_and_japanese_content():
    content = "biography contents"
    language_url = "http://hl7.org/fhir/StructureDefinition/translation"
    request_body = {"bio_en": content, "bio_ja": content}
    biography = get_biographies_ext(request_body, ["en", "ja"])
    actual_en_bio, actual_ja_bio = biography
    expected_en = {
        "url": "bio",
        "valueString": content,
        "extension": [{"url": language_url, "valueString": "en"}],
    }
    expected_ja = {
        "url": "bio",
        "valueString": content,
        "extension": [{"url": language_url, "valueString": "ja"}],
    }
    assert [actual_en_bio.get_bio_with_lang(), actual_ja_bio.get_bio_with_lang()] == [
        expected_en,
        expected_ja,
    ]
