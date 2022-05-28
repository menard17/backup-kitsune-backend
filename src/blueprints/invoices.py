import json

from flask import Blueprint
from flask.wrappers import Response

from adapters.fhir_store import ResourceClient
from services.invoice_service import InvoiceService
from utils.middleware import jwt_authenticated, jwt_authorized

invoices_blueprint = Blueprint("invoices", __name__, url_prefix="/invoices")


@invoices_blueprint.route("/<invoice_id>", methods=["GET"])
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def get_invoice(invoice_id: str) -> Response:
    return InvoiceController().get_invoice(invoice_id)


class InvoiceController:
    def __init__(self, resource_client=None, invoice_service=None):
        self.resource_client = resource_client or ResourceClient()
        self.invoice_service = invoice_service or InvoiceService(self.resource_client)

    def get_invoice(self, invoice_id: str):
        err, invoice = self.invoice_service.get_invoice(invoice_id)
        if err is not None:
            return Response(status=400, response=err.args[0])
        return Response(status=200, response=json.dumps({"data": invoice.json()}))
