import uuid
from typing import Tuple

from fhir.resources import construct_fhir_element

from adapters.fhir_store import ResourceBundle, ResourceClient
from utils.system_code import SystemCode


class EncounterService:
    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def create_encounter(
        self,
        appointment_id: uuid,
        role_id: uuid,
        patient_id: uuid,
        account_id: uuid,
        identity: uuid = None,
    ) -> Tuple[Exception, ResourceBundle]:
        """Returns encounter bundle

        :param appointment_id: uuid for appointment
        :type appointment_id: uuid
        :param role_id: uuid for practitioner role
        :type role_id: uuid
        :param patient_id: uuid for patient
        :type patient_id: uuid
        :param account_id: uuid for account
        :type account_id: uuid
        :param identity: (optional)uuid for encounter
        :type identity: uuid

        :rtype: Tuple[Exception, ResourceBundle]
        """
        encounter_jsondict = {
            "resourceType": "Encounter",
            "status": "in-progress",
            "appointment": [{"reference": f"Appointment/{appointment_id}"}],
            "class": SystemCode.enconuter(),
            "subject": {"reference": f"Patient/{patient_id}"},
            "account": [{"reference": account_id}],
            "participant": [
                {
                    "individual": {
                        "reference": f"PractitionerRole/{role_id}",
                    },
                },
            ],
        }
        encounter = construct_fhir_element("Encounter", encounter_jsondict)
        encounter_bundle = self.resource_client.get_post_bundle(encounter, identity)
        return None, encounter_bundle
