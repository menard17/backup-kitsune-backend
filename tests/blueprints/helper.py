from fhir.resources.domainresource import DomainResource


class FakeRequest:
    def __init__(self, data={}, args={}, claims=None):
        self.data = data
        self.claims = claims
        self.args = args

    def get_json(self):
        return self.data

    def args(self):
        return self.args


class MockResourceClient:
    def create_resource(self, data: DomainResource):
        data.id = "id1"
        return data
