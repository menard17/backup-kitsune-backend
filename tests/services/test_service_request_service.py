from fhir.resources import construct_fhir_element

from services.service_request_service import ServiceRequestService


def get_service_request(count):
    service_request = {
        "code": "Allplex SARS-CoV-2 Assay",
        "display": "PCR検査施行",
        "system": "ServiceRequest",
    }
    service_requests = []
    for _ in range(count):
        service_requests.append(service_request)

    print(service_requests)
    return {
        "code": {"coding": service_requests},
        "id": "id1",
        "intent": "order",
        "priority": "urgent",
        "resourceType": "ServiceRequest",
        "status": "completed",
        "subject": {"reference": "Patient/id2"},
    }


class MockServiceRequest:
    def __init__(self, count=2):
        self.appointment_dict = get_service_request(count)

    def get_resource(self):
        return construct_fhir_element("ServiceRequest", self.appointment_dict)


def test_get_service_requests():
    # Given
    expected = [
        {
            "value": "Allplex SARS-CoV-2 Assay",
            "display": "PCR検査施行",
            "verified": "false",
        }
    ]
    mock_resource_client = MockServiceRequest(count=2)
    mock_service_request = mock_resource_client.get_resource()

    # When
    actual = ServiceRequestService.get_service_request(mock_service_request)

    # Then
    assert actual[0] == expected[0]
    assert actual[1] == expected[0]


def test_get_medications_when_empty():
    # Given
    expected = []
    mock_resource_client = MockServiceRequest(count=0)
    mock_service_request = mock_resource_client.get_resource()

    # When
    actual = ServiceRequestService.get_service_request(mock_service_request)

    # Then
    assert actual == expected
