import json

from firebase_admin import auth
from pytest_bdd import given, parsers, scenarios, then, when

from integtest.characters import Patient, Practitioner, User
from integtest.conftest import Client
from integtest.utils import (
    create_patient,
    create_practitioner,
    create_user,
    get_token,
    make_admin,
)

scenarios("../features/prequestionnaire.feature")


@given("an admin", target_fixture="admin")
def get_admin() -> User:
    user = create_user()
    return make_admin(user)


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


@given("a doctor", target_fixture="practitioner")
def get_doctor(client: Client) -> Practitioner:
    user = create_user()
    return create_practitioner(client, user, role_type="doctor")


@given("a patient", target_fixture="patient")
def get_patient(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


@when(
    parsers.parse("the admin creates a prequestionnaire"),
    target_fixture="fhir_questionnaire",
)
def create_prequestionnaire(client: Client, admin: User):
    token = get_token(admin.uid)
    resp = client.post(
        "/prequestionnaire",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 201

    fhir_questionnaire = json.loads(resp.data)
    assert fhir_questionnaire["status"] == "active"
    return fhir_questionnaire


@then("the back-office staff can see all prequestionnaires")
def staff_can_see_prequestionnaires(
    client: Client, staff: Practitioner, fhir_questionnaire: dict
):
    token = get_token(staff.uid)
    resp = client.get(
        f"/prequestionnaire/{fhir_questionnaire['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    resp_list = json.loads(resp.data)
    assert resp_list["id"] == fhir_questionnaire["id"]


@then("the doctor can see the prequestionnaire")
def doctor_can_see_prequestionnaire(
    client: Client, practitioner: Practitioner, fhir_questionnaire: dict
):
    token = get_token(practitioner.uid)
    resp = client.get(
        f"/prequestionnaire/{fhir_questionnaire['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    resp_list = json.loads(resp.data)
    assert resp_list["id"] == fhir_questionnaire["id"]


@then("the patient can see all prequestionnaires")
def patient_can_see_all_lists(
    client: Client, patient: Patient, fhir_questionnaire: dict
):
    token = get_token(patient.uid)
    resp = client.get(
        f"/prequestionnaire/{fhir_questionnaire['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200


@then(
    "the back-office staff can add new prequestionnaire question",
    target_fixture="item_question",
)
def staff_can_add_question(
    client: Client, staff: Practitioner, fhir_questionnaire: dict
):
    token = get_token(staff.uid)

    data = {"type": "string", "text": "example"}

    resp = client.post(
        f"/prequestionnaire/{fhir_questionnaire['id']}/items",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
        data=json.dumps(data),
    )
    fhir_questionnaire = json.loads(resp.data)
    assert resp.status_code == 201
    assert fhir_questionnaire["item"][0]["text"] == "example"
    return fhir_questionnaire["item"][0]


@then("the back-office staff can update a question in the prequestionnaire")
def staff_can_updated_question(
    client: Client, staff: Practitioner, fhir_questionnaire: dict, item_question: dict
):
    token = get_token(staff.uid)

    data = {"type": "string", "text": "updated example"}
    resp = client.patch(
        f"/prequestionnaire/{fhir_questionnaire['id']}/items/{item_question['linkId']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
        data=json.dumps(data),
    )
    fhir_questionnaire = json.loads(resp.data)
    assert resp.status_code == 201
    assert fhir_questionnaire["item"][0]["text"] == "updated example"


@then(
    parsers.parse(
        "the back-office staff can remove from a question in the prequestionnaire"
    )
)
def staff_can_remove_question(
    client: Client, staff: Practitioner, fhir_questionnaire: dict, item_question: dict
):
    token = get_token(staff.uid)
    resp = client.delete(
        f"/prequestionnaire/{fhir_questionnaire['id']}/items/{item_question['linkId']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    fhir_questionnaire = json.loads(resp.data)
    assert resp.status_code == 200
    assert "item" not in fhir_questionnaire


@then(
    "the patient cannot add new prequestionnaire question",
    target_fixture="item_question",
)
def staff_cannot_add_question(
    client: Client, patient: Patient, fhir_questionnaire: dict
):
    token = get_token(patient.uid)

    data = {"type": "string", "text": "example"}

    resp = client.post(
        f"/prequestionnaire/{fhir_questionnaire['id']}/items",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
        data=json.dumps(data),
    )

    assert resp.status_code == 401


@then("the patient cannot update a question in the prequestionnaire")
def staff_cannot_updated_question(
    client: Client, patient: Patient, fhir_questionnaire: dict
):
    token = get_token(patient.uid)

    data = {"type": "string", "text": "updated example"}
    resp = client.patch(
        f"/prequestionnaire/{fhir_questionnaire['id']}/items/c0da4dd6-3c5c-432a-8cb6-791a3a132697",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
        data=json.dumps(data),
    )
    assert resp.status_code == 401


@then(
    parsers.parse("the patient cannot remove from a question in the prequestionnaire")
)
def staff_cannot_remove_question(
    client: Client, patient: Patient, fhir_questionnaire: dict
):
    token = get_token(patient.uid)
    resp = client.delete(
        f"/prequestionnaire/{fhir_questionnaire['id']}/items/c0da4dd6-3c5c-432a-8cb6-791a3a132697",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 401
