import pytest
from resource_client import ResourceClient


def test_resource_client():
    sessino_mock = pytest.mock()
    resource = pytest.mock()
    resource_client = ResourceClient(sessino_mock)
    resource_client.get_srouce
