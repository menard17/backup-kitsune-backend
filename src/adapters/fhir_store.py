import json
import os
from typing import List, Tuple, TypedDict
from urllib.parse import quote
from uuid import UUID

import google.auth
from fhir.resources import construct_fhir_element
from fhir.resources.domainresource import DomainResource
from fhir.resources.fhirtypes import BundleType
from google.auth.transport import requests


def _get_url():
    return "{}/projects/{}/locations/{}/datasets/{}/fhirStores/{}/fhir".format(
        "https://healthcare.googleapis.com/v1",
        os.environ["PROJECT"],
        os.environ["LOCATION"],
        os.environ["FHIR_DATASET"],
        os.environ["FHIR_STORE"],
    )


# Gets credentials from the Cloud Run environment or local GOOGLE_APPLICATION_CREDENTIALS
# See https://googleapis.dev/python/google-auth/latest/reference/google.auth.html#google.auth.default
def _get_session():
    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    return requests.AuthorizedSession(credentials)


ResourceSearchArgs = List[Tuple[str, str]]


class ResourceBundle(TypedDict):
    resource: DomainResource
    request: str
    fullUrl: str or None


class ResourceClient:
    def __init__(self, session=None, url=None):
        self._session = session or _get_session()
        self._url = url or _get_url()
        self._headers = {"Content-Type": "application/fhir+json;charset=utf-8"}
        self._last_seen_headers = {}

    @property
    def last_seen_etag(self):
        """
        The latest "Etag" seen from this client.
        This is for optimistic locking.
        see: https://build.fhir.org/http.html#concurrency
        """
        return self._last_seen_headers.get("Etag")

    def get_post_bundle(
        self, resource: DomainResource, fullurl: str = None
    ) -> ResourceBundle:
        """Returns dictionary of bundle for post ready to process with `create_resources`"""
        return self._get_bundle(resource, None, fullurl, "POST")

    def get_put_bundle(
        self, resource: DomainResource, uid: str, fullurl: str = None
    ) -> ResourceBundle:
        """Returns dictionary of bundle for put ready to process with `create_resources`"""
        return self._get_bundle(resource, uid, fullurl, "PUT")

    def _get_bundle(
        self, resource: DomainResource, uid: str, fullurl: str, method: str
    ) -> ResourceBundle:
        url = resource.resource_type
        if uid:
            url = f"{resource.resource_type}/{uid}"

        bundle = {
            "resource": resource,
            "request": {"method": method, "url": url},
        }

        if fullurl:
            bundle["fullUrl"] = fullurl
        return bundle

    def create_resources(self, bundles: List[ResourceBundle], lock_header: str = "") -> BundleType:
        """Creates resources in FHIR in transaction manner

        :param bundles: list of bundle resources
        :type bundles: List[ResourceBundle]
        :return: Created resources in JSON object
        :rtype: Response
        """
        body = {
            "resourceType": "Bundle",
            "id": "bundle-transaction",
            "type": "transaction",
            "entry": bundles,
        }

        header = {
            "Content-Type": "application/fhir+json;charset=utf-8",
            "Prefer": "return=representation",
        }

        result = construct_fhir_element(body["resourceType"], body)

        if lock_header != "":
            # Optimistic lock: https://build.fhir.org/http.html#concurrency
            header["If-Match"] = lock_header

        response = self._session.post(
            f"{self._url}", headers=header, data=result.json(indent=True)
        )
        response.raise_for_status()
        self._last_seen_headers = response.headers
        return construct_fhir_element(body["resourceType"], response.json())

    def get_resource(
        self,
        resource_uid: UUID,
        resource_type: str,
    ) -> DomainResource:
        """Retrieve a resource from FHIR store.
        The data retrieved from FHIR store is a JSON object,
        which will be converted into an DomainResource Python object,
        using Resource Factory Function.

        :param resource_id: The FHIR resource identifier
        :type resource_id: str
        :param resource_type: The FHIR resource type
        :type resource_type: str

        :rtype: DomainResource
        """
        resource_path = f"{self._url}/{resource_type}/{resource_uid}"
        response = self._session.get(resource_path, headers=self._headers)
        response.raise_for_status()
        self._last_seen_headers = response.headers
        result = construct_fhir_element(resource_type, response.json())
        return result

    def get_resources(self, resource_type: str, count: int = 300) -> DomainResource:
        """Retrieve all resources with given type from FHIR store.
        The data retrieved from FHIR store is a JSON object,
        which will be converted into an DomainResource Python object,
        using Resource Factory Function.

        :param resource_type: The FHIR resource type
        :type resource_type: str
        :param count: the page count of the results. Default to 300.
        :type count: int

        :rtype: DomainResource
        """
        count_url_param = f"?_count={count}"
        resource_path = f"{self._url}/{resource_type}"
        resource_path += count_url_param

        response = self._session.get(resource_path, headers=self._headers)
        response.raise_for_status()
        self._last_seen_headers = response.headers

        return construct_fhir_element("Bundle", response.json())

    def link(self, url: str) -> DomainResource:
        response = self._session.get(url, headers=self._headers)
        response.raise_for_status()
        self._last_seen_headers = response.headers

        return construct_fhir_element("Bundle", response.json())

    def search(self, resource_type: str, search: ResourceSearchArgs) -> DomainResource:
        """Search all resources with given type and search condition from FHIR store.
        The data retrieved from FHIR store is a JSON object,
        which will be converted into an DomainResource Python object,
        using Resource Factory Function. Currently returning search results = 300

        :param resource_type: The FHIR resource type
        :param search: list of search (key, value) tuple

        :rtype: DomainResource
        """
        resource_path = f"{self._url}/{resource_type}"

        # Increase the max number of search results returned from 100 to 300
        if "_count" not in map(lambda x: x[0], search):
            modified_search = search + [("_count", "300")]
        else:
            modified_search = search

        for i, (key, value) in enumerate(modified_search):
            if i == 0:
                resource_path += "?"
            else:
                resource_path += "&"
            resource_path += f"{key}={quote(value, safe='')}"

        response = self._session.get(resource_path, headers=self._headers)
        response.raise_for_status()
        self._last_seen_headers = response.headers

        return construct_fhir_element("Bundle", response.json())

    def create_resource(self, resource: DomainResource) -> DomainResource:
        """Creates a resource with DomainResource. Returns newly create resource
        in DomainResource Python object.

        :param resource: The FHIR resource
        :type resource: DomainResource

        :rtype: DomainResource
        """
        resource_path = f"{self._url}/{resource.resource_type}"
        # NOTE: resource.json(indent=True) would make date field to string
        # otherwise the json result would not be a string for date fields and
        # would lead to error later
        response = self._session.post(
            resource_path, headers=self._headers, data=resource.json(indent=True)
        )
        response.raise_for_status()
        self._last_seen_headers = response.headers
        return construct_fhir_element(resource.resource_type, response.json())

    def patch_resource(
        self, resource_uid: UUID, resource_type: str, resource: list
    ) -> DomainResource:
        """Updates a resource with patch. Returns updated resource
        in DomainResource Python object.
        :param resource: list with patch operation. replace does not work
        :type resource: list
        :rtype: DomainResource
        """
        resource_path = f"{self._url}/{resource_type}/{resource_uid}"
        # Need separate header for patch call
        _headers = {"Content-Type": "application/json-patch+json"}

        body = json.dumps(resource)

        response = self._session.patch(resource_path, headers=_headers, data=body)
        response.raise_for_status()
        self._last_seen_headers = response.headers

        return construct_fhir_element(resource_type, response.json())

    def put_resource(
        self,
        resource_uid: UUID,
        resource: DomainResource,
        lock_header: str = "",
    ) -> DomainResource:
        """Updates a resource with put. Returns updated resource
        in DomainResource Python object.
        """

        resource_path = f"{self._url}/{resource.resource_type}/{resource_uid}"

        headers = self._headers
        if lock_header != "":
            # Optimistic lock: https://build.fhir.org/http.html#concurrency
            headers["If-Match"] = lock_header

        response = self._session.put(
            resource_path, headers=headers, data=resource.json(indent=True)
        )
        response.raise_for_status()
        self._last_seen_headers = response.headers
        return construct_fhir_element(resource.resource_type, response.json())

    def delete_resources(self, requests: list):
        """Delete bundle of resources with post request
        This is not meant to be used in API endpoint but for the clean up

        :param requests: list of entry, [{'request': {'method': 'DELETE', 'url': 'Patient/d5151e19-3c05-4273-ac48-91820f8c288d'}}]
        :type resource: list
        :rtype: DomainResource
        """
        resource_path = f"{self._url}"
        # Need separate header for patch call
        body = {
            "resourceType": "Bundle",
            "id": "bundle-transaction",
            "type": "transaction",
            "entry": requests,
        }
        bundle_body = construct_fhir_element("Bundle", body)

        response = self._session.post(
            resource_path, headers=self._headers, data=bundle_body.json(indent=True)
        )
        response.raise_for_status()
        self._last_seen_headers = response.headers

        return response.json()
