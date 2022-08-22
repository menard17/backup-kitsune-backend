import os
from multiprocessing import Process

import stripe
from flask import Blueprint, Response, json, request

from adapters.fhir_store import ResourceClient
from adapters.fire_storage import StorageClient
from adapters.fire_store import FireStoreClient
from services.account_service import AccountService
from services.invoice_service import InvoiceService
from services.patient_service import PatientService
from services.payment_service import PaymentService
from utils.middleware import jwt_authenticated, jwt_authorized

payments_blueprint = Blueprint("payments", __name__, url_prefix="/payments")
BUCKET_NAME = os.getenv("BUCKET_NAME")
OBJECT_NAME = os.getenv("PROCESSED_BULK_PAYMENT_FILES")


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


@payments_blueprint.route("/bulk", methods=["POST"])
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def create_bulk_payments():
    return PaymentsController().create_bulk_payments(request)


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


class PaymentObject:
    def __init__(self, account, patient, amount, currency, description):
        self.account = account
        self.patient = patient
        self.amount = amount
        self.currency = currency
        self.description = description
        self._error = []

    @property
    def error(self):
        return self._error

    @error.setter
    def error(self, new_error: Exception):
        self._error.append(new_error.args[0])

    def get_json(self):
        if self._error:
            status = "error"
        else:
            status = "success"

        return {
            "accountId": self.account,
            "status": status,
            "price": self.amount,
            "currency": self.currency,
            "patientId": self.patient,
            "description": ",".join(self._error),
        }

    def is_valid(self):
        return bool(
            self.currency
            and self.amount
            and self.description
            and (self.patient or self.account)
        )


class PaymentsController:
    def __init__(
        self,
        resource_client=None,
        account_service=None,
        invoice_service=None,
        payment_service=None,
        firestore_client=None,
        storage_client=None,
        patient_service=None,
    ):
        self.resource_client = resource_client or ResourceClient()
        self.account_service = account_service or AccountService(self.resource_client)
        self.invoice_service = invoice_service or InvoiceService(self.resource_client)
        self.payment_service = payment_service or PaymentService(self.resource_client)
        self.firestore_client = firestore_client or FireStoreClient()
        self.storage_client = storage_client or StorageClient()
        self.patient_service = patient_service or PatientService(self.resource_client)

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

    def _create_payment(
        self, amount: str, currency: str, account_id: str, description: str = None
    ) -> tuple[Exception, str]:

        # Get Active Account
        err_account, account = self.account_service.get_account(account_id, True)
        if err_account is not None:
            return err_account, None
        patient_id = account.subject[0].reference.split("/")[1]

        # Create Invoice
        err_invoice, invoice = self.invoice_service.create_invoice(
            account_id, patient_id, amount, currency
        )
        if err_invoice is not None:
            return err_invoice, None

        # Get Payment Details
        (
            err_patient_payment,
            payment_details,
        ) = self.patient_service.get_patient_payment_details(patient_id)
        if err_patient_payment is not None:
            return err_patient_payment, None

        # Create Payment
        customer_id, payment_method_id = payment_details
        err_payment, payment_intent_id = self.payment_service.create_payment(
            amount, currency, customer_id, payment_method_id, description, account_id
        )
        if err_payment is not None:
            self.invoice_service.update_invoice_status(
                payment_intent_id, invoice.id, False, "CC payment failed"
            )
            return err_payment, None
        self.invoice_service.update_invoice_status(payment_intent_id, invoice.id, True)
        self.account_service.inactivate_account(account_id)
        return None, None

    def create_payment(self, request) -> tuple:
        """Returns the details of a invoice created.

        This creates a invoice in FHIR and payment request to stripe.
        Status of invoice and account is updated accordingly.

        :param request: the request for this operation
        :rtype: tuple
        """
        body = json.loads(request.data)
        amount = body["amount"]
        currency = "jpy"
        account_id = body["accountId"]

        err, _ = self._create_payment(amount, currency, account_id)

        if err is not None:
            return Response(
                status=500,
                response=json.dumps("Stripe did not proceed correctly"),
                mimetype="application/json",
            )
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
        err, account = self.account_service.get_account(account_id, True)
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

    def create_bulk_payments(self, request) -> Response:
        """
        Returns response with status 202 if background job starts without any error
        Returns response with status 400 if background job was not started
        """
        request_body = request.get_json()
        collection = request_body.get("collection")
        collection_id = request_body.get("collectionId")
        contents = request_body.get("contents")

        if collection and collection_id and contents:
            heavy_process = Process(
                target=self.create_bulk_payment_job,
                args=(collection, collection_id, contents),
                daemon=True,
            )
            heavy_process.start()
            return Response(mimetype="application/json", status=202)

        if collection and collection_id:
            self.firestore_client.update_value(
                collection, collection_id, {"status": "error"}
            )
        return Response(status=400, response="Validation Error")

    def create_bulk_payment_job(
        self,
        collection: str,
        collection_id: str,
        contents: list,
        bucket_name: str = BUCKET_NAME,
        object_name: str = OBJECT_NAME,
    ):
        # Change the status in firebase store to in-progress
        self.firestore_client.update_value(
            collection, collection_id, {"status": "in-progress"}
        )

        output = []
        for item in contents:
            account_id = item.get("account")
            patient_id = item.get("patient")
            amount = item.get("amount")
            currency = item.get("currency")
            description = item.get("description")
            payment_obj = PaymentObject(
                account_id, patient_id, amount, currency, description
            )
            result = self._create_payment_helper(payment_obj)
            output.append(result)

        # Upload output to gcs
        base_storage_url = self.storage_client.upload_blob_from_memory(
            output, bucket_name, object_name, collection_id
        )

        # Change the status in firebase store to success
        self.firestore_client.update_value(
            collection, collection_id, {"processedURL": base_storage_url}
        )
        self.firestore_client.update_value(
            collection, collection_id, {"status": "success"}
        )

    def _create_payment_helper(self, payment_obj: PaymentObject):
        # Check if payment object is valid or not
        if not payment_obj.is_valid():
            payment_obj.error = Exception("Invalid payment input")
            return payment_obj.get_json()

        # If Account is not provide, create account from patient id
        if not payment_obj.account:
            err_account, account = self.account_service.create_account_resource(
                payment_obj.patient, payment_obj.description
            )
            if err_account is not None:
                payment_obj.error = err_account
            else:
                payment_obj.account = account.id

        # Create Payment
        if not payment_obj.error:
            err_payment, _ = self._create_payment(
                payment_obj.amount,
                payment_obj.currency,
                payment_obj.account,
                payment_obj.description,
            )
            if err_payment is not None:
                payment_obj.error = err_payment
        return payment_obj.get_json()
