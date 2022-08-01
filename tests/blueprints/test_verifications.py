import pytest

from blueprints.verifications import VerficationController
from tests.blueprints.helper import FakeRequest


def test_start_verification_happy_path(verification_service):
    request = FakeRequest(
        data={"to": "+8100011112222", "channel": "sms", "locale": "ja"}
    )
    verification_service.start_verification.return_value = None, "pending"
    controller = VerficationController(verification_service)

    response = controller.start_verification(request)
    print(f"response: {response.json}")

    assert response.status_code == 200
    assert response.json == {"status": "pending"}
    verification_service.start_verification.assert_called_once_with(
        to="+8100011112222", channel="sms", locale="ja"
    )


def test_start_verification_with_error_response(verification_service):
    request = FakeRequest(
        data={"to": "+8100011112222", "channel": "sms", "locale": "ja"}
    )
    verification_service.start_verification.return_value = Exception("exception"), None
    controller = VerficationController(verification_service)

    response = controller.start_verification(request)

    assert response.status_code == 400
    verification_service.start_verification.assert_called_once_with(
        to="+8100011112222", channel="sms", locale="ja"
    )


def test_start_verification_with_internal_exception(verification_service):
    request = FakeRequest(
        data={"to": "+8100011112222", "channel": "sms", "locale": "ja"}
    )
    verification_service.start_verification.side_effect = Exception("exception")
    controller = VerficationController(verification_service)

    response = controller.start_verification(request)

    assert response.status_code == 500
    verification_service.start_verification.assert_called_once_with(
        to="+8100011112222", channel="sms", locale="ja"
    )


def test_check_verification_happy_path(verification_service):
    request = FakeRequest(data={"to": "+8100011112222", "code": "1234"})
    verification_service.check_verification.return_value = None, "accepted"
    controller = VerficationController(verification_service)

    response = controller.check_verification(request)
    print(f"response: {response.json}")

    assert response.status_code == 200
    assert response.json == {"status": "accepted"}
    verification_service.check_verification.assert_called_once_with(
        to="+8100011112222", code="1234"
    )


def test_check_verification_with_error_response(verification_service):
    request = FakeRequest(data={"to": "+8100011112222", "code": "1234"})
    verification_service.check_verification.return_value = Exception("exception"), None
    controller = VerficationController(verification_service)

    response = controller.check_verification(request)

    assert response.status_code == 400
    verification_service.check_verification.assert_called_once_with(
        to="+8100011112222", code="1234"
    )


def test_check_verification_with_internal_exception(verification_service):
    request = FakeRequest(data={"to": "+8100011112222", "code": "1234"})
    verification_service.check_verification.side_effect = Exception("exception")
    controller = VerficationController(verification_service)

    response = controller.check_verification(request)

    assert response.status_code == 500
    verification_service.check_verification.assert_called_once_with(
        to="+8100011112222", code="1234"
    )


@pytest.fixture
def verification_service(mocker):
    yield mocker.MagicMock()
