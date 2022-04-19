import stripe
from flask import Blueprint, Response, json, request

from utils.middleware import jwt_authenticated

payments_blueprint = Blueprint("payments", __name__, url_prefix="/payments")


@payments_blueprint.route("/customer", methods=["POST"])
@jwt_authenticated()
def create_customer():
    return PaymentsController().create_customer(request)


@payments_blueprint.route("/customer/<customer_id>", methods=["GET"])
@jwt_authenticated()
def get_customer(customer_id: str):
    return PaymentsController().get_customer(customer_id)


@payments_blueprint.route("/payment-intent", methods=["POST"])
@jwt_authenticated()
def create_payment_intent():
    return PaymentsController().create_payment_intent(request)


@payments_blueprint.route("/setup-intent", methods=["POST"])
@jwt_authenticated()
def create_setup_intent():
    return PaymentsController().create_setup_intent(request)


@payments_blueprint.route("/<customer_id>/payment-methods", methods=["GET"])
@jwt_authenticated()
def get_payment_methods(customer_id: str):
    return PaymentsController().get_payment_methods(customer_id)


@payments_blueprint.route("/payment-methods/<payment_method_id>", methods=["GET"])
@jwt_authenticated()
def get_payment_method(payment_method_id: str):
    return PaymentsController().get_payment_method(payment_method_id)


@payments_blueprint.route("/payment-methods/<payment_method_id>", methods=["DELETE"])
@jwt_authenticated()
def detach_payment_method(payment_method_id: str):
    return PaymentsController().detach_payment_method(payment_method_id)


@payments_blueprint.route("/<customer_id>/payment-intents", methods=["GET"])
@jwt_authenticated()
def get_payment_intents(customer_id: str):
    return PaymentsController().get_payment_intents(customer_id)


@payments_blueprint.route("/payment-intent/<payment_intent_id>", methods=["GET"])
@jwt_authenticated()
def get_payment_intent(payment_intent_id: str):
    return PaymentsController().get_payment_intent(payment_intent_id)


class PaymentsController:
    def create_customer(self, request) -> Response:
        body = json.loads(request.data)
        email = body["email"]
        account = stripe.Customer.create(email=email)
        return Response(
            status=201, response=json.dumps(account), mimetype="application/json"
        )

    def get_customer(self, customer_id: str) -> Response:
        """Returns details of a customer.

        :param customer_id: uid for customer
        :type customer_id: str

        :rtype: Response
        """
        customer = stripe.Customer.retrieve(customer_id)
        return Response(
            status=200, response=json.dumps(customer), mimetype="application/json"
        )

    def create_setup_intent(self, request) -> Response:
        body = json.loads(request.data)
        customer_id = body["customerId"]
        intent = stripe.SetupIntent.create(customer=customer_id)
        return Response(
            status=201, response=json.dumps(intent), mimetype="application/json"
        )

    def get_payment_methods(self, customer_id) -> Response:
        """Returns details of a customer's payment methods.

        :param customer_id: uid for customer
        :type customer_id: str

        :rtype: Response
        """
        payment_methods = stripe.PaymentMethod.list(
            customer=customer_id,
            type="card",
        )

        return Response(
            status=200,
            response=json.dumps(payment_methods),
            mimetype="application/json",
        )

    def get_payment_method(self, payment_method_id) -> Response:
        """Returns details of a payment method.

        :param payment_method_id: uid for payment method
        :type payment_method_id: str

        :rtype: Response
        """
        payment_method = stripe.PaymentMethod.retrieve(payment_method_id)

        return Response(
            status=200, response=json.dumps(payment_method), mimetype="application/json"
        )

    def detach_payment_method(self, payment_method_id: str) -> Response:
        """Detaches a payment method from customer.

        :param payment_method_id: uid for payment method
        :type payment_method_id: str

        :rtype: Response
        """
        payment_method = stripe.PaymentMethod.detach(payment_method_id)

        return Response(
            status=200, response=json.dumps(payment_method), mimetype="application/json"
        )

    def create_payment_intent(self, request) -> Response:
        body = json.loads(request.data)

        customer_id = body["customerId"]
        payment_method_id = body["paymentMethodId"]
        amount = body["amount"]
        currency = "jpy"

        # TODO: AB#725
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

            return Response(
                status=201,
                response=json.dumps(payment_intent),
                mimetype="application/json",
            )
        except stripe.error.CardError as e:
            err = e.error
            # Error code will be authentication_required
            # if authentication is needed
            print("Code is: %s" % err.code)
            payment_intent_id = err.payment_intent["id"]
            error_payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return Response(
                stratus=500,
                response=json.dumps(error_payment_intent),
                mimetype="application/json",
            )

    def get_payment_intents(self, customer_id: str) -> Response:
        """Returns details of payment intents from a customer.

        :param customer_id: uid for customer
        :type customer_id: str

        :rtype: Response
        """

        try:
            payment_intents = stripe.PaymentIntent.list(customer=customer_id)
        except:  # noqa: E722
            error_message = (
                "There was a problem getting Payment Intents for customer: "
                + customer_id
            )
            return Response(status=500, response=error_message, mimetype="text/plain")

        return Response(
            status=200,
            response=json.dumps(payment_intents),
            mimetype="application/json",
        )

    def get_payment_intent(self, payment_intent_id: str) -> Response:
        """Returns details of a payment intent from a customer.

        :param payment_intent_id: uid for payment intent
        :type payment_intent_id: str

        :rtype: Response
        """
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        except:  # noqa: E722
            error_message = (
                "There was a problem getting Payment Intent for id: "
                + payment_intent_id
            )
            return Response(status=500, response=error_message, mimetype="text/plain")

        return Response(
            status=200, response=json.dumps(payment_intent), mimetype="application/json"
        )
