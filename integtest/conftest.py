"""
pytest would share the fixtures automatically from conftest.py
"""
from typing import Protocol

import pytest
from flask.testing import FlaskClient

from app import app


class Client(Protocol):
    def __call__(self) -> FlaskClient:
        ...


@pytest.fixture
def client() -> Client:
    return app.test_client()
