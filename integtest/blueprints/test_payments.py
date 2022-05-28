import json

from pytest_bdd import given, parsers, scenarios, then, when

from blueprints.payments import PaymentsController
from integtest.characters import Account, Appointment, Encounter, Patient, Practitioner
from integtest.conftest import Client
from integtest.utils import (
    create_appointment,
    create_encounter,
    create_patient,
    create_practitioner,
    create_user,
    get_token,
)

scenarios("../features/payments.feature")


@given("a patient", target_fixture="patient")
def get_patient(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


@given("a doctor", target_fixture="practitioner")
def get_doctor(client: Client) -> Practitioner:
    user = create_user()
    return create_practitioner(client, user, role_type="doctor")


@given("an appointment", target_fixture="appointment")
def book_appointment(client: Client, practitioner: Practitioner, patient: Patient):
    return create_appointment(client, practitioner, patient)


@given("an encounter", target_fixture="encounter")
def get_encounter(
    client: Client,
    practitioner: Practitioner,
    patient: Patient,
    appointment: Appointment,
) -> Encounter:
    return create_encounter(client, practitioner, patient, appointment)


@when("the payment is processed")
def process_payment(mocker, client: Client, account: Account):
    mock_payment_service = mocker.Mock()
    mocker.patch.object(
        mock_payment_service, "create_payment", return_value=(None, 123)
    )

    class Sample:
        data = json.dumps(
            {
                "customerId": "1",
                "paymentMethodId": "2",
                "amount": "10",
                "accountId": account["id"],
            }
        )

    sample = Sample()
    resp = PaymentsController(payment_service=mock_payment_service).create_payment(
        sample
    )
    assert resp.status_code == 201


@when("the payment is cancelled")
def payment_is_cancelled(
    client: Client, practitioner: Practitioner, encounter: Encounter
):
    token = get_token(practitioner.uid)
    account_id = encounter["account"][0]["reference"].split("/")[1]
    url = f"/accounts/{account_id}"
    resp = client.delete(url, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 204


@when("the charging is failed")
def fail_charge(mocker, client: Client, account: Account):
    mock_payment_service = mocker.Mock()
    mocker.patch.object(
        mock_payment_service, "create_payment", return_value=(Exception(), 123)
    )

    class Sample:
        data = json.dumps(
            {
                "customerId": "1",
                "paymentMethodId": "2",
                "amount": "10",
                "accountId": account["id"],
            }
        )

    sample = Sample()
    resp = PaymentsController(payment_service=mock_payment_service).create_payment(
        sample
    )
    assert resp.status_code == 500


@when(
    parsers.parse("account status is correctly set: {status}"), target_fixture="account"
)
@then(
    parsers.parse("account status is correctly set: {status}"), target_fixture="account"
)
def check_account_status(
    client: Client, practitioner: Practitioner, encounter: Encounter, status: str
) -> Account:
    token = get_token(practitioner.uid)
    account_id = encounter["account"][0]["reference"].split("/")[1]
    url = f"/accounts/{account_id}"
    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    output = json.loads(json.loads(resp.data)["data"])
    assert output["status"] == status
    return output


@then(parsers.parse("invoice status is correctly set: {all_or_any} {status}"))
def check_invoice_status(
    client: Client,
    practitioner: Practitioner,
    account: Account,
    all_or_any: str,
    status: str,
):
    token = get_token(practitioner.uid)
    url = f"/accounts/{account['id']}/invoices"
    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    output = json.loads(resp.data)["data"]
    status_list = []
    for invoice in output:
        status_list.append(json.loads(invoice)["status"] == status)
    if all_or_any == "all":
        assert all(status_list)
    if all_or_any == "any":
        assert any(status_list)


@then("payment is charged manually")
def charged_manually(client: Client, practitioner: Practitioner, account: Account):
    token = get_token(practitioner.uid)
    url = "/payments?manual=true"
    body = json.dumps(
        {
            "payment_intent_id": "2",
            "amount": "10",
            "accountId": account["id"],
        }
    )
    client.post(url, headers={"Authorization": f"Bearer {token}"}, data=body)
