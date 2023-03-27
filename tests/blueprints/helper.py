import json

from fhir.resources import construct_fhir_element
from fhir.resources.domainresource import DomainResource

TEST_PRACTITIONER_ID = "dummy-practitioner-id"
TEST_PRACTITIONER_ROLE_ID = "dummy-role-id"
TEST_SCHEDULE_ID = "dummy-schedule-id"

PRACTITIONER_DATA = {
    "resourceType": "Practitioner",
    "active": True,
    "name": [{"family": "Test", "given": ["Cool"], "prefix": ["Dr"]}],
}

PRACTITIONER_ROLE_DATA = {
    "resourceType": "PractitionerRole",
    "id": TEST_PRACTITIONER_ROLE_ID,
    "active": True,
    "period": {"start": "2012-01-01", "end": "2012-03-31"},
    "practitioner": {
        "reference": f"Practitioner/{TEST_PRACTITIONER_ID}",
        "display": "Dr Adam Careful",
    },
    "availableTime": [
        {
            "daysOfWeek": ["mon", "tue", "wed"],
            "availableStartTime": "09:00:00",
            "availableEndTime": "16:30:00",
        },
        {
            "daysOfWeek": ["thu", "fri"],
            "availableStartTime": "09:00:00",
            "availableEndTime": "12:00:00",
        },
    ],
}


SCHEDULE_DATA = {
    "resourceType": "Schedule",
    "id": TEST_SCHEDULE_ID,
    "active": True,
    "actor": [
        {
            "reference": "PractitionerRole/" + TEST_PRACTITIONER_ROLE_ID,
            "display": "PractitionerRole: " + TEST_PRACTITIONER_ROLE_ID,
        }
    ],
    "planningHorizon": {
        "start": PRACTITIONER_ROLE_DATA["period"]["start"],
        "end": PRACTITIONER_ROLE_DATA["period"]["end"],
    },
    "comment": "auto generated schedule on practitioner role creation",
}

SCHEDULE_SEARCH_DATA = {
    "entry": [
        {
            "fullUrl": "https://dummy-search-url",
            "resource": SCHEDULE_DATA,
            "search": {"mode": "match"},
        }
    ],
    "link": [],
    "total": 1,
    "type": "searchset",
    "resourceType": "Bundle",
}


class FakeRequest:
    def __init__(self, data={}, args={}, claims=None):
        self.data = data
        self.claims = claims
        self.args = args

    def get_json(self):
        return self.data

    def args(self):
        return self.args

    @property
    def json(self):
        return json.loads(self.data) if self.data else None


class FakeAppointment:
    def __init__(self, status):
        self.status = status


class MockResourceClient:
    def create_resource(self, data: DomainResource):
        data.id = "id1"
        return data

    def get_resource(self, id, resource):
        if resource == "Practitioner":
            return construct_fhir_element(resource, PRACTITIONER_DATA)
        if resource == "PractitionerRole":
            return construct_fhir_element(resource, PRACTITIONER_ROLE_DATA)
        return ""

    def search(self, param1, search):
        class result:
            entry = None

        return result
