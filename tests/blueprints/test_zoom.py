import jwt

from blueprints.zoom import get_zoom_jwt


class MockZoomObject:
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret


def test_zoom():
    """Set the USER env var to assert the behavior."""
    KEY = "Key"
    SECRET = "Secret"
    zoom_object = MockZoomObject(KEY, SECRET)
    token = get_zoom_jwt(zoom_object)
    decoded_token = jwt.decode(token, SECRET, algorithms="HS256")

    assert KEY == decoded_token["appKey"]
