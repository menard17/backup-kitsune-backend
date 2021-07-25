import google.auth
import json
from fhir.resources import construct_fhir_element
from fhir.resources.fhirabstractmodel import FHIRAbstractModel
from google.auth.transport import requests
from fhir.resources.domainresource import DomainResource
from fhir.resources.bundle import Bundle
from urllib.parse import quote


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

ResourceSearchArgs = list[tuple[str, str]]
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
        resource_type: str,
    ) -> DomainResource:
        """Retrieve a resource from FHIR store.
        The data retrieved from FHIR store is a JSON object, which will be converted
        into an DomainResource Python object, using Resource Factory Function.

        :param resource_id: The FHIR resource identifier
        :type resource_id: str
        :param resource_type: The FHIR resource type
        :type resource_type: str

        :rtype: DomainResource
        """
        resource_path = "{}/datasets/{}/fhirStores/{}/fhir/{}/{}".format(
            self._url,
            fhir_configuration.get("DATASET"),
            fhir_configuration.get("FHIR_STORE"),
            resource_type,
            resource_uid,
        )

        response = self._session.get(resource_path, headers=self._headers)
        response.raise_for_status()
        result = construct_fhir_element(resource_type, response.json())
        return result

    def get_resources(self, resource_type: str) -> DomainResource:
        """Retrieve all resources with given type from FHIR store.
        The data retrieved from FHIR store is a JSON object, which will be converted
        into an DomainResource Python object, using Resource Factory Function.

        :param resource_type: The FHIR resource type
        :type resource_type: str

        :rtype: DomainResource
        """
        resource_path = "{}/datasets/{}/fhirStores/{}/fhir/{}".format(
            self._url,
            fhir_configuration.get("DATASET"),
            fhir_configuration.get("FHIR_STORE"),
            resource_type,
        )

        response = self._session.get(resource_path, headers=self._headers)
        response.raise_for_status()

        return construct_fhir_element("Bundle", response.json())

    def search(self, resource_type: str, search: ResourceSearchArgs) -> DomainResource:
        """Search all resources with given type and search condition from FHIR store.
        The data retrieved from FHIR store is a JSON object, which will be converted
        into an DomainResource Python object, using Resource Factory Function.

        :param resource_type: The FHIR resource type
        :param search: list of search (key, value) tuple

        :rtype: DomainResource
        """
        dataset = fhir_configuration.get("DATASET")
        fhir_store = fhir_configuration.get("FHIR_STORE")
        resource_path = f"{self._url}/datasets/{dataset}/fhirStores/{fhir_store}/fhir/{resource_type}"

        for i, (key, value) in enumerate(search):
            if i == 0:
                resource_path += "?"
            else:
                resource_path += "&"
            resource_path += f"{key}={quote(value, safe='')}"

        response = self._session.get(resource_path, headers=self._headers)
        response.raise_for_status()

        return construct_fhir_element("Bundle", response.json())

    def create_resource(self, resource: DomainResource) -> DomainResource:
        """Creates a resource with DomainResource. Returns newly create resource
        in DomainResource Python object.

        :param resource: The FHIR resource
        :type resource: DomainResource

        :rtype: DomainResource
        """
        resource_path = "{}/datasets/{}/fhirStores/{}/fhir/{}".format(
            self._url,
            fhir_configuration.get("DATASET"),
            fhir_configuration.get("FHIR_STORE"),
            resource.resource_type,
        )

        # NOTE: resource.json(indent=True) would make date field to string
        # otherwise the json result would not be a string for date fields and
        # would lead to error later
        response = self._session.post(
            resource_path, headers=self._headers, data=resource.json(indent=True)
        )

        response_dict = response.json() # it will return a dict actually despite the name json()
        if response_dict["resourceType"] == resource.resource_type:
            return construct_fhir_element(resource.resource_type, response_dict)
        else:
            raise Exception("Failed in ResourceClient.create_resource: {}".format(response_dict))

    def get_resources_by_key(self, key: str, value: str, resource_type: str) -> Bundle:
        """Returns object containing key value pair in FHIR

        :param key: Key you want to search in FHIR. E.g. name
        :type key: str
        :param value: Value you want to search. E.g. UMed Inc,
        :type value: str
        :param resource_type: type of resource, e.g. Organization
        :type resource_type: str

        rtype: Bundle
        """
        resource_path = "{}/datasets/{}/fhirStores/{}/fhir/{}?{}:exact={}".format(
            self._url,
            fhir_configuration.get("DATASET"),
            fhir_configuration.get("FHIR_STORE"),
            resource_type,
            key,
            value,
        )

        response = self._session.get(resource_path, headers=self._headers)
        response.raise_for_status()

        return construct_fhir_element("Bundle", response.json())

    def patch_resource(self, resource_uid: str,
                       resource_type: str, resource: list) -> DomainResource:
        """Updates a resource with patch. Returns updated resource
        in DomainResource Python object.
        :param resource: list with patch operation
        :type resource: DomainResource
        :rtype: DomainResource
        """

        resource_path = "{}/datasets/{}/fhirStores/{}/fhir/{}/{}".format(
            self._url,
            fhir_configuration.get("DATASET"),
            fhir_configuration.get("FHIR_STORE"),
            resource_type,
            resource_uid,
        )

        # Need separate header for patch call
        _headers = {"Content-Type": "application/json-patch+json"}

        body = json.dumps(resource)

        response = self._session.patch(
            resource_path, headers=_headers, data=body
        )

        return construct_fhir_element(resource_type, response.json())

