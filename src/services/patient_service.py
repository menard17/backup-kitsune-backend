from datetime import datetime

from fhir.resources import construct_fhir_element

from adapters.fhir_store import ResourceClient


class PatientService:
    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def get_patient_email(self, patient_id: str) -> tuple:
        """Returns patient email

        :param patient_id: uuid for patient
        :type patient_id: str

        :rtype: tuple
        """
        patient = self.resource_client.get_resource(patient_id, "Patient").dict()
        telecom = patient.get("telecom")
        if telecom:
            patient_email: str = list(
                filter(lambda x: x["system"] == "email", telecom)
            )[0]["value"]
            return None, patient_email
        return None, None

    def get_patient_name(self, patient_id: str) -> tuple:
        """Returns patient name

        :param patient_id: uuid for patient
        :type patient_id: str

        :rtype: tuple
        """
        patient = self.resource_client.get_resource(patient_id, "Patient")
        patient_name: dict = patient.dict()["name"][0]
        return None, patient_name

    # TODO: AB#788 This does not support multiple langauge for the name or address
    def update(
        self,
        patient_id: str,
        family_name: str,
        given_name: list,
        gender: str,
        phone: str,
        dob: str,
        address: list,
    ):
        patient = self.resource_client.get_resource(patient_id, "Patient")
        modified = False
        name = [{"use": "official"}]
        if family_name:
            modified = True
            name[0]["family"] = family_name
        else:
            name[0]["family"] = patient.name[0].family

        if given_name:
            modified = True
            name[0]["given"] = given_name
        else:
            name[0]["given"] = patient.name[0].given

        patient.name = name

        if gender:
            if gender in {"male", "female"}:
                modified = True
                patient.gender = gender

        if phone:
            modified = True
            telecom = list(filter(lambda item: item.system != "phone", patient.telecom))
            telecom.append({"system": "phone", "use": "mobile", "value": phone})
            patient.telecom = telecom

        if dob:
            format = "%Y-%m-%d"
            try:
                # Validates string format for dob
                _ = datetime.strptime(dob, format)
                modified = True
                patient.birthDate = dob
            except ValueError:
                return (
                    Exception(
                        f"This is the incorrect date string format. It should be YYYY-MM-DD: {dob}"
                    ),
                    None,
                )

        if address:
            modified = True
            patient.address = address

        if modified:
            patient = construct_fhir_element("Patient", patient)
            patient = self.resource_client.put_resource(patient_id, patient)

            return None, patient
        return None, None
