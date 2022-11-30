import json

from fhir.resources import construct_fhir_element
from fhir.resources.domainresource import DomainResource

from services.patient_service import PatientService, remove_empty_string_from_address


class MockPatientClient:
    def __init__(
        self,
        mocker=None,
        email=None,
        second_email=None,
        customer_id=None,
        payment_id=None,
        address=None,
        zip=None,
        phone=None,
        kana=None,
    ):
        self.data = {
            "resourceType": "Patient",
            "id": "example",
            "active": True,
            "name": [
                {"use": "official", "family": "Chalmers", "given": ["Peter", "James"]}
            ],
            "gender": "male",
            "birthDate": "1990-01-01",
        }

        if email:
            self.data["telecom"] = [
                {"system": "email", "use": "home", "value": email},
            ]

        if second_email:
            # Insert old email at index 0 and index 2
            self.data["telecom"].insert(
                0, {"system": "email", "use": "old", "value": second_email}
            )
            self.data["telecom"].append(
                {"system": "email", "use": "old", "value": second_email}
            )

        if customer_id and payment_id:
            self.data["extension"] = []
            self.data["extension"].append(
                {"url": "stripe-customer-id", "valueString": customer_id}
            )
            self.data["extension"].append(
                {"url": "stripe-payment-method-id", "valueString": payment_id}
            )

        if address:
            self.data["address"] = [
                {
                    "city": address[1],
                    "country": "JP",
                    "line": [address[2], address[3]],
                    "postalCode": "1000000",
                    "state": address[0],
                    "type": "both",
                    "use": "home",
                }
            ]

        if zip:
            self.data["address"] = [{"postalCode": zip}]

        if phone:
            self.data["telecom"] = [
                {
                    "extension": [{"url": "verified", "valueString": "true"}],
                    "system": "phone",
                    "use": phone[0],
                    "value": phone[1],
                },
                {
                    "extension": [{"url": "verified", "valueString": "true"}],
                    "system": "email",
                    "use": "old",
                    "value": "abc@umed.com",
                },
            ]

        if kana:
            self.data["name"].append(
                {
                    "extension": [
                        {
                            "url": "http://hl7.org/fhir/StructureDefinition/iso21090-EN-representation",
                            "valueString": "SYL",
                        }
                    ],
                    "family": kana[0],
                    "given": [kana[1]],
                }
            )
        self.mocker = mocker

    def get_resource(self, id: str, resource_type: str) -> DomainResource:
        return construct_fhir_element(resource_type, json.dumps(self.data))


def test_get_patient_email_normal():
    # Given
    expected_email = "example@umed.jp"
    mock_resource_client = MockPatientClient(email=expected_email)
    patient_service = PatientService(mock_resource_client)

    # When
    _, actual_email = patient_service.get_patient_email("1")

    # Then
    assert expected_email == actual_email


def test_get_patient_email_not_exist():
    # Given
    mock_resource_client = MockPatientClient()
    patient_service = PatientService(mock_resource_client)

    # When
    _, actual_email = patient_service.get_patient_email("1")

    # Then
    assert not actual_email


def test_get_patient_name_normal():
    # Given
    expected_name = {
        "use": "official",
        "family": "Chalmers",
        "given": ["Peter", "James"],
    }
    mock_resource_client = MockPatientClient()
    patient_service = PatientService(mock_resource_client)

    # When
    _, actual_name = patient_service.get_patient_name("1")

    # Then
    assert expected_name == actual_name


def test_remove_empty_string_from_address_contains_empty_string():
    # Given
    addresses = [{"line": ["", "line2"], "country": "JP"}]
    expected_output = [{"line": ["line2"], "country": "JP"}]

    # When
    actual_addresses = remove_empty_string_from_address(addresses)

    # Then
    assert expected_output == actual_addresses

    # Check if original address list is not modified
    assert addresses == [{"line": ["", "line2"], "country": "JP"}]


def test_remove_empty_string_from_address_contains_without_empty_string():
    # Given
    addresses = [{"line": ["abc", "def"]}]
    expected_output = [{"line": ["abc", "def"]}]

    # When
    actual_addresses = remove_empty_string_from_address(addresses)

    # Then
    assert expected_output == actual_addresses


def test_remove_empty_string_from_address_contains_with_no_item():
    # Given
    addresses = [{"line": []}]
    expected_output = [{"line": []}]

    # When
    actual_addresses = remove_empty_string_from_address(addresses)

    # Then
    assert expected_output == actual_addresses


def test_check_link_success():
    valid_link = "https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/Patient/?_count=1&_page_token=Cjj3YqaT4f%2F%2F%2F%2F%2BABeFKRf0xQQD%2FAf%2F%2BNTk0ZjgxODM1MjM2ZGM1M2IyZTMwNTUxNTUwMWFjODQAARABIZRNcFwxQ70GOQAAAAAebFmdSAFQAFoLCSzWOfWKBujqEANgxd%2BBywc%3D"  # noqa: E501
    service = PatientService(None)

    ok, err_resp = service.check_link(valid_link)

    assert ok
    assert err_resp is None


def test_check_link_return_false_when_not_link_for_patient():
    appointment_link = "https://my.fhir.link/Appointment?_count=1&actor=87c802f0-c486-438d-b2e9-e06543303b4c&date=ge2022-05-21&_page_token=Cjj3YokQdv%2F%2F%2F%2F%2BABd%2BH721RFgD%2FAf%2F%2BNWM4NDM2YmQ3ZWExOTZiYTE5NzAyMDQ4Njc4NjMyOWUAARABIZRNcFwxQ70GOQAAAACJ73adSAFQAFoLCbs%2BeLJbiDrKEANg2qiOZGgB"  # noqa: E501
    service = PatientService(None)

    ok, err_resp = service.check_link(appointment_link)

    assert not ok
    assert err_resp.status_code == 400
    assert err_resp.data == b"not link for patient"


def test_get_patient_multiple_emails():
    # Given
    new_email = "new@umed.jp"
    old_email = "old@umed.jp"
    mock_resource_client = MockPatientClient(email=new_email, second_email=old_email)
    patient_service = PatientService(mock_resource_client)

    # When
    _, actual_email = patient_service.get_patient_email("1")

    # Then
    assert new_email == actual_email


def test_get_patient_payment_details():
    # Given
    payment_id = "payment id"
    customer_id = "customer id"
    mock_resource_client = MockPatientClient(
        customer_id=customer_id, payment_id=payment_id
    )
    patient_service = PatientService(mock_resource_client)

    # When
    err, (
        expected_cusotmer_id,
        expected_payment_id,
    ) = patient_service.get_patient_payment_details("1")

    # Then
    assert expected_cusotmer_id == customer_id
    assert expected_payment_id == payment_id
    assert err is None


def test_get_patient_payment_error():
    # Given
    mock_resource_client = MockPatientClient()
    patient_service = PatientService(mock_resource_client)

    # When
    err, outputs = patient_service.get_patient_payment_details("1")

    # Then
    assert outputs is None
    assert err is not None


def test_get_kana_empty():
    # Given
    mock_resource_client = MockPatientClient()
    patient = construct_fhir_element("Patient", mock_resource_client.data)
    expected = ""

    # When
    actual = PatientService.get_kana(patient)

    # Then
    assert actual == expected


def test_get_kana():
    # Given
    first_name_kana = "タロウ"
    last_name_kana = "ヤマダ"
    mock_resource_client = MockPatientClient(kana=[last_name_kana, first_name_kana])
    patient = construct_fhir_element("Patient", mock_resource_client.data)
    expected = last_name_kana + " " + first_name_kana

    # When
    actual = PatientService.get_kana(patient)

    # Then
    assert actual == expected


def test_get_name():
    # Given
    mock_resource_client = MockPatientClient()
    patient = construct_fhir_element("Patient", mock_resource_client.data)

    # When
    actual = PatientService.get_name(patient)

    # Then
    assert actual == "Chalmers Peter James"


def test_get_address_when_empty():
    # Given
    mock_resource_client = MockPatientClient()
    patient = construct_fhir_element("Patient", mock_resource_client.data)
    expected = ""

    # When
    actual = PatientService.get_address(patient)

    # Then
    assert actual == expected


def test_get_address():
    # Given
    mock_resource_client = MockPatientClient(
        address=["Tokyo", "Shinagawa", "123", "23523"]
    )
    patient = construct_fhir_element("Patient", mock_resource_client.data)
    expected = "TokyoShinagawa123 23523"

    # When
    actual = PatientService.get_address(patient)

    # Then
    assert actual == expected


def test_get_zip_empty():
    # Given
    mock_resource_client = MockPatientClient()
    patient = construct_fhir_element("Patient", mock_resource_client.data)
    expected = ""

    # When
    actual = PatientService.get_zip(patient)

    # Then
    assert actual == expected


def test_get_zip():
    # Given
    expected = "123"
    mock_resource_client = MockPatientClient(zip=expected)
    patient = construct_fhir_element("Patient", mock_resource_client.data)

    # When
    actual = PatientService.get_zip(patient)

    # Then
    assert actual == expected


def test_get_phone_empty():
    # Given
    mock_resource_client = MockPatientClient()
    patient = construct_fhir_element("Patient", mock_resource_client.data)
    expected = ""

    # When
    actual = PatientService.get_phone(patient)

    # Then
    assert actual == expected


def test_get_no_mobile_phone():
    # Given
    mock_resource_client = MockPatientClient(phone=["home", "123"])
    patient = construct_fhir_element("Patient", mock_resource_client.data)
    expected = ""

    # When
    actual = PatientService.get_phone(patient)

    # Then
    assert actual == expected


def test_get_phone():
    # Given
    expected = "123"
    mock_resource_client = MockPatientClient(phone=["mobile", expected])
    patient = construct_fhir_element("Patient", mock_resource_client.data)

    # When
    actual = PatientService.get_phone(patient)

    # Then
    assert actual == expected
