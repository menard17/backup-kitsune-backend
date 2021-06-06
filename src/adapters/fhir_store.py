from fhir.resources import construct_fhir_element
from fhir.resources.fhirabstractmodel import FHIRAbstractModel
import google.auth
from google.auth.transport import requests
from fhir.resources.domainresource import DomainResource

# This configuration is only for testing purpose only. Should be separated to
# different configuration for dev/test/prod in the future.
fhir_configuration = {
    "BASE_URL": "https://healthcare.googleapis.com/v1",
    "PROJECT": "kitsune-dev-313313",
    "LOCATION": "asia-northeast1",
    "DATASET": "phat-fhir-dataset-id",
    "FHIR_STORE": "phat-fhir-store-id",
}


# Gets credentials from the Cloud Run environment or local GOOGLE_APPLICATION_CREDENTIALS
# See https://googleapis.dev/python/google-auth/latest/reference/google.auth.html#google.auth.default
credentials, project_id = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

session = requests.AuthorizedSession(credentials)


class ResourceClient:
    def __init__(self, session=session):
        self._session = session

        self._url = "{}/projects/{}/locations/{}".format(
            fhir_configuration.get("BASE_URL"),
            fhir_configuration.get("PROJECT"),
            fhir_configuration.get("LOCATION"),
        )

        self._headers = {"Content-Type": "application/fhir+json;charset=utf-8"}

    def get_resource(
        self,
        resource_uid: str,
        resource: DomainResource,
    ) -> FHIRAbstractModel:
        """Retrieve a resource from FHIR store.
        The data retrieved from FHIR store is a JSON object, which will be converted
        into an FHIRAbstractModel Python object, using Resource Factory Function.

        :param resource_id: The FHIR resource identifier
        :type resource_id: str
        :param resource: The FHIR resource
        :type resource: DomainResource

        :rtype: FHIRAbstractModel
        """
        resource_path = "{}/datasets/{}/fhirStores/{}/fhir/{}/{}".format(
            self._url,
            fhir_configuration.get("DATASET"),
            fhir_configuration.get("FHIR_STORE"),
            resource.resource_type,
            resource_uid,
        )

        response = self._session.get(resource_path, headers=self._headers)
        result = construct_fhir_element(resource.resource_type, response.json())
        result.active = True

        response.raise_for_status()

        return result

    def get_resources(self, resource: DomainResource) -> DomainResource:
        """Retrieve all resources with given type from FHIR store.
        The data retrieved from FHIR store is a JSON object, which will be converted
        into an FHIRAbstractModel Python object, using Resource Factory Function.

        :param resource: The FHIR resource
        :type resource: DomainResource

        :rtype: FHIRAbstractModel
        """
        resource_path = "{}/datasets/{}/fhirStores/{}/fhir/{}".format(
            self._url,
            fhir_configuration.get("DATASET"),
            fhir_configuration.get("FHIR_STORE"),
            resource.resource_type,
        )

        response = self._session.get(resource_path, headers=self._headers)
        response.raise_for_status()

        return construct_fhir_element("Bundle", response.json())

    def create_resource(self, resource: DomainResource) -> FHIRAbstractModel:
        """Creates a resource with DomainResource. Returns newly create resource
        in FHIRAbstractModel Python object.

        :param resource: The FHIR resource
        :type resource: DomainResource

        :rtype: FHIRAbstractModel
        """
        resource_path = "{}/datasets/{}/fhirStores/{}/fhir/{}".format(
            self._url,
            fhir_configuration.get("DATASET"),
            fhir_configuration.get("FHIR_STORE"),
            resource.resource_type,
        )

        response = self._session.post(
            resource_path, headers=self._headers, json=resource.dict()
        )
        return construct_fhir_element(resource.resource_type, response.json())
