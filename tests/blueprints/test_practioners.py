from blueprints.practitioners import PractitionerController
from helper import MockResourceClient


PRACTITIONER_DATA = {
    "resourceType": "Practitioner",
    "gender": "male",
    "birthDate": "1971-11-01",
    "active": "true",
    "name": [
        {
            "family": "水田",
            "given": ["万理"],
            "extension": [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/iso21090-EN-representation",
                    "valueCode": "IDE",
                }
            ],
        },
        {
            "family": "みずた",
            "given": ["まり"],
            "extension": [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/iso21090-EN-representation",
                    "valueCode": "SYL",
                }
            ],
        },
        {
            "family": "Mizuta",
            "given": ["Mari"],
            "extension": [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/iso21090-EN-representation",
                    "valueCode": "ABC",
                }
            ],
        },
    ],
}


def test_create_practioner(mocker):
    mock_auth = mocker.Mock()
    mock_resource = MockResourceClient()
    practitioner = PractitionerController(mock_resource, mock_auth).create_practitioner(
        "firebaseid", PRACTITIONER_DATA
    )

    assert practitioner.id == "id1"
