import jwt
import datetime
import os


def get_zoom_jwt() -> str:
    """Get jwt from api key and sec. It should be authenticated with token from firebase"""

    zoom_api_key = os.getenv("API_KEY")
    zoom_api_secret = os.getenv("API_SECRET")

    payload = {
        "iss": zoom_api_key,
        "exp": datetime.datetime.now() + datetime.timedelta(hours=2),
    }

    jwt_encoded = jwt.encode(payload, zoom_api_secret)
    return jwt_encoded
