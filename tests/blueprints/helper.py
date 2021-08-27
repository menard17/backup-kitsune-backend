from fhir.resources.domainresource import DomainResource


class FakeRequest:
    def __init__(self, data):
        self.data = data

    def get_json(self):
        return self.data


class MockResourceClient:
    def create_resource(self, data: DomainResource):
        data.id = "id1"
        return data
