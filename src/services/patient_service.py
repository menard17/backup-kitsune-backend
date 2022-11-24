from datetime import datetime

from fhir.resources import construct_fhir_element
from fhir.resources.domainresource import DomainResource
from flask import Response

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
                filter(lambda x: x["system"] == "email" and x["use"] == "home", telecom)
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

    def get_patient_payment_details(self, patient_id: str) -> tuple[Exception, tuple]:
        """Returns patient payment detaisl

        :param patient_id: uuid for patient
        :type patient_id: str

        :rtype: tuple
        """
        patient = self.resource_client.get_resource(patient_id, "Patient")
        if patient.extension is None:
            return Exception(f"No extension is added with patient: {patient.id}"), None
        customer_ids = list(
            filter(lambda x: (x.url == "stripe-customer-id"), patient.extension)
        )
        payment_method_ids = list(
            filter(lambda x: (x.url == "stripe-payment-method-id"), patient.extension)
        )

        if not customer_ids or not payment_method_ids:
            return (
                Exception(
                    f"No customer id or payment id is registered with patient: {patient.id}"
                ),
                None,
            )

        customer_id = customer_ids[0].valueString
        payment_method_id = payment_method_ids[0].valueString

        return None, (customer_id, payment_method_id)

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
            patient.address = remove_empty_string_from_address(address)

        if modified:
            patient = construct_fhir_element("Patient", patient)
            patient = self.resource_client.put_resource(patient_id, patient)

            return None, patient
        return None, None

    def check_link(self, link: str) -> tuple[bool, Response]:
        """
        This sanity checks the link for security reason to disallow arbitrary calls to get
        proxy result of the FHIR.

        We add validation on the link to check it is related to the Patient search.
        Note that the format might be coupled with the FHIR provider (GCP for now).
        Different provider might have different link schema. It is not part of the FHIR protocol.

        A sample URL from GCP:
        https://healthcare.googleapis.com/v1/projects/kitsune-dev-313313/locations/asia-northeast1/datasets/hdb-kitsune-dev-asia-northeast1/fhirStores/fhr-kitsune-dev-asia-northeast1/fhir/Patient/?_count=1&_page_token=Cjj3YqaT4f%2F%2F%2F%2F%2BABeFKRf0xQQD%2FAf%2F%2BNTk0ZjgxODM1MjM2ZGM1M2IyZTMwNTUxNTUwMWFjODQAARABIZRNcFwxQ70GOQAAAAAebFmdSAFQAFoLCSzWOfWKBujqEANgxd%2BBywc%3D
        """

        base_url = link.split("?")[0]
        if "/Patient" not in base_url:
            return False, Response(status=400, response="not link for patient")

        return True, None

    @staticmethod
    def get_name(patient: DomainResource) -> str:
        if patient.name and len(names := patient.name) > 0:
            for name in names:
                if name.use == "official":
                    return name.family + " " + " ".join(name.given)
        return ""

    # TODO: AB#1207
    @staticmethod
    def get_kana(patient: DomainResource) -> str:
        return ""

    @staticmethod
    def get_phone(patient: DomainResource) -> str:
        if patient.telecom and len(telecoms := patient.telecom) > 0:
            for telecom in telecoms:
                if telecom.use == "mobile":
                    return telecom.value
        return ""

    @staticmethod
    def get_address(patient: DomainResource) -> str:
        if patient.address and len(patient.address) > 0:
            return (
                patient.address[0].state
                + patient.address[0].city
                + " ".join(patient.address[0].line)
            )
        return ""

    @staticmethod
    def get_zip(patient: DomainResource) -> str:
        if patient.address and len(patient.address) > 0:
            return patient.address[0].postalCode
        return ""


def remove_empty_string_from_address(addresses: list) -> list:
    lines = [address["line"] for address in addresses]
    modified_lines = [[item for item in line if item != ""] for line in lines]
    modified_addresses = []
    for idx, address in enumerate(addresses):
        # Create a Deep copy
        modified_address = address.copy()
        modified_address["line"] = modified_lines[idx]
        modified_addresses.append(modified_address)
    return modified_addresses
