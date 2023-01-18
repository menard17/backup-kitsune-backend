import json
import threading
from datetime import datetime, timedelta

import pytz
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

scenarios("../features/lineup.feature")

CONCURRENT_PATIENT_NUM = 5


@given("an admin", target_fixture="admin")
def get_admin() -> User:
    user = create_user()
    return make_admin(user)


@given("a patient", target_fixture="patient")
def get_patient(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


@given("a doctor", target_fixture="doctor")
def get_doctor(client: Client) -> Practitioner:
    user = create_user()
    jst = pytz.timezone("Asia/Tokyo")
    now = datetime.now().astimezone(jst)
    base_time = now.time().isoformat()
    current_time_plus_ten_mins = (now + timedelta(minutes=10)).time().isoformat()
    return create_practitioner(
        client,
        user,
        role_type="doctor",
        visit_type="walk-in",
        available_time=[
            {
                "daysOfWeek": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
                "availableStartTime": base_time,
                "availableEndTime": current_time_plus_ten_mins,
            },
        ],
    )


@given("a doctor B", target_fixture="doctor_b")
def get_doctor_b(client: Client) -> Practitioner:
    user = create_user()
    jst = pytz.timezone("Asia/Tokyo")
    now = datetime.now().astimezone(jst)
    base_time = now.time().isoformat()
    current_time_plus_ten_mins = (now + timedelta(minutes=10)).time().isoformat()
    return create_practitioner(
        client,
        user,
        role_type="doctor",
        visit_type="walk-in",
        available_time=[
            {
                "daysOfWeek": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
                "availableStartTime": base_time,
                "availableEndTime": current_time_plus_ten_mins,
            },
        ],
    )


@given("a patient B", target_fixture="patient_b")
def get_patient_b(client: Client) -> Patient:
    user = create_user()
    return create_patient(client, user)


@when("the admin creates a list", target_fixture="fhir_list")
def admin_create_a_list(client: Client, admin: User) -> dict:
    token = get_token(admin.uid)
    resp = client.post(
        "/lists",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 201

    fhir_list = json.loads(resp.data)
    assert fhir_list["mode"] == "working"
    assert fhir_list["status"] == "current"
    assert fhir_list["title"] == "Patient Queue"
    return fhir_list


@then("the doctor can see all lists")
def doctor_can_see_all_lists(client: Client, doctor: Practitioner):
    token = get_token(doctor.uid)
    resp = client.get(
        "/lists",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    resp_lists = json.loads(resp.data)["data"]

    # the integration reuses the same FHIR. So there will be multiple lists in test env.
    assert len(resp_lists) > 0


@then("the doctor can see the list")
def doctor_can_see_the_list(client: Client, doctor: Practitioner, fhir_list: dict):
    token = get_token(doctor.uid)
    resp = client.get(
        f"/lists/{fhir_list['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    resp_list = json.loads(resp.data)["data"]
    assert resp_list["id"] == fhir_list["id"]


@then("the patient cannot see all lists")
def patient_cannot_see_all_lists(client: Client, patient: Patient):
    token = get_token(patient.uid)
    resp = client.get(
        "/lists",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 401


@then("the patient cannot see the list")
def patient_cannot_see_the_list(client: Client, patient: Patient, fhir_list: dict):
    token = get_token(patient.uid)
    resp = client.get(
        f"/lists/{fhir_list['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 401


@then(parsers.parse("the patient can see the number of item in the list: {count}"))
def patient_can_see_length_of_list(
    client: Client, patient: Patient, fhir_list: dict, count: str
):
    token = get_token(patient.uid)
    resp = client.get(
        f"/lists/{fhir_list['id']}/counts",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    resp = json.loads(resp.data)["data"]
    assert resp == int(count)


@then(parsers.parse("the patient can see the position of item in the list: {count}"))
def patient_can_see_the_position_of_list(
    client: Client, patient: Patient, fhir_list: dict, count: str
):
    token = get_token(patient.uid)
    resp = client.get(
        f"/lists/{fhir_list['id']}/patients/{patient.fhir_data['id']}/counts",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    resp = json.loads(resp.data)["data"]
    assert resp == {"position": int(count)}


@then(parsers.parse("the patientB can see the position of item in the list: {count}"))
def patientB_can_see_the_position_of_list(
    client: Client, patient_b: Patient, fhir_list: dict, count: str
):
    token = get_token(patient_b.uid)
    resp = client.get(
        f"/lists/{fhir_list['id']}/patients/{patient_b.fhir_data['id']}/counts",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    resp = json.loads(resp.data)["data"]
    assert resp == {"position": int(count)}


@then("the patient can join the lineup", target_fixture="fhir_list")
def patient_join_the_lineup(client: Client, patient: Patient, fhir_list: dict) -> dict:
    token = get_token(patient.uid)
    patient_id = patient.fhir_data["id"]
    resp = client.post(
        f"/lists/{fhir_list['id']}/items/{patient_id}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 201

    fhir_list = json.loads(resp.data)["data"]
    assert len(fhir_list["entry"]) == 1
    assert fhir_list["entry"][0]["item"]["reference"] == f"Patient/{patient_id}"
    return fhir_list


@then("the patientB can also join the lineup", target_fixture="fhir_list")
def patient_b_also_join_the_lineup(
    client: Client, patient_b: Patient, fhir_list: dict
) -> dict:
    token = get_token(patient_b.uid)
    patient_id = patient_b.fhir_data["id"]
    resp = client.post(
        f"/lists/{fhir_list['id']}/items/{patient_id}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 201

    fhir_list = json.loads(resp.data)["data"]
    assert len(fhir_list["entry"]) == 2
    assert fhir_list["entry"][1]["item"]["reference"] == f"Patient/{patient_id}"
    return fhir_list


@then("the patient can remove from the lineup", target_fixture="fhir_list")
def patient_remove_from_the_lineup(
    client: Client, patient: Patient, fhir_list: dict
) -> dict:
    token = get_token(patient.uid)
    patient_id = patient.fhir_data["id"]
    resp = client.delete(
        f"/lists/{fhir_list['id']}/items/{patient_id}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200

    old_entry_len = len(fhir_list["entry"])
    fhir_list = json.loads(resp.data)["data"]
    assert len(fhir_list["entry"]) == old_entry_len - 1
    for e in fhir_list["entry"]:
        e["item"]["reference"] != f"Patient/{patient_id}"
    return fhir_list


@when("multiple patients trying to join the lineup at the same time")
def multiple_patients_lining_up(
    client: Client,
    fhir_list: dict,
):
    # create multiple patients
    patients = []
    for _ in range(CONCURRENT_PATIENT_NUM):
        user = create_user()
        patients.append(create_patient(client, user))

    # the thread function and thread results
    results = [0] * CONCURRENT_PATIENT_NUM

    def patient_join(token, patient_id, result_idx):
        resp = client.post(
            f"/lists/{fhir_list['id']}/items/{patient_id}",
            headers={"Authorization": f"Bearer {token}"},
            content_type="application/json",
        )
        results[result_idx] = resp.status_code

    threads = []
    for idx, patient in enumerate(patients):
        token = get_token(patient.uid)
        patient_id = patient.fhir_data["id"]
        th = threading.Thread(target=patient_join, args=(token, patient_id, idx))
        threads.append(th)

    # all patients joining the list in the same time
    for th in threads:
        th.start()

    # wait the thread finishes
    for th in threads:
        th.join()

    # assert that some succeed and some failed
    # the reason not checking only one will succeed is to avoid flaky tests.
    # despite using the thread, the server might still not receive those request at the same time
    assert 201 in results
    assert 503 in results


@then("not all can successfully join")
def not_all_can_successfully_join(client: Client, admin: User, fhir_list: dict):
    token = get_token(admin.uid)
    resp = client.get(
        f"/lists/{fhir_list['id']}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    resp_list = json.loads(resp.data)["data"]
    assert resp_list["id"] == fhir_list["id"]
    assert len(resp_list["entry"]) < CONCURRENT_PATIENT_NUM


@then(parsers.parse("the correct available spot counts can be fetched: {count}"))
def get_spot_counts(client: Client, admin: User, fhir_list: dict, count: str):
    token = get_token(admin.uid)
    resp = client.get(
        f"/lists/{fhir_list['id']}/appointments",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    result = json.loads(resp.data)
    assert result["available_spot"] == int(count)
    assert resp.status_code == 200


@then("inactivate doctor")
def inactive_doctor(client: Client, doctor: Practitioner):
    token = get_token(doctor.uid)
    role_id = doctor.fhir_data["id"]
    resp = client.patch(
        f"/practitioner_roles/{role_id}?active=false",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


@then("inactivate doctor b")
def inactive_doctor_b(client: Client, doctor_b: Practitioner):
    token = get_token(doctor_b.uid)
    role_id = doctor_b.fhir_data["id"]
    resp = client.patch(
        f"/practitioner_roles/{role_id}?active=false",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


@then(
    "the patient cannot see the number of item in the list if wrong id of list is used"
)
def patient_cannot_see_the_numer_of_item(client: Client, patient: Patient):
    wrong_list_id = "wrong_id"
    token = get_token(patient.uid)
    resp = client.get(
        f"/lists/{wrong_list_id}/counts",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 500


@then(
    "the patient cannot see the position of item in the list if wrong id of list is used"
)
def patient_cannot_see_the_position_of_list(client: Client, patient: Patient):
    wrong_list_id = "wrong_id"
    token = get_token(patient.uid)
    resp = client.get(
        f"/lists/{wrong_list_id}/patients/{patient.fhir_data['id']}/counts",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert resp.status_code == 500
