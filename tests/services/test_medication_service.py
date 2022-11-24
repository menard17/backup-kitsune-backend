from fhir.resources import construct_fhir_element

from services.medication_request_service import MedicationRequestService


def get_medication_request(count):
    medication = {"code": "Loxonin tablet", "display": "ロキソニン&セルベックス錠剤"}
    medications = []
    for _ in range(count):
        medications.append(medication)

    return {
        "id": "id1",
        "intent": "order",
        "medicationCodeableConcept": {
            "coding": medications,
        },
        "priority": "urgent",
        "resourceType": "MedicationRequest",
        "status": "completed",
        "subject": {"reference": "Patient/patientid"},
    }


class MockMedicationRequest:
    def __init__(self, count=2):
        self.medication_request = get_medication_request(count=count)

    def get_resource(self):
        return construct_fhir_element("MedicationRequest", self.medication_request)


def test_get_medications():
    # Given
    expected = [
        {"value": "Loxonin tablet", "display": "ロキソニン&セルベックス錠剤", "verified": "false"}
    ]
    mock_resource_client = MockMedicationRequest(count=2)
    mock_medication_request = mock_resource_client.get_resource()

    # When
    actual = MedicationRequestService.get_medications(mock_medication_request)

    # Then
    assert actual[0] == expected[0]
    assert actual[1] == expected[0]


def test_get_medications_when_empty():
    # Given
    expected = []
    mock_resource_client = MockMedicationRequest(count=0)
    mock_medication_request = mock_resource_client.get_resource()

    # When
    actual = MedicationRequestService.get_medications(mock_medication_request)

    # Then
    assert actual == expected
