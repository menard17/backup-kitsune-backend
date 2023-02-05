import uuid
from unittest.mock import Mock

from fhir.resources.patient import Patient
from helper import MockResourceClient

from blueprints.calls import CallsController

PATIENT_DATA = {
    "resourceType": "Patient",
    "id": "example",
    "active": True,
    "name": [{"use": "official", "family": "Chalmers", "given": ["Peter", "James"]}],
    "gender": "male",
    "birthDate": "1990-01-01",
    "extension": [
        {"url": "voip-token", "valueString": "sample voip token"},
    ],
}


def test_upsert_call_docs():
    call_log_collection_mock = Mock()
    call_log_collection_mock.where = Mock(return_value=call_log_collection_mock)
    call_log_collection_mock.stream = Mock(return_value=[])

    firestore_client_mock = Mock()
    firestore_client_mock.get_collection = Mock(return_value=call_log_collection_mock)

    def mock_get_resource(id, resource_type):
        return Patient.parse_obj(PATIENT_DATA)

    resource_client = MockResourceClient()
    resource_client.get_resource = mock_get_resource

    controller = CallsController(resource_client, Mock(), firestore_client_mock)

    result = controller.upsert_call_docs(
        patient_id=PATIENT_DATA["id"],
        appointment_id=str(uuid.uuid4()),
    )

    assert result == (None, "Successfully saved call logs.")
