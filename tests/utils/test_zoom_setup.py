import os

import pytest

from utils.zoom_setup import ZoomObject


def test_set_key_and_secret(url_path):
    zoom_object = ZoomObject(url_path)
    assert zoom_object.key == "zoom key"
    assert zoom_object.secret == "zoom secret"


@pytest.fixture(autouse=True)
def url_path():
    return f"{os.path.dirname(os.path.abspath(__file__))}/secrets"
