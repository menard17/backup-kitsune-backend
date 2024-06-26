from unittest.mock import patch

import pytest

from utils import role_auth


class UserObject:
    custom_claims = {}


def test_grant_role_without_existing_role():
    request_claims = {"uid": "test-uid"}

    with patch("utils.role_auth.auth") as mock_auth:
        with patch("utils.role_auth.auth.get_user", return_value=UserObject):
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
        with patch("utils.role_auth.auth.get_user", return_value=UserObject):
            role_auth.grant_role(current_claims, "Admin")

            mock_auth.set_custom_user_claims.assert_called_once_with(
                "test-uid", {"roles": {"Admin": {}}}
            )


def test_delegate_role():
    main_role_id = "primary-patient-id"
    delegate_role_id = "secondary-patient-id"
    current_claims = {
        "uid": "test-uid",
        "roles": {
            "Patient": {
                "id": main_role_id,
            },
        },
    }
    expected_updated_roles = current_claims["roles"].copy()
    expected_updated_roles["Patient"]["delegates"] = [delegate_role_id]

    with patch("utils.role_auth.auth") as mock_auth:
        with patch("utils.role_auth.auth.get_user", return_value=UserObject):
            role_auth.delegate_role(
                current_claims, "Patient", main_role_id, delegate_role_id
            )

            mock_auth.set_custom_user_claims.assert_called_once_with(
                "test-uid", {"roles": expected_updated_roles}
            )


def test_delegate_role_fail_when_role_not_existing():
    main_role_id = "primary-patient-id"
    delegate_role_id = "secondary-patient-id"
    current_claims = {
        "uid": "test-uid",
    }

    with pytest.raises(Exception):
        role_auth.delegate_role(
            current_claims, "Patient", main_role_id, delegate_role_id
        )


def test_delegate_role_fail_when_main_role_id_not_existing():
    delegate_role_id = "secondary-patient-id"

    # only have practitioner role, not able to delegate for patient
    current_claims = {
        "uid": "test-uid",
        "roles": {
            "Practitioner": {
                "id": "doctor-id",
            },
        },
    }

    with pytest.raises(Exception):
        role_auth.delegate_role(
            current_claims, "Patient", "patient-id", delegate_role_id
        )


def test_delegate_role_fail_when_main_role_id_mismatch():
    delegate_role_id = "secondary-patient-id"
    current_claims = {
        "uid": "test-uid",
        "roles": {
            "Patient": {
                "id": "patient-id",
            },
        },
    }

    with pytest.raises(Exception):
        role_auth.delegate_role(
            current_claims, "Patient", "wrong-patient-id", delegate_role_id
        )


def test_extract_roles():
    expected_roles = {"Patient": {"id": "patient-id"}}
    custom_claims = {"roles": expected_roles}

    roles = role_auth.extract_roles(custom_claims)

    assert roles == expected_roles


def test_add_id_to_existing_roles():
    current_claims = {"uid": "test-uid", "roles": {"Staff": {}}}

    with patch("utils.role_auth.auth") as mock_auth:
        role_auth.grant_role(current_claims, "Staff", "staff-id")

        mock_auth.set_custom_user_claims.assert_called_once_with(
            "test-uid",
            {
                "roles": {
                    "Staff": {"id": "staff-id"},
                }
            },
        )


def test_is_authorized_unauthorized_for_user_without_claims_roles():
    claims_roles = None

    assert role_auth.is_authorized(claims_roles, "Patient", "patient-id") is False
    assert role_auth.is_authorized(claims_roles, "Patient", "*") is False
    assert (
        role_auth.is_authorized(claims_roles, "Practitioner", "practitioner-id")
        is False
    )
    assert role_auth.is_authorized(claims_roles, "Practitioner", "*") is False
    assert role_auth.is_authorized(claims_roles, "Staff", "staff-id") is False
    assert role_auth.is_authorized(claims_roles, "Staff", "*") is False
    assert role_auth.is_authorized(claims_roles, "Admin", None) is False


def test_is_authorized_admin_should_have_full_access():
    claims_roles = {"Admin": {}}

    assert role_auth.is_authorized(claims_roles, "Patient", "patient-id") is True
    assert role_auth.is_authorized(claims_roles, "Patient", "*") is True
    assert (
        role_auth.is_authorized(claims_roles, "Practitioner", "practitioner-id") is True
    )
    assert role_auth.is_authorized(claims_roles, "Practitioner", "*") is True
    assert role_auth.is_authorized(claims_roles, "Staff", "staff-id") is True
    assert role_auth.is_authorized(claims_roles, "Staff", "*") is True
    assert role_auth.is_authorized(claims_roles, "Admin", None) is True


def test_is_authorized_staff_should_have_access_to_patients_practitioners_themselves():
    claims_roles = {"Staff": {"id": "staff-id"}}

    assert role_auth.is_authorized(claims_roles, "Patient", "patient-id") is True
    assert role_auth.is_authorized(claims_roles, "Patient", "*") is True
    assert (
        role_auth.is_authorized(claims_roles, "Practitioner", "practitioner-id") is True
    )
    assert role_auth.is_authorized(claims_roles, "Practitioner", "*") is True
    assert role_auth.is_authorized(claims_roles, "Staff", "staff-id") is True
    assert role_auth.is_authorized(claims_roles, "Staff", "*") is False
    assert role_auth.is_authorized(claims_roles, "Admin", None) is False


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
    assert role_auth.is_authorized(claims_roles, "Staff", "staff-id") is False
    assert role_auth.is_authorized(claims_roles, "Staff", "*") is False
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
    assert role_auth.is_authorized(claims_roles, "Staff", "staff-id") is False
    assert role_auth.is_authorized(claims_roles, "Staff", "*") is False
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
    assert role_auth.is_authorized(claims_roles, "Staff", "staff-id") is False
    assert role_auth.is_authorized(claims_roles, "Staff", "*") is False
    assert role_auth.is_authorized(claims_roles, "Practitioner", "*") is False
    assert role_auth.is_authorized(claims_roles, "Admin", None) is False


def test_is_authorized_with_delegate_role():
    secondary_patient_1 = "secondary-patient-1"
    secondary_patient_2 = "secondary-patient-2"
    claim_roles = {
        "Patient": {
            "id": "primary-patient-id",
            "delegates": [secondary_patient_1, secondary_patient_2],
        },
    }

    assert role_auth.is_authorized(claim_roles, "Patient", secondary_patient_1)
    assert role_auth.is_authorized(claim_roles, "Patient", secondary_patient_2)
