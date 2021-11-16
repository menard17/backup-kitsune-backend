"""
pytest would share the fixtures automatically from conftest.py
"""
from typing import Protocol

import pytest
from firebase_admin import auth
from flask.testing import FlaskClient

from adapters.fhir_store import ResourceClient
from app import app


class Client(Protocol):
    def __call__(self) -> FlaskClient:
        ...


@pytest.fixture
def client() -> Client:
    return app.test_client()


def pytest_bdd_after_scenario(request, feature, scenario):
    fixtures = [
        Fixture("Encounter"),
        Fixture("DiagnosticReport", "diagnostic_report"),
        Fixture("ServiceRequest", "service_request"),
        Fixture("Appointment"),
        Fixture("Appointment", "nurse_appointment"),
        Fixture("Appointment", "appointment_yesterday"),
        Fixture("Patient"),
        Fixture("Practitioner"),
        Fixture("Practitioner", "doctor"),
        Fixture("Practitioner", "nurse"),
        Fixture("Patient", "patientA"),
        Fixture("Patient", "patientB"),
        Fixture("DocumentReference", "document_reference"),
    ]

    requests = []
    for fixture in fixtures:
        if fixture.fixture_name in request.fixturenames:
            resource = request.getfixturevalue(fixture.fixture_name)
            if fixture.resource_type == "Patient":
                requests.extend(_tear_down_patient(resource))
            elif fixture.resource_type == "Practitioner":
                requests.extend(_tear_down_practitioner(resource))
            else:
                requests.append(
                    _construct_delete_request(fixture.resource_type, resource["id"])
                )
    ResourceClient().delete_resources(requests)


class Fixture:
    def __init__(self, resource_type: str, fixture_name: str = None):
        self.resource_type = resource_type
        self.fixture_name = fixture_name
        if not (self.fixture_name):
            self.fixture_name = self._resource_type_in_camel()

    def _resource_type_in_camel(self):
        return self.resource_type[0].lower() + self.resource_type[1:]


def _tear_down_patient(patient_resource) -> list:
    patient_id = patient_resource.fhir_data["id"]
    firebase_id = patient_resource.uid
    auth.delete_user(firebase_id)
    request = _construct_delete_request("Patient", patient_id)
    return [request]


def _tear_down_practitioner(practitioner_resource) -> list:
    results = []
    if practioner_schedule := practitioner_resource.fhir_schedule:
        slot = ResourceClient().search(
            "Slot", [("schedule", practioner_schedule["id"])]
        )
        if (entry := slot.entry) is not None:
            results.append(_construct_delete_request("Slot", entry[0].resource.id))
        results.append(_construct_delete_request("Schedule", practioner_schedule["id"]))
    if practitioner_role := practitioner_resource.fhir_data:
        results.append(
            _construct_delete_request("PractitionerRole", practitioner_role["id"])
        )
    if practioner := practitioner_resource.fhir_practitioner_data:
        results.append(_construct_delete_request("Practitioner", practioner["id"]))
    firebase_id = practitioner_resource.uid
    auth.delete_user(firebase_id)
    return results


def _construct_delete_request(resource_type, resource_id) -> dict:
    return {"request": {"method": "DELETE", "url": f"{resource_type}/{resource_id}"}}
