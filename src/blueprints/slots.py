from flask import Blueprint, Response

from adapters.fhir_store import ResourceClient
from services.slots_service import SlotService
from utils.middleware import jwt_authenticated

slots_blueprint = Blueprint("slots", __name__, url_prefix="/slots")


@slots_blueprint.route("/<slot_id>/free", methods=["PUT"])
@jwt_authenticated()
def free_slot(slot_id: str):
    return SlotsController().free_slot(slot_id)


class SlotsController:
    def __init__(
        self,
        resource_client=None,
        slot_service=None,
    ):
        self.resource_client = resource_client or ResourceClient()
        self.slot_service = slot_service or SlotService(self.resource_client)

    def free_slot(self, slot_id) -> Response:
        err, slot = self.slot_service.update_slot(slot_id, "free")
        if err is not None:
            return Response(status=400, response=err.args[0])

        resources = [slot]
        self.resource_client.create_resources(resources)

        return Response(status=204)
