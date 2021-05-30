import google.auth
from fhir.resources.patient import Patient
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


def get_patient(patient_uid):
    return Patient.parse_obj(get_resource_raw("Patient", patient_uid))


def get_resource_raw(resource_type, resource_uid):

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
        resource_uid,
    )

    # Sets required application/fhir+json header on the request
    headers = {"Content-Type": "application/fhir+json;charset=utf-8"}

    response = session.get(resource_path, headers=headers)
    response.raise_for_status()

    resource = response.json()

    return resource
