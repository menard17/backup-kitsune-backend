import structlog
from typing import Optional

import stripe

from adapters.fhir_store import ResourceClient

log = structlog.get_logger()


class PaymentService:
    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def create_payment(
        self,
        amount: str,
        currency: str,
        customer_id: str,
        payment_method_id: str,
        description: str = "診療費用等",
        account_id: Optional[str] = None,
    ) -> tuple[Exception, str]:
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                customer=customer_id,
                payment_method=payment_method_id,
                idempotency_key=account_id,
                off_session=True,
                confirm=True,
                description=description,
            )
            payment_intent_id = payment_intent["id"]
            return None, payment_intent_id

        except stripe.error.CardError as e:
            err = e.error
            # Error code will be authentication_required
            # if authentication is needed
            log.error("Code is: %s" % err.code)
            payment_intent_id = err.payment_intent["id"]
            return Exception(err.message), payment_intent_id
        except (
            stripe.error.InvalidRequestError,
            stripe.error.APIError,
            stripe.error.IdempotencyError,
        ) as e:
            err = e.error
            return Exception(err.message), None
