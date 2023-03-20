import json
import os

from flask import Blueprint, Response

from json_serialize import json_serial
from utils.middleware import jwt_authenticated

config_blueprint = Blueprint("config", __name__, url_prefix="/config")


@jwt_authenticated()
@config_blueprint.route("/", methods=["GET"])
def get_list_id() -> Response:
    return ConfigController().get_list_id()


@config_blueprint.route("/questionnaire", methods=["GET"])
def get_prequestionnaire_id() -> Response:
    return ConfigController().get_prequestionnaire_id()


class ConfigController:
    def get_list_id(self) -> Response:
        "This is a mitigation plan to have an env variable to contain list id."
        LIST_ID = os.getenv("LIST_ID")

        return Response(
            status=200,
            response=json.dumps(
                {"patientQueueListId": LIST_ID},
                default=json_serial,
            ),
        )

    def get_prequestionnaire_id(self) -> Response:
        PREQUESTIONNAIRE_ID = os.getenv("PREQUESTIONNAIRE_ID")

        return Response(
            status=200,
            response=json.dumps(
                {"prequestionnaireId": PREQUESTIONNAIRE_ID},
                default=json_serial,
            ),
        )
