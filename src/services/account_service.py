import string
import uuid
from typing import Optional, Tuple

from fhir.resources import construct_fhir_element
from fhir.resources.domainresource import DomainResource

from adapters.fhir_store import ResourceBundle, ResourceClient
from utils.system_code import SystemCode


class AccountService:
    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def inactivate_account(self, account_id: uuid) -> Tuple[Exception, ResourceBundle]:
        account = self.resource_client.patch_resource(
            account_id,
            "Account",
            [{"op": "add", "path": "/status", "value": "inactive"}],
        )
        return None, account

    def get_account(
        self, account_id: str, is_active: Optional[bool] = None
    ) -> Tuple[Exception, DomainResource]:
        """Return an account by account id

        :param account_id: uuid for account
        :type account_id: str

        rtype: Tuple[Exception, DomainResource]
        """
        search_clause = [("_id", account_id)]
        if is_active:
            search_clause.append(("status", "active"))
        account = self.resource_client.search("Account", search=search_clause)
        if account.total == 0:
            return Exception(f"Account does not exist. account_id: {account_id}"), None

        return None, account.entry[0].resource

    def _create_account(self, patient_id: uuid, description: string = None):
        account_jsondict = {
            "resourceType": "Account",
            "status": "active",
            "type": {"coding": [SystemCode.billing()], "text": "patient"},
            "subject": [{"reference": f"Patient/{patient_id}"}],
            "guarantor": [
                {
                    "party": {"reference": f"Patient/{patient_id}"},
                    "onHold": "false",
                }
            ],
        }
        if description:
            account_jsondict["description"] = description
        account = construct_fhir_element(
            account_jsondict["resourceType"], account_jsondict
        )
        return account

    def create_account_bundle(
        self,
        patient_id: uuid,
        identity: uuid = None,
        description: string = None,
    ) -> Tuple[Exception, ResourceBundle]:
        """Returns account bundle

        :param patient_id: uuid for patient
        :type patient_id: uuid
        :param identity: (optional)uuid for account
        :type identity: uuid

        :rtype: Tuple[Exception, ResourceBundle]
        """
        account = self._create_account(patient_id, description)
        account_bundle = self.resource_client.get_post_bundle(account, identity)
        return None, account_bundle

    def create_account_resource(
        self, patient_id: uuid, description: string
    ) -> Tuple[Exception, ResourceBundle]:
        """Returns account

        :param patient_id: uuid for patient
        :type patient_id: uuid

        :rtype: Tuple[Exception, ResourceBundle]
        """
        account = self._create_account(patient_id, description)
        try:
            account_resource = self.resource_client.create_resource(account)
            return None, account_resource
        except Exception:
            return (
                Exception("Failed to create account for the patient"),
                None,
            )
