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


@payments_blueprint.route("/customer/<customer_id>", methods=["GET"])
@jwt_authenticated()
def get_customer(customer_id: str):
    """Returns details of a customer.

    :param customer_id: uid for customer
    :type customer_id: str

    :rtype: Object
    """
    customer = stripe.Customer.retrieve(customer_id)
    return customer


@payments_blueprint.route("/payment-intent", methods=["POST"])
@jwt_authenticated()
def create_payment_intent():
    body = json.loads(request.data)
    customer_id = body["customerId"]
    payment_method_id = body["paymentMethodId"]
    amount = body["amount"]
    currency = 'jpy'

    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            customer=customer_id,
            payment_method=payment_method_id,
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


@payments_blueprint.route("/<customer_id>/payment-methods", methods=["GET"])
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


@payments_blueprint.route("/payment-methods/<payment_method_id>", methods=["GET"])
@jwt_authenticated()
def get_payment_method(payment_method_id: str):
    """Returns details of a payment method.

    :param payment_method_id: uid for payment method
    :type payment_method_id: str

    :rtype: Object
    """
    payment_method = stripe.PaymentMethod.retrieve(
        payment_method_id
    )

    return payment_method


@payments_blueprint.route("/payment-methods/<payment_method_id>", methods=["DELETE"])
@jwt_authenticated()
def detach_payment_method(payment_method_id: str):
    """Detaches a payment method from customer.

    :param payment_method_id: uid for payment method
    :type payment_method_id: str

    :rtype: Object
    """
    payment_method = stripe.PaymentMethod.detach(
        payment_method_id
    )

    return payment_method
