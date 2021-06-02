from fhir import resources
from fhir.resources import organization
from fhir.resources.organization import Organization
from fhir.resources.address import Address
from fhir.resources.patient import Patient
import json


# Import google.auth for default credential
import google.auth

# Imports the google.auth.transport.requests transport
from google.auth.transport import requests

# Imports a module to allow authentication using a service account
from google.oauth2 import service_account


fhir_configuration = {
    "BASE_URL": "https://healthcare.googleapis.com/v1",
    "PROJECT": "kitsune-dev-313313",
    "LOCATION": "asia-northeast1",
    "DATASET": "phat-fhir-dataset-id",
    "FHIR_STORE": "phat-fhir-store-id",
}


class OrganizationClient:
    def __init__(self):
        url = "{}/projects/{}/locations/{}".format(
            fhir_configuration.get("BASE_URL"),
            fhir_configuration.get("PROJECT"),
            fhir_configuration.get("LOCATION"),
        )
        credentials, project_id = google.auth.default()
        scopeed = credentials.with_scopes(
            ["https://www.googleapis.com/auth/cloud-platform"]
        )
        self._session = requests.AuthorizedSession(scopeed)
        self._headers = {"Content-Type": "application/fhir+json;charset=utf-8"}
        self._resource_path = "{}/datasets/{}/fhirStores/{}/fhir/{}".format(
            url,
            fhir_configuration.get("DATASET"),
            fhir_configuration.get("FHIR_STORE"),
            "Organization",
        )

    def add_organization(self, name):
        organization = create_organization(name)
        response = self._session.get(self._resource_path, headers=self._headers)
        resource = response.json()
        print(resource)
        return resource


def create_organization(name: str) -> dict:
    org = Organization.construct()
    org.active = True
    org.name = name
    org.address = list()
    address = Address.construct()
    address.country = "Japan"
    org.address.append(address)
    return org.dict()


if __name__ == "__main__":
    client = OrganizationClient()
    client.add_organization("UMed Inc.")
