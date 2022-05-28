from typing import Tuple

from fhir.resources import construct_fhir_element
from fhir.resources.domainresource import DomainResource
from flask import Response

from adapters.fhir_store import ResourceClient
from utils.system_code import SystemCode


class InvoiceService:
    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def create_invoice(
        self,
        account_id: str,
        patient_id: str,
        amount: int,
        currency: str,
    ) -> Tuple[Exception, DomainResource]:
        """Returns invoice after creating invoice"""
        invoice = {
            "resourceType": "Invoice",
            "status": "issued",
            "subject": {"reference": f"Patient/{patient_id}"},
            "account": {"reference": f"Account/{account_id}"},
            "totalGross": {"value": amount, "currency": currency},
        }
        invoice_construct = construct_fhir_element(invoice["resourceType"], invoice)

        invoice = self.resource_client.create_resource(invoice_construct)
        return None, invoice

    def update_invoice_status(
        self,
        payment_intent_id: str,
        invoice_id: str,
        is_successful: bool,
        reason: str = None,
    ) -> Tuple[Exception, DomainResource]:
        """Update invoice status

        :param payment_intent_id: id for the payment
        :type payment_intent_id: str
        :param invoice_id: uuid for invoice
        :type invoice_id: str
        :param is_successful: if payment is successfully processed or not.
        :type is_successful: bool

        :rtype: Tuple[Exception, DomainResource]
        """
        err, invoice = self.get_invoice(invoice_id)
        if err is not None:
            return Response(status=400, response=err.args[0])
        construct_invoice = construct_fhir_element("Invoice", invoice)
        if is_successful:
            construct_invoice.status = "balanced"
            construct_invoice.extension = [SystemCode.payment_intent(payment_intent_id)]
        else:
            construct_invoice.status = "cancelled"
            construct_invoice.cancelledReason = reason
            construct_invoice.extension = [SystemCode.payment_intent(payment_intent_id)]
        invoice = self.resource_client.put_resource(invoice_id, construct_invoice)
        return None, invoice

    def get_invoice(self, invoice_id: str) -> Tuple[Exception, DomainResource]:
        """Returns invoice by invoice id

        :param invoice_id: uuid for invoice
        :type invoice_id: str

        rtype: Tuple[Exception, DomainResource]
        """
        invoice = self.resource_client.get_resource(invoice_id, "Invoice")
        return None, invoice

    def get_invoice_by_account_id(
        self, account_id: str
    ) -> Tuple[Exception, DomainResource]:
        """Returns invoice by account id

        :param account_id: uuid for account
        :type account_id: str

        rtype: Tuple[Exception, DomainResource]
        """
        result = self.resource_client.search(
            "Invoice",
            search=[("account", account_id)],
        )
        return None, result
