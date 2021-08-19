import pytest
import os

from utils.stripe_setup import StripeSingleton


def test_initialized_twice(mock_stripe, url_path):
    StripeSingleton(mock_stripe, base_path=url_path)

    with pytest.raises(Exception):
        StripeSingleton(mock_stripe, base_path=url_path)


def test_load_secret(mock_stripe, url_path):
    StripeSingleton(mock_stripe, base_path=url_path)
    assert mock_stripe.api_key == "test_key"


def test_call_stripe_after_singleton_creation(url_path):
    import stripe

    StripeSingleton(stripe, url_path)

    # re-importing stripe and see if key is set globally
    # flake8: noqa
    import stripe

    assert stripe.api_key == "test_key"


@pytest.fixture(autouse=True)
def url_path():
    return f"{os.path.dirname(os.path.abspath(__file__))}/secrets"
