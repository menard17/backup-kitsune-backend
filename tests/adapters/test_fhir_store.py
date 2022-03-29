import pytest
from fhir.resources.bundle import Bundle
from fhir.resources.patient import Patient

from adapters.fhir_store import ResourceClient


def test_get_resource(mocker, session, url, test_patient_data):
    response = mocker.Mock()
    mocker.patch.object(response, "json", return_value=test_patient_data.json())
    mocker.patch.object(session, "get", return_value=response)
    resource_client = ResourceClient(session=session, url=url)

    result = resource_client.get_resource("resource-id", "Patient")

    assert result.resource_type == "Patient"
    assert result.id == "patient-id"
    session.get.assert_called_once_with(
        "testurl/Patient/resource-id",
        headers={"Content-Type": "application/fhir+json;charset=utf-8"},
    )
    response.raise_for_status.assert_called_once()


def test_get_resources(mocker, session, url, test_bundle_data):
    response = mocker.Mock()
    mocker.patch.object(response, "json", return_value=test_bundle_data.json())
    mocker.patch.object(session, "get", return_value=response)
    resource_client = ResourceClient(session=session, url=url)

    result = resource_client.get_resources("Patient")

    assert result.resource_type == "Bundle"
    assert result.id == "bundle-id"
    session.get.assert_called_once_with(
        "testurl/Patient",
        headers={"Content-Type": "application/fhir+json;charset=utf-8"},
    )
    response.raise_for_status.assert_called_once()


def test_search(mocker, session, url, test_bundle_data):
    response = mocker.Mock()
    mocker.patch.object(response, "json", return_value=test_bundle_data.json())
    mocker.patch.object(session, "get", return_value=response)
    resource_client = ResourceClient(session=session, url=url)

    result = resource_client.search("Patient", [("_id", "patient-id")])

    assert result.resource_type == "Bundle"
    assert result.id == "bundle-id"
    session.get.assert_called_once_with(
        "testurl/Patient?_id=patient-id&_count=300",
        headers={"Content-Type": "application/fhir+json;charset=utf-8"},
    )
    response.raise_for_status.assert_called_once()


def test_create_resource(mocker, session, url, test_patient_data):
    response = mocker.Mock()
    mocker.patch.object(response, "json", return_value=test_patient_data.json())
    mocker.patch.object(session, "post", return_value=response)
    patient_input = Patient()
    resource_client = ResourceClient(session=session, url=url)

    result = resource_client.create_resource(patient_input)

    assert result.resource_type == "Patient"
    assert result.id == "patient-id"
    session.post.assert_called_once_with(
        "testurl/Patient",
        headers={"Content-Type": "application/fhir+json;charset=utf-8"},
        data='{\n "resourceType": "Patient"\n}',
    )
    response.raise_for_status.assert_called_once()


def test_patch_resource(mocker, session, url, test_patient_data):
    response = mocker.Mock()
    mocker.patch.object(response, "json", return_value=test_patient_data.json())
    mocker.patch.object(session, "patch", return_value=response)
    resource_client = ResourceClient(session=session, url=url)

    result = resource_client.patch_resource(
        "patient-id",
        "Patient",
        [{"op": "add", "path": "/extension", "value": [], "resourceType": "Patient"}],
    )

    assert result.resource_type == "Patient"
    assert result.id == "patient-id"
    session.patch.assert_called_once_with(
        "testurl/Patient/patient-id",
        headers={"Content-Type": "application/json-patch+json"},
        data='[{"op": "add", "path": "/extension", "value": [], "resourceType": "Patient"}]',
    )
    response.raise_for_status.assert_called_once()


def test_put_resource(mocker, session, url, test_patient_data):
    response = mocker.Mock()
    mocker.patch.object(response, "json", return_value=test_patient_data.json())
    mocker.patch.object(session, "put", return_value=response)

    patient_input = Patient()
    resource_client = ResourceClient(session=session, url=url)

    result = resource_client.put_resource("patient-id", patient_input)

    assert result.resource_type == "Patient"
    assert result.id == "patient-id"
    session.put.assert_called_once_with(
        "testurl/Patient/patient-id",
        headers={"Content-Type": "application/fhir+json;charset=utf-8"},
        data='{\n "resourceType": "Patient"\n}',
    )
    response.raise_for_status.assert_called_once()


@pytest.fixture
def session(mocker):
    yield mocker.Mock()


@pytest.fixture
def url():
    yield "testurl"


@pytest.fixture
def test_patient_data():
    patient = Patient()
    patient.id = "patient-id"
    return patient


@pytest.fixture
def test_bundle_data():
    bundle = Bundle(type="document")
    bundle.id = "bundle-id"
    return bundle
