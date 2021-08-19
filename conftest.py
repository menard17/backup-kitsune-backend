import pytest
from utils.stripe_setup import StripeSingleton


class MockStripe:
    api_key: str = None


@pytest.fixture(autouse=True)
def mock_stripe():
    yield MockStripe()
    StripeSingleton._instance = None
