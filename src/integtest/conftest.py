"""
pytest would share the fixtures automatically from conftest.py
"""
import pytest

from app import app


@pytest.fixture
def client():
    return app.test_client()
