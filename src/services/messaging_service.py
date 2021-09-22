from firebase_admin import messaging
from flask import Blueprint, Response, request

from utils.middleware import jwt_authenticated

messaging_blueprint = Blueprint("messaging", __name__, url_prefix="/messaging")


class MessagingController:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run

    def send_push_notification(self, request_body):
        fcm_token = request_body.get("fcm_token")
        title = request_body.get("title")
        body = request_body.get("body")

        if fcm_token is None:
            return Response(status=400, response="missing param: fcm_token")
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=fcm_token,
        )

        try:
            response = messaging.send(message, self.dry_run)
            return Response(status=200, response=response)
        except Exception as error:
            return Response(status=500, response=error)


@messaging_blueprint.route("/", methods=["POST"])
@jwt_authenticated()
def send_push_notification():
    request_body = request.get_json()
    return MessagingController().send_push_notification(request_body)
