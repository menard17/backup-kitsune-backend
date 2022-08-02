import stripe
from flask import Blueprint, Response, json, request

from adapters.fhir_store import ResourceClient
from services.account_service import AccountService
from services.invoice_service import InvoiceService
from services.payment_service import PaymentService
from utils.middleware import jwt_authenticated, jwt_authorized

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


# TODO: AB#812
@payments_blueprint.route("/", methods=["POST"])
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def create_payment():
    request.get_json()
    manual = request.args.get("manual")
    if manual is not None and manual == "false":
        return PaymentsController().create_payment(request)
    else:
        return PaymentsController().create_payment_manually(request)


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
    def __init__(
        self,
        resource_client=None,
        account_service=None,
        invoice_service=None,
        payment_service=None,
    ):
        self.resource_client = resource_client or ResourceClient()
        self.account_service = account_service or AccountService(self.resource_client)
        self.invoice_service = invoice_service or InvoiceService(self.resource_client)
        self.payment_service = payment_service or PaymentService(self.resource_client)

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

    def create_payment(self, request) -> tuple:
        """Returns the details of a invoice created.

        This creates a invoice in FHIR and payment request to stripe.
        Status of invoice and account is updated accordingly.

        :param request: the request for this operation
        :rtype: tuple
        """
        body = json.loads(request.data)
        customer_id = body["customerId"]
        payment_method_id = body["paymentMethodId"]
        amount = body["amount"]
        currency = "jpy"
        account_id = body["accountId"]

        err, account = self.account_service.get_account(account_id)
        if err is not None:
            return Response(status=400, response=err.args[0])
        patient_id = account.subject[0].reference.split("/")[1]

        err, invoice = self.invoice_service.create_invoice(
            account_id, patient_id, amount, currency
        )
        if err is not None:
            return Response(status=400, response=err.args[0])
        err, payment_intent_id = self.payment_service.create_payment(
            amount, currency, customer_id, payment_method_id
        )
        if err is not None:
            self.invoice_service.update_invoice_status(
                payment_intent_id, invoice.id, False, "CC payment failed"
            )
            return Response(
                status=500,
                response=json.dumps("Stripe did not proceed correctly"),
                mimetype="application/json",
            )
        self.invoice_service.update_invoice_status(payment_intent_id, invoice.id, True)
        self.account_service.inactivate_account(account_id)
        return Response(status=201)

    def create_payment_manually(self, request) -> tuple:
        """Returns the details of a invoice created.

        This creates another invoice in FHIR in addition to the cancelled ones
        Status of invoice and account is updated accordingly.
        Payment is not processed within the function.

        :param request: the request for this operation
        :rtype: tuple
        """
        body = json.loads(request.data)
        payment_intent_id = body["payment_intent_id"]
        amount = body["amount"]
        currency = "jpy"
        account_id = body["accountId"]
        err, account = self.account_service.get_account(account_id)
        if err is not None:
            return Response(status=400, response=err.args[0])
        patient_id = account.subject[0].reference.split("/")[1]

        err, invoice = self.invoice_service.create_invoice(
            account_id, patient_id, amount, currency
        )
        if err is not None:
            return Response(status=400, response=err.args[0])

        self.invoice_service.update_invoice_status(payment_intent_id, invoice.id, True)
        self.account_service.inactivate_account(account_id)
        return Response(status=201)

    def cancel_payment(self, encounter_id: str) -> Response:
        err, account = self.account_service.get_account(encounter_id)
        err, _ = self.account_service.in_activate_account(account.id)
        if err is None:
            return Response(status=204)
        else:
            return Response(status=400)
