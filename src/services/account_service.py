import uuid
from typing import Tuple

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

    def get_account(self, account_id: str) -> Tuple[Exception, DomainResource]:
        """Return an account by account id

        :param account_id: uuid for account
        :type account_id: str

        rtype: Tuple[Exception, DomainResource]
        """
        account = self.resource_client.get_resource(account_id, "Account")
        return None, account

    def create_account(
        self, patient_id: uuid, identity: uuid = None
    ) -> Tuple[Exception, ResourceBundle]:
        """Returns account bundle

        :param patient_id: uuid for patient
        :type patient_id: uuid
        :param identity: (optional)uuid for account
        :type identity: uuid

        :rtype: Tuple[Exception, ResourceBundle]
        """
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
            "description": "Created with encounter",
        }
        account = construct_fhir_element("Account", account_jsondict)
        account_bundle = self.resource_client.get_post_bundle(account, identity)
        return None, account_bundle
