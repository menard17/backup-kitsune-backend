from unittest.mock import patch
from utils import role_auth


def test_grant_role_without_existing_role():
    request_claims = {"uid": "test-uid"}

    with patch("utils.role_auth.auth") as mock_auth:
        role_auth.grant_role(request_claims, "Patient", "patient-id")

        mock_auth.set_custom_user_claims.assert_called_once_with(
            "test-uid", {"roles": {"Patient": {"id": "patient-id"}}}
        )


def test_grant_role_with_existing_same_role():
    request_claims = {"uid": "test-uid", "roles": {"Patient": {"id": "patient-id"}}}

    with patch("utils.role_auth.auth") as mock_auth:
        role_auth.grant_role(request_claims, "Patient", "other-patient-id")

        mock_auth.set_custom_user_claims.assert_called_once_with(
            "test-uid", {"roles": {"Patient": {"id": "other-patient-id"}}}
        )


def test_grant_role_with_existing_different_role():
    current_claims = {"uid": "test-uid", "roles": {"Patient": {"id": "patient-id"}}}

    with patch("utils.role_auth.auth") as mock_auth:
        role_auth.grant_role(current_claims, "Practitioner", "practitioner-id")

        mock_auth.set_custom_user_claims.assert_called_once_with(
            "test-uid",
            {
                "roles": {
                    "Patient": {"id": "patient-id"},
                    "Practitioner": {"id": "practitioner-id"},
                }
            },
        )


def test_grant_role_without_role_id():
    current_claims = {
        "uid": "test-uid",
    }

    with patch("utils.role_auth.auth") as mock_auth:
        role_auth.grant_role(current_claims, "Admin")

        mock_auth.set_custom_user_claims.assert_called_once_with(
            "test-uid", {"roles": {"Admin": {}}}
        )


def test_extract_roles():
    expected_roles = {"Patient": {"id": "patient-id"}}
    custom_claims = {"roles": expected_roles}

    roles = role_auth.extract_roles(custom_claims)

    assert roles == expected_roles


def test_is_authorized_unauthorized_for_user_without_claims_roles():
    claims_roles = None

    assert role_auth.is_authorized(claims_roles, "Patient", "patient-id") is False
    assert role_auth.is_authorized(claims_roles, "Patient", "*") is False
    assert (
        role_auth.is_authorized(claims_roles, "Practitioner", "practitioner-id")
        is False
    )
    assert role_auth.is_authorized(claims_roles, "Practitioner", "*") is False
    assert role_auth.is_authorized(claims_roles, "Admin", None) is False


def test_is_authorized_admin_should_have_full_access():
    claims_roles = {"Admin": {}}

    assert role_auth.is_authorized(claims_roles, "Patient", "patient-id") is True
    assert role_auth.is_authorized(claims_roles, "Patient", "*") is True
    assert (
        role_auth.is_authorized(claims_roles, "Practitioner", "practitioner-id") is True
    )
    assert role_auth.is_authorized(claims_roles, "Practitioner", "*") is True
    assert role_auth.is_authorized(claims_roles, "Admin", None) is True


def test_is_authorized_patient_should_only_have_access_to_their_resources():
    claims_roles = {"Patient": {"id": "patient-id"}}

    assert role_auth.is_authorized(claims_roles, "Patient", "patient-id") is True
    assert role_auth.is_authorized(claims_roles, "Patient", "other_patient-id") is False
    assert role_auth.is_authorized(claims_roles, "Patient", "*") is False
    assert (
        role_auth.is_authorized(claims_roles, "Practitioner", "practitioner-id")
        is False
    )
    assert role_auth.is_authorized(claims_roles, "Practitioner", "*") is False
    assert role_auth.is_authorized(claims_roles, "Admin", None) is False


def test_is_authorized_practitioner_should_have_access_to_patients_and_themselves():
    claims_roles = {"Practitioner": {"id": "practitioner-id"}}

    assert role_auth.is_authorized(claims_roles, "Patient", "patient-id") is True
    assert role_auth.is_authorized(claims_roles, "Patient", "*") is True
    assert (
        role_auth.is_authorized(claims_roles, "Practitioner", "practitioner-id") is True
    )
    assert (
        role_auth.is_authorized(claims_roles, "Practitioner", "other_practitioner-id")
        is False
    )
    assert role_auth.is_authorized(claims_roles, "Practitioner", "*") is False
    assert role_auth.is_authorized(claims_roles, "Admin", None) is False


def test_is_authorized_multiple_roles():
    claims_roles = {
        "Patient": {"id": "patient-id"},
        "Practitioner": {"id": "practitioner-id"},
    }

    assert role_auth.is_authorized(claims_roles, "Patient", "patient-id") is True
    assert role_auth.is_authorized(claims_roles, "Patient", "other_patient-id") is True
    assert role_auth.is_authorized(claims_roles, "Patient", "*") is True
    assert (
        role_auth.is_authorized(claims_roles, "Practitioner", "practitioner-id") is True
    )
    assert (
        role_auth.is_authorized(claims_roles, "Practitioner", "other_practitioner-id")
        is False
    )
    assert role_auth.is_authorized(claims_roles, "Practitioner", "*") is False
    assert role_auth.is_authorized(claims_roles, "Admin", None) is False
