"""
pytest would share the fixtures automatically from conftest.py
"""
from typing import Protocol

import pytest
from firebase_admin import auth
from flask.testing import FlaskClient

from app import app


class Client(Protocol):
    def __call__(self) -> FlaskClient:
        ...


@pytest.fixture
def client() -> Client:
    return app.test_client()


def pytest_bdd_after_scenario(request, feature, scenario):
    fixtures = ["patient", "practitioner", "doctor", "nurse", "patientA", "patientB"]

    for fixture in fixtures:
        if fixture in request.fixturenames:
            resource = request.getfixturevalue(fixture)
            auth.delete_user(resource.uid)
