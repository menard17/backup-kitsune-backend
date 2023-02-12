import json
import logging

from flask import Blueprint, request
from flask.wrappers import Response

from services.verification_service import VerificationService
from utils.middleware import jwt_authenticated

verifications_blueprint = Blueprint("verifications", __name__, url_prefix="/")

log = logging.getLogger()


@jwt_authenticated()
@verifications_blueprint.route("verifications", methods=["POST"])
def start_verification() -> Response:
    return VerficationController().start_verification(request)


@jwt_authenticated()
@verifications_blueprint.route("verification_checks", methods=["POST"])
def check_verification() -> Response:
    return VerficationController().check_verification(request)


class VerficationController:
    def __init__(self, verification_service=None):
        self._verification_service = verification_service or VerificationService()

    def start_verification(self, request) -> Response:
        request_body = request.get_json()
        to = request_body.get("to")
        channel = request_body.get("channel")
        locale = request_body.get("locale")

        try:
            err, verification_status = self._verification_service.start_verification(
                to=to, channel=channel, locale=locale
            )
            if err is not None:
                return Response(status=400, response=err.args[0], mimetype="text/plain")
            return Response(
                status=200,
                response=json.dumps({"status": verification_status}),
                mimetype="application/json",
            )
        except Exception:
            err_msg = (
                f"There was a problem with starting verification. Input: {request_body}"
            )
            log.exception(err_msg)
            return Response(
                status=500,
                response=err_msg,
                mimetype="text/plain",
            )

    def check_verification(self, request) -> Response:
        request_body = request.get_json()
        to = request_body.get("to")
        code = request_body.get("code")

        try:
            (
                err,
                verification_check_status,
            ) = self._verification_service.check_verification(to=to, code=code)
            if err is not None:
                return Response(status=400, response=err.args[0], mimetype="text/plain")

            return Response(
                status=200,
                response=json.dumps({"status": verification_check_status}),
                mimetype="application/json",
            )
        except Exception:
            err_msg = (
                f"There was a problem with checking verification. Input: {request_body}"
            )
            log.exception(err_msg)
            return Response(
                status=500,
                response=err_msg,
                mimetype="text/plain",
            )
