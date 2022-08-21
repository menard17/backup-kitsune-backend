import base64
import logging

from flask import Blueprint, Response, request

from adapters.fhir_store import ResourceClient

notion_blueprint = Blueprint("notion", __name__, url_prefix="/notion")

log = logging.getLogger(__name__)


@notion_blueprint.route("/encounter", methods=["POST"])
def encounter() -> Response:
    return NotionController().post_encounter(request)


class NotionController:
    def __init__(self):
        self.resource_client = ResourceClient()

    def post_encounter(self, request) -> Response:
        """Post encounter to notion"""
        envelope = request.get_json()
        log.info(f"Envelope: {envelope}")

        if not envelope:
            msg = "no Pub/Sub message received"
            log.error(f"error: {msg}")
            return Response(
                status=400, response=f"Bad Request: {msg}", mimetype="text/plain"
            )
        log.info(f"Envelope: {envelope}")

        if not isinstance(envelope, dict) or "message" not in envelope:
            msg = "invalid Pub/Sub message format"
            log.error(f"error: {msg}")
            return Response(
                status=400, response=f"Bad Request: {msg}", mimetype="text/plain"
            )

        pubsub_message = envelope["message"]
        log.info(f"Pub/Sub Message: {pubsub_message}")
        if isinstance(pubsub_message, dict) and "data" in pubsub_message:
            data = base64.b64decode(pubsub_message["data"]).decode("utf-8").strip()
            log.info(f"Data: {data}")
        return Response(status=204, mimetype="application/json")

        # Add code to handle the encounter here

        # return Response(
        #     status=201, response="post encounter to notion", mimetype="text/plain"
        # )
