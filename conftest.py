import pytest

from utils.stripe_setup import StripeSingleton


class MockStripe:
    api_key: str = None


@pytest.fixture(autouse=True)
def mock_stripe():
    yield MockStripe()
    StripeSingleton._instance = None


@pytest.fixture
def resource_client(mocker):
    yield mocker.Mock()


@pytest.fixture
def firebase_auth(mocker):
    yield mocker.Mock()
