from unittest.mock import patch

from helper import MockResourceClient

from blueprints.practitioners import PractitionerController

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
    request = FakeRequest(
        data=PRACTITIONER_DATA, claims={"uid": "test-uid", "email_verified": True}
    )
    mock_resource = MockResourceClient()

    with patch("blueprints.practitioners.role_auth") as mock_role_auth:
        controller = PractitionerController(mock_resource)

        practitioner = controller.create_practitioner(request)

        assert practitioner.id == "id1"
        mock_role_auth.grant_role.assert_called_once_with(
            {"uid": "test-uid", "email_verified": True}, "Practitioner", "id1"
        )


class FakeRequest:
    def __init__(self, data={}, args={}, claims=None):
        self.data = data
        self.claims = claims
        self.args = args

    def get_json(self):
        return self.data

    def args(self):
        return self.args
