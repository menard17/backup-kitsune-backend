import json

from firebase_admin import auth
from pytest_bdd import given, parsers, scenarios, then, when

from blueprints.payments import PaymentsController
from integtest.characters import (
    Account,
    Appointment,
    Encounter,
    Invoice,
    Patient,
    Practitioner,
)
from integtest.conftest import Client
from integtest.utils import (
    create_appointment,
    create_encounter,
    create_patient,
    create_practitioner,
    create_user,
    get_token,
)

scenarios("../features/accounts.feature")


@given("a patient", target_fixture="patient")
def get_patient(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


@given("a doctor", target_fixture="practitioner")
def get_doctor(client: Client) -> Practitioner:
    user = create_user()
    return create_practitioner(client, user, role_type="doctor")


@given("a back-office staff", target_fixture="staff")
def get_staff(client: Client) -> Practitioner:
    user = create_user()

    # Assign required role for staff
    firebase_user = auth.get_user_by_email(user.email)
    custom_claims = firebase_user.custom_claims or {}
    current_roles = custom_claims.get("roles", {})
    current_roles["Staff"] = {}
    auth.set_custom_user_claims(user.uid, {"roles": current_roles})

    return create_practitioner(client, user, role_type="staff")


@given("an appointment", target_fixture="appointment")
def book_appointment(
    client: Client, practitioner: Practitioner, patient: Patient
) -> Appointment:
    return create_appointment(client, practitioner, patient)


@given("an encounter", target_fixture="encounter")
def get_encounter(
    client: Client,
    practitioner: Practitioner,
    patient: Patient,
    appointment: Appointment,
) -> Encounter:
    return create_encounter(client, practitioner, patient, appointment)


@when("the payment is cancelled")
def payment_is_cancelled(client: Client, staff: Practitioner, encounter: Encounter):
    token = get_token(staff.uid)
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


@then(parsers.parse("invoice status is correctly set: {status}"))
def check_invoice_status(
    client: Client, practitioner: Practitioner, invoice: Invoice, status: str
):
    token = get_token(practitioner.uid)
    invoice_id = invoice["id"]
    url = f"/invoices/{invoice_id}"
    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = json.loads(resp.data)["data"]
    assert json.loads(data)["status"] == status
