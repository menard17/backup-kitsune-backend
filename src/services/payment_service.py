import logging
from typing import Tuple

import stripe

from adapters.fhir_store import ResourceClient

log = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def create_payment(
        self, amount, currency, customer_id, payment_method_id
    ) -> Tuple[Exception, str]:
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                customer=customer_id,
                payment_method=payment_method_id,
                off_session=True,
                confirm=True,
                description="診療費用等",  # This shows up on the receipt
            )
            payment_intent_id = payment_intent["id"]
            return None, payment_intent_id

        except stripe.error.CardError as e:
            err = e.error
            # Error code will be authentication_required
            # if authentication is needed
            log.error("Code is: %s" % err.code)
            payment_intent_id = err.payment_intent["id"]
            return err, payment_intent_id
