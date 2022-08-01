from unittest.mock import Mock

import pytest

from services.verification_service import VerificationService


def test_start_verification_happy_path(twilio_service):
    verification_service = VerificationService(twilio_service)

    err, status = verification_service.start_verification(
        to="+8100011112222", channel="sms", locale="ja"
    )

    assert err is None
    assert status == "pending"


def test_start_verification_disallowed_channels(twilio_service):
    verification_service = VerificationService(twilio_service)
    err, _ = verification_service.start_verification(
        to="+8100011112222", channel="voice", locale="ja"
    )

    assert err is not None
    assert err.args[0].startswith("Channel voice is not allowed")


def test_start_verification_unsupported_locales(twilio_service):
    verification_service = VerificationService(twilio_service)
    err, _ = verification_service.start_verification(
        to="+8100011112222", channel="sms", locale="vi"
    )

    assert err is not None
    assert err.args[0].startswith("Locale vi is not supported")


def test_check_verification_happy_path(twilio_service):
    verification_service = VerificationService(twilio_service)
    err, status = verification_service.check_verification(
        to="+8100011112222", code="1234"
    )

    assert err is None
    assert status == "accepted"


@pytest.fixture
def twilio_service(mocker):
    mocker.verification_checks = MockVerificationCheck()
    mocker.verifications = MockVerifications()
    yield mocker


class MockVerificationCheck:
    def create(self, to, code):
        mock = Mock()
        if to == "+8100011112222" and code == "1234":
            mock.status = "accepted"
            return mock


class MockVerifications:
    def create(self, to, channel):
        mock = Mock()
        if to == "+8100011112222" and channel == "sms":
            mock.status = "pending"
            return mock
