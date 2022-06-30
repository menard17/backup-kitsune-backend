import json
from urllib.parse import urlencode

from pytest_bdd import given, scenarios, then, when

from integtest.characters import Patient, Practitioner
from integtest.conftest import Client
from integtest.utils import create_patient, create_practitioner, create_user, get_token

scenarios("../features/get_patients.feature")


@given("a doctor", target_fixture="doctor")
def create_doctor(client: Client) -> Practitioner:
    user = create_user()
    return create_practitioner(client, user)


@given("multiple patients")
def create_multiple_patients(client: Client) -> list[Patient]:
    # creates a few patients to ensure the pagination would work even with a clean patient set.
    # note that the integration tests will reuse the patients set without clean-up
    # so usually there will already be several patients already.
    patients = []
    for _ in range(2):
        user = create_user()
        patients.append(create_patient(client, user))
    return patients


@when("the doctor calls get_patients endpoint", target_fixture="patients_resp")
def doctor_calls_get_patients(client: Client, doctor: Practitioner) -> dict:
    token = get_token(doctor.uid)
    patient_resp = client.get(
        "/patients?count=1",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert patient_resp.status_code == 200
    return json.loads(patient_resp.data)["data"]


@then("return the first page of patients", target_fixture="next_link")
def return_the_first_page_of_patient(patients_resp: dict) -> str:
    assert len(patients_resp["entry"]) == 1, "not matching count size"
    for link in patients_resp["link"]:
        if link["relation"] == "next":
            return link["url"]

    assert False, "should have next link"


@when(
    "the doctor gets the next page of the patients",
    target_fixture="patients_page_2_resp",
)
def doctor_get_the_next_page_of_the_patients(
    client: Client, doctor: Practitioner, next_link: str
) -> dict:
    token = get_token(doctor.uid)
    patient_resp = client.get(
        f"/patients?{urlencode({'next_link': next_link})}",
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert patient_resp.status_code == 200
    return json.loads(patient_resp.data)["data"]


@then("return the next page of patients", target_fixture="next_link")
def return_the_next_page_of_patients(patients_page_2_resp: dict):
    assert len(patients_page_2_resp["entry"]) == 1, "not matching count size"
    for link in patients_page_2_resp["link"]:
        if link["relation"] == "next":
            return link["url"]

    assert False, "should have next link"
