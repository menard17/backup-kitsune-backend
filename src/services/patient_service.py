import uuid
from typing import Dict, Tuple

from adapters.fhir_store import ResourceClient


class PatientService:
    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def get_patient_email(self, patient_id: uuid) -> Tuple[Exception, str]:
        """Returns patient email
        :param patient_id: uuid for patient
        :type patient_id: uuid
        :rtype: Tuple[Exception, str]
        """
        patient = self.resource_client.get_resource(patient_id, "Patient").dict()
        telecom = patient.get("telecom")
        if telecom:
            patient_email: str = list(
                filter(lambda x: x["system"] == "email", telecom)
            )[0]["value"]
            return None, patient_email
        return None, None

    def get_patient_name(self, patient_id: uuid) -> Tuple[Exception, Dict]:
        """Returns patient name
        :param patient_id: uuid for patient
        :type patient_id: uuid
        :rtype: Tuple[Exception, Dict]
        """
        patient = self.resource_client.get_resource(patient_id, "Patient")
        patient_name: Dict = patient.dict()["name"][0]
        return None, patient_name
