import google.auth
from fhir.resources import construct_fhir_element
from google.auth.transport import requests

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
credentials, project_id = google.auth.default()

scoped_credentials = credentials.with_scopes(
    ["https://www.googleapis.com/auth/cloud-platform"]
)


def get_resource(resource_type, resource_id):
    """Retrieve a resource from FHIR store.

    The data retrieved from FHIR store is a JSON object, which will be converted
    into an fhir.resources Python object, using Resource Factory Function.

    :param resource_type: The FHIR resource type
    :type resource_type: str

    :param resource_id: The FHIR resource identifier
    :type resource_id: str

    :rtype: Resource
    """

    # Creates a requests Session object with the credentials.
    session = requests.AuthorizedSession(scoped_credentials)

    url = "{}/projects/{}/locations/{}".format(
        fhir_configuration.get("BASE_URL"),
        fhir_configuration.get("PROJECT"),
        fhir_configuration.get("LOCATION"),
    )

    resource_path = "{}/datasets/{}/fhirStores/{}/fhir/{}/{}".format(
        url,
        fhir_configuration.get("DATASET"),
        fhir_configuration.get("FHIR_STORE"),
        resource_type,
        resource_id,
    )

    # Sets required application/fhir+json header on the request
    headers = {"Content-Type": "application/fhir+json;charset=utf-8"}

    response = session.get(resource_path, headers=headers)
    response.raise_for_status()

    return construct_fhir_element(resource_type, response.json())
