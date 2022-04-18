import pytest

from blueprints.accounts import AccountController
from tests.blueprints.helper import FakeRequest


@pytest.fixture
def account_service(mocker, patient_id):
    mock_account_service = mocker.Mock()
    mocker.patch.object(
        mock_account_service,
        "get_account",
        return_value=(None, MockAccount(patient_id)),
    )
    yield mock_account_service


@pytest.fixture
def account_id():
    return "account_id"


@pytest.fixture
def patient_id():
    return "patient_id"


@pytest.fixture
def practitioner_id():
    return "practitioner_id"


@pytest.fixture
def staff_id():
    return "staff_id"


@pytest.fixture
def wrong_patient_id():
    return "wrong_patient_id"


class MockSubjct:
    def __init__(self, patient_id):
        self.reference = patient_id


class MockAccount:
    def __init__(self, patient_id):
        self.subject = MockSubjct(patient_id)

    def json(self):
        return {}


def test_get_account_when_role_is_staff(
    resource_client, account_service, account_id, staff_id
):
    # Given
    account_controller = AccountController(resource_client, account_service)
    request = FakeRequest(
        claims={
            "roles": {
                "Staff": {
                    "id": staff_id,
                },
            },
        },
    )
    # When
    response = account_controller.get_account(request, account_id)

    # Then
    response.status_code == 200


def test_get_account_when_roles_are_staff_and_patient(
    resource_client, account_service, account_id, patient_id, staff_id
):
    # Given
    account_controller = AccountController(resource_client, account_service)
    request = FakeRequest(
        claims={
            "roles": {
                "Staff": {
                    "id": staff_id,
                },
                "Patient": {"id": patient_id},
            },
        },
    )
    # When
    response = account_controller.get_account(request, account_id)

    # Then
    response.status_code == 200


def test_get_account_when_role_is_practitioner(
    resource_client, account_service, account_id, practitioner_id
):
    # Given
    account_controller = AccountController(resource_client, account_service)
    request = FakeRequest(
        claims={
            "roles": {
                "Practitioner": {
                    "id": practitioner_id,
                },
            },
        },
    )
    # When
    response = account_controller.get_account(request, account_id)

    # Then
    response.status_code == 401


def test_get_account_when_role_has_correct_patient_id(
    resource_client, account_service, account_id, patient_id
):
    # Given
    account_controller = AccountController(resource_client, account_service)
    request = FakeRequest(
        claims={
            "roles": {
                "Patient": {
                    "id": patient_id,
                },
            },
        },
    )
    # When
    response = account_controller.get_account(request, account_id)

    # Then
    response.status_code == 401


def test_get_account_when_role_has_wrong_patient_id(
    resource_client, account_service, account_id, wrong_patient_id
):
    # Given
    account_controller = AccountController(resource_client, account_service)
    request = FakeRequest(
        claims={
            "roles": {
                "Practitioner": {
                    "id": wrong_patient_id,
                },
            },
        },
    )
    # When
    response = account_controller.get_account(request, account_id)

    # Then
    response.status_code == 401


def test_get_account_when_roles_are_staff_and_practitioner(
    resource_client, account_service, account_id, staff_id, practitioner_id
):
    # Given
    account_controller = AccountController(resource_client, account_service)
    request = FakeRequest(
        claims={
            "roles": {
                "Staff": {
                    "id": staff_id,
                },
                "Practitioner": {"id": practitioner_id},
            },
        },
    )
    # When
    response = account_controller.get_account(request, account_id)

    # Then
    response.status_code == 401
