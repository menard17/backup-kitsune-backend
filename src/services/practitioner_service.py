from fhir.resources import construct_fhir_element

from adapters.fhir_store import ResourceClient


class PractitionerService:
    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def create_practitioner(self, identity, email, family_name, given_name, photo_url):
        practitioner_jsondict = {
            "resourceType": "Practitioner",
            "active": True,
            "name": [{"family": family_name, "given": [given_name]}],
            "telecom": [{"system": "email", "value": email, "use": "work"}],
        }

        practitioner = construct_fhir_element("Practitioner", practitioner_jsondict)
        practitioner = self.resource_client.get_post_bundle(practitioner, identity)
        return None, practitioner
