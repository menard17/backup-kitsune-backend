import json
import os

from flask import Blueprint, Response, request

from json_serialize import json_serial
from utils.middleware import jwt_authenticated

config_blueprint = Blueprint("config", __name__, url_prefix="/config")


@jwt_authenticated()
@config_blueprint.route("/", methods=["GET"])
def get_list_id() -> Response:
    return ConfigController().get_list_id(request)


class ConfigController:
    def get_list_id(self, request) -> Response:
        "This is a mitigation plan to have an env variable to contain list id."
        LIST_ID = os.getenv("LIST_ID")

        return Response(
            status=200,
            response=json.dumps(
                {"list_id": LIST_ID},
                default=json_serial,
            ),
        )
