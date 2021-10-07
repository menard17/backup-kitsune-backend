import datetime
import json
import time

import jwt
from flask import Blueprint, Response

from json_serialize import json_serial
from utils.middleware import jwt_authenticated
from utils.zoom_setup import ZoomObject

zoom_blueprint = Blueprint("zoom", __name__, url_prefix="/zoom_jwt")


@zoom_blueprint.route("/", methods=["GET"])
@jwt_authenticated()
def zoom_jwt() -> Response:
    token = get_zoom_jwt()

    return Response(
        status=200,
        response=json.dumps(
            {
                "data": {
                    "jwt": token,
                }
            },
            default=json_serial,
        ),
    )


def get_zoom_jwt(zoom_object=None) -> str:
    """Get jwt from api key and sec. It should be authenticated with token from firebase"""
    if not zoom_object:
        zoom_object = ZoomObject()
    zoom_api_key = zoom_object.key
    zoom_api_secret = zoom_object.secret
    exp = datetime.datetime.now() + datetime.timedelta(hours=2)

    payload = {
        "appKey": zoom_api_key,
        "iat": time.mktime(datetime.datetime.now().timetuple()),
        "exp": time.mktime(exp.timetuple()),
        "tokenExp": time.mktime(exp.timetuple()),
    }

    jwt_encoded = jwt.encode(payload, zoom_api_secret)
    return jwt_encoded
