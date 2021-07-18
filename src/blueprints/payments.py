from flask import Blueprint
from flask.globals import request
from adapters import fhir_store
from middleware import jwt_authenticated
import os
import stripe
import json

payments_blueprint = Blueprint("payments", __name__, url_prefix="/payments")

key = os.environ.get("STRIPE_API_KEY")
stripe.api_key = key


@payments_blueprint.route("/customer", methods=["POST"])
@jwt_authenticated()
def create_customer():
    body = json.loads(request.data)
    email = body["email"]
    account = stripe.Customer.create(
        email=email
    )
    return account


@payments_blueprint.route("/payment-intent", methods=["POST"])
@jwt_authenticated()
def create_payment_intent():
    body = json.loads(request.data)
    customer_id = body["customerId"]

    try:
        payment_methods = stripe.PaymentMethod.list(
            customer=customer_id,
            type="card",
        )

        # Only for Testing purposes.
        # Will need to add logic to calculate payment
        # through admin UI
        payment_intent = stripe.PaymentIntent.create(
            amount=1099,
            currency='jpy',
            customer=customer_id,
            payment_method=payment_methods.data[0].id,
            off_session=True,
            confirm=True,
        )

        return payment_intent
    except stripe.error.CardError as e:
        err = e.error
        # Error code will be authentication_required if authentication is needed
        print("Code is: %s" % err.code)
        payment_intent_id = err.payment_intent['id']
        error_payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return error_payment_intent


@payments_blueprint.route("/setup-intent", methods=["POST"])
@jwt_authenticated()
def create_setup_intent():
    body = json.loads(request.data)
    customer_id = body["customerId"]
    intent = stripe.SetupIntent.create(
        customer=customer_id
    )
    return intent


@payments_blueprint.route("/payment-methods/<customer_id>", methods=["GET"])
@jwt_authenticated()
def get_payment_methods(customer_id: str):
    """Returns details of a customer's payment methods.

    :param customer_id: uid for customer
    :type customer_id: str

    :rtype: array
    """
    payment_methods = stripe.PaymentMethod.list(
        customer=customer_id,
        type="card",
    )

    return payment_methods
