import json
from unittest.mock import Mock, call, patch

from helper import FakeRequest, MockResourceClient

from blueprints.payments import PaymentObject, PaymentsController

CUSTOMER_DATA = json.dumps(
    {
        "email": "fake-email",
        "id": "fake-id",
    }
)

SETUP_INTENT_DATA = json.dumps(
    {
        "customer": "fake-customer",
        "id": "fake-id",
    }
)

PAYMENT_METHOD_DATA = json.dumps(
    {
        "billing_details": {
            "address": {},
            "email": "fake-email",
            "name": "fake-name",
        },
        "card": {
            "brand": "visa",
            "last4": "4242",
        },
        "customer": "fake-customer",
        "id": "fake-id",
        "object": "payment_method",
        "type": "card",
    }
)

PAYMENT_METHODS_DATA = json.dumps(
    {
        "data": [PAYMENT_METHOD_DATA],
        "has_more": "false",
        "object": "list",
        "url": "/v1/payment_methods",
    }
)

PAYMENT_INTENT_DATA = json.dumps(
    {
        "amount": 1000,
        "charges": {},
        "currency": "jpy",
        "customer": "fake-customer",
        "id": "fake-id",
        "object": "payment_intent",
        "payment_method_types": ["card"],
        "status": "succeeded",
    }
)

PAYMENT_INTENTS_DATA = json.dumps(
    {
        "data": [PAYMENT_INTENT_DATA],
        "has_more": "false",
        "object": "list",
        "url": "/v1/payment_intents",
    }
)


@patch("blueprints.payments.stripe")
def test_create_customer(mock_stripe):
    request = FakeRequest(
        data=json.dumps({"email": "fake-email"}),
        claims={"uid": "test-uid", "email_verified": True},
    )
    mock_stripe.Customer.create.return_value = CUSTOMER_DATA
    controller = PaymentsController()

    result = controller.create_customer(request)

    assert result.status_code == 201
    assert json.loads(result.data) == CUSTOMER_DATA
    mock_stripe.Customer.create.assert_called_once_with(email="fake-email")


@patch("blueprints.payments.stripe")
def test_get_customer(mock_stripe):
    mock_stripe.Customer.retrieve.return_value = CUSTOMER_DATA
    controller = PaymentsController()

    result = controller.get_customer("fake-id")

    assert result.status_code == 200
    assert json.loads(result.data) == CUSTOMER_DATA
    mock_stripe.Customer.retrieve.assert_called_once_with("fake-id")


@patch("blueprints.payments.stripe")
def test_create_setup_intent(mock_stripe):
    request = FakeRequest(
        data=json.dumps({"customerId": "fake-id"}),
        claims={"uid": "test-uid", "email_verified": True},
    )
    mock_stripe.SetupIntent.create.return_value = SETUP_INTENT_DATA
    controller = PaymentsController()

    result = controller.create_setup_intent(request)

    assert result.status_code == 201
    assert json.loads(result.data) == SETUP_INTENT_DATA
    mock_stripe.SetupIntent.create.assert_called_once_with(customer="fake-id")


@patch("blueprints.payments.stripe")
def test_get_payment_methods(mock_stripe):
    mock_stripe.PaymentMethod.list.return_value = PAYMENT_METHODS_DATA
    controller = PaymentsController()

    result = controller.get_payment_methods("fake-id")

    assert result.status_code == 200
    assert json.loads(result.data) == PAYMENT_METHODS_DATA
    mock_stripe.PaymentMethod.list.assert_called_once_with(
        customer="fake-id", type="card"
    )


@patch("blueprints.payments.stripe")
def test_get_payment_method(mock_stripe):
    mock_stripe.PaymentMethod.retrieve.return_value = PAYMENT_METHOD_DATA
    controller = PaymentsController()

    result = controller.get_payment_method("fake-id")

    assert result.status_code == 200
    assert json.loads(result.data) == PAYMENT_METHOD_DATA
    mock_stripe.PaymentMethod.retrieve.assert_called_once_with("fake-id")


@patch("blueprints.payments.stripe")
def test_detach_payment_method(mock_stripe):
    mock_stripe.PaymentMethod.detach.return_value = PAYMENT_METHOD_DATA
    controller = PaymentsController()

    result = controller.detach_payment_method("fake-id")

    assert result.status_code == 200
    assert json.loads(result.data) == PAYMENT_METHOD_DATA
    mock_stripe.PaymentMethod.detach.assert_called_once_with("fake-id")


@patch("blueprints.payments.stripe")
def test_create_payment_intent(mock_stripe):
    request = FakeRequest(
        data=json.dumps(
            {
                "customerId": "fake-customer-id",
                "paymentMethodId": "fake-payment-method-id",
                "amount": 1000,
            }
        ),
        claims={"uid": "test-uid", "email_verified": True},
    )
    mock_stripe.PaymentIntent.create.return_value = PAYMENT_INTENT_DATA
    controller = PaymentsController()

    result = controller.create_payment_intent(request)

    assert result.status_code == 201
    assert json.loads(result.data) == PAYMENT_INTENT_DATA
    mock_stripe.PaymentIntent.create.assert_called_once_with(
        amount=1000,
        currency="jpy",
        customer="fake-customer-id",
        payment_method="fake-payment-method-id",
        off_session=True,
        confirm=True,
        description="診療費用等",
    )


@patch("blueprints.payments.stripe")
def test_get_payment_intents(mock_stripe):
    mock_stripe.PaymentIntent.list.return_value = PAYMENT_INTENTS_DATA
    controller = PaymentsController()

    result = controller.get_payment_intents("fake-id")

    assert result.status_code == 200
    assert json.loads(result.data) == PAYMENT_INTENTS_DATA
    mock_stripe.PaymentIntent.list.assert_called_once_with(customer="fake-id")


@patch("blueprints.payments.stripe")
def test_get_payment_intent(mock_stripe):
    mock_stripe.PaymentIntent.retrieve.return_value = PAYMENT_INTENT_DATA
    controller = PaymentsController()

    result = controller.get_payment_intent("fake-id")

    assert result.status_code == 200
    assert json.loads(result.data) == PAYMENT_INTENT_DATA
    mock_stripe.PaymentIntent.retrieve.assert_called_once_with("fake-id")


class TestIsPaymentValid:
    def test_is_payment_valid_when_amount_is_none(self):
        # Given
        currency = None
        amount = "1"
        account_id = "account id"
        patient_id = "patient id"
        description = "description"

        # Wehn
        payment_obj = PaymentObject(
            account=account_id,
            patient=patient_id,
            amount=amount,
            currency=currency,
            description=description,
        )

        # Then
        assert not payment_obj.is_valid()

    def test_is_payment_valid_when_account_is_none(self):
        # Given
        currency = "yen"
        amount = "1"
        account_id = None
        patient_id = "patient id"
        description = "description"

        # Wehn
        payment_obj = PaymentObject(
            account=account_id,
            patient=patient_id,
            amount=amount,
            currency=currency,
            description=description,
        )

        # Then
        assert payment_obj.is_valid()

    def test_is_payment_valid_when_patient_and_account_are_none(self):
        # Given
        currency = "yen"
        amount = "1"
        account_id = None
        patient_id = None
        description = "description"

        # Wehn
        payment_obj = PaymentObject(
            account=account_id,
            patient=patient_id,
            amount=amount,
            currency=currency,
            description=description,
        )

        # Then
        assert not payment_obj.is_valid()

    def test_is_payment_valid(self):
        # Given
        currency = "yen"
        amount = "1"
        account_id = "account id"
        patient_id = "patient id"
        description = "description"

        # Wehn
        payment_obj = PaymentObject(
            account=account_id,
            patient=patient_id,
            amount=amount,
            currency=currency,
            description=description,
        )

        # Then
        assert payment_obj.is_valid()


class TestBulkPayment:
    def test_create_bulk_payment_invalid_without_collection(self):
        # Given
        requests = MockRequest()
        firestore_mock = Mock()
        firestore_mock.update_value = Mock()
        payment_controller = PaymentsController(
            MockResourceClient(), Mock(), Mock(), Mock(), firestore_mock
        )

        # When
        response = payment_controller.create_bulk_payments(requests)

        # Then
        firestore_mock.update_value.assert_not_called()
        assert response.status_code == 400

    def test_create_bulk_payment_invalid_with_collection(self):
        # Given
        collection = "collection"
        collection_id = "collection id"
        requests = MockRequest(collection, collection_id)
        firestore_mock = Mock()
        firestore_mock.update_value = Mock()
        payment_controller = PaymentsController(
            MockResourceClient(), Mock(), Mock(), Mock(), firestore_mock
        )

        # When
        response = payment_controller.create_bulk_payments(requests)

        # Then
        firestore_mock.update_value.assert_called_once_with(
            collection, collection_id, {"status": "error"}
        )
        assert response.status_code == 400

    def test_create_bulk_payment_valid_payment(self):
        # Given
        requests = MockRequest("collection", "collection id", [{"patient": "id"}])
        firestore_mock = Mock()
        firestore_mock.update_value = Mock()
        payment_controller = PaymentsController(
            MockResourceClient(), Mock(), Mock(), Mock(), firestore_mock
        )

        # When
        response = payment_controller.create_bulk_payments(requests)

        # Then
        assert response.status_code == 202

    def test_create_bulk_payment_job_invalid(self):
        # Given
        collection = "collection"
        collection_id = "collection id"
        contents = [{"patient": "id"}]
        firestore_mock = Mock()
        firestore_mock.update_value = Mock()
        storage_mock = Mock()
        storage_name = "storage name"
        bucket_name = "bucket"
        object_name = "object"

        # When
        storage_mock.upload_blob_from_memory = Mock(return_value=storage_name)
        payment_controller = PaymentsController(
            MockResourceClient(), Mock(), Mock(), Mock(), firestore_mock, storage_mock
        )
        payment_controller.create_bulk_payment_job(
            collection, collection_id, contents, bucket_name, object_name
        )

        # Then
        firestore_mock.update_value.assert_has_calls(
            [
                call(collection, collection_id, {"status": "in-progress"}),
                call(collection, collection_id, {"status": "success"}),
                call(collection, collection_id, {"processedURL": storage_name}),
            ],
            any_order=True,
        )
        storage_mock.upload_blob_from_memory.assert_called_once_with(
            [
                {
                    "accountId": None,
                    "currency": None,
                    "description": "Invalid payment input",
                    "patientId": "id",
                    "price": None,
                    "status": "error",
                }
            ],
            bucket_name,
            object_name,
            collection_id,
        )


class TestPaymentObject:
    def test_returns_multiple_error(self):
        # Given
        payment_obj = PaymentObject("account", "patient", "10", "jpy", "description")

        # When
        payment_obj.error = Exception("First error")
        payment_obj.error = Exception("Second error")

        # Then
        assert payment_obj.get_json()["status"] == "error"

    def test_returns_without_error(self):
        # Given
        payment_obj = PaymentObject("account", "patient", "10", "jpy", "description")

        # Then
        assert payment_obj.get_json()["status"] == "success"


class MockRequest:
    def __init__(self, collection=None, collection_id=None, contents=None):
        self.request_output = {}
        if collection:
            self.request_output["collection"] = collection
        if collection_id:
            self.request_output["collectionId"] = collection_id
        if contents:
            self.request_output["contents"] = contents

    def get_json(self):
        return self.request_output
