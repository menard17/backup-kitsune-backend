from unittest.mock import Mock
from uuid import uuid4

from services.patient_call_logs_service import PatientCallLogsService


def test_upsert_call_docs():
    call_log_collection_mock = Mock()
    call_log_collection_mock.where = Mock(return_value=call_log_collection_mock)
    call_log_collection_mock.stream = Mock(return_value=[])

    firestore_client_mock = Mock()
    firestore_client_mock.get_collection = Mock(return_value=call_log_collection_mock)

    controller = PatientCallLogsService(firestore_client_mock)

    result = controller.upsert_call_docs(
        patient_id=str(uuid4()),
        appointment_id=str(uuid4()),
    )

    assert result == (None, "Successfully saved call logs.")
