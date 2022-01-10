import json
from unittest.mock import patch

from helper import FakeRequest

from blueprints.payments import PaymentsController

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
