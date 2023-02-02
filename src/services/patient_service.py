from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID

from fhir.resources.address import Address
from fhir.resources.contactpoint import ContactPoint
from fhir.resources.extension import Extension
from fhir.resources.fhirtypes import (
    AddressType,
    Code,
    ContactPointType,
    Date,
    ExtensionType,
    Uri,
)
from fhir.resources.domainresource import DomainResource
from fhir.resources.humanname import HumanName
from fhir.resources.patient import Patient
from flask.wrappers import Response

from adapters.fhir_store import ResourceClient


class PatientService:
    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def get_patient_email(self, patient_id: UUID) -> tuple:
        """Returns patient email

        :param patient_id: uuid for patient
        :type patient_id: uuid

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

    def get_patient_name(self, patient_id: UUID) -> tuple:
        """Returns patient name

        :param patient_id: uuid for patient
        :type patient_id: uuid

        :rtype: tuple
        """
        patient = self.resource_client.get_resource(patient_id, "Patient")
        patient_name: dict = patient.dict()["name"][0]
        return None, patient_name

    def get_voip_token(
        self, patient_id: UUID
    ) -> tuple[Optional[Exception], Optional[str]]:
        """Returns patient's voip token

        :param patient_id: uuid for patient
        :type patient_id: uuid

        :rtype: tuple
        """
        patient = self.resource_client.get_resource(patient_id, "Patient")
        if patient.extension is None:
            return Exception(f"No extension is added with patient: {patient_id}"), None
        voip_token = list(filter(lambda x: (x.url == "voip-token"), patient.extension))

        if not voip_token:
            return (
                Exception(f"No voip_token is registered with patient: {patient_id}"),
                None,
            )

        voip_token_value = voip_token[0].valueString

        return None, voip_token_value

    def get_patient_payment_details(
        self, patient_id: UUID
    ) -> tuple[Optional[Exception], Optional[tuple]]:
        """Returns patient payment detaisl

        :param patient_id: uuid for patient
        :type patient_id: uuid

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
    # TODO: AB#1355 Support multiple orca ids to support multiple organizations
    def update(
        self,
        patient_id: UUID,
        family_name: Optional[str] = None,
        given_name: Optional[list] = None,
        gender: Optional[str] = None,
        phone: Optional[str] = None,
        dob: Optional[str] = None,
        address: Optional[list] = None,
        orca_id: Optional[str] = None,
    ):
        resource = self.resource_client.get_resource(patient_id, "Patient")
        patient = Patient(**resource.dict())
        modified = False
        if family_name:
            modified = True
            patient.name[0].family = family_name

        if given_name:
            modified = True
            patient.name[0].given = given_name

        if gender:
            if gender in {"male", "female"}:
                modified = True
                patient.gender = Code(gender)

        if phone:
            modified = True
            telecom = list(
                filter(
                    lambda item: ContactPoint(**item.__dict__).system != "phone",
                    patient.telecom,
                )
            )
            telecom.append(
                ContactPointType(**{"system": "phone", "use": "mobile", "value": phone})
            )
            patient.telecom = telecom

        if dob:
            format = "%Y-%m-%d"
            try:
                # Validates string format for dob
                date = datetime.strptime(dob, format)
                modified = True
                patient.birthDate = Date(month=date.month, day=date.day, year=date.year)
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

        if orca_id:
            modified = True
            patient.extension = [
                ExtensionType(**{"valueString": orca_id, "url": Uri("orca-id")})
            ]

        if modified:
            patient = self.resource_client.put_resource(patient_id, patient)

            return None, patient
        return None, None

    def check_link(self, link: str) -> tuple[bool, Optional[Response]]:
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
    def get_name(patient: Patient) -> str:
        if patient.name and len(names := patient.name) > 0:
            for name_item in names:
                name = HumanName(**name_item.__dict__)
                if name.use == "official":
                    return name.family + " " + " ".join(name.given)
        return ""

    @staticmethod
    def get_kana(patient: Patient) -> str:
        if patient.name and len(names := patient.name) > 0:
            for name_item in names:
                name = HumanName(**name_item.__dict__)
                if (
                    name.use != "official"
                    and name.extension
                    and name.extension[0]
                    and (extension := Extension(**name.extension[0].__dict__))
                    and extension.valueString == "SYL"
                ):
                    return name.family + " " + " ".join(name.given)
        return ""

    @staticmethod
    def get_phone(patient: Patient) -> str:
        if patient.telecom and len(telecoms := patient.telecom) > 0:
            for telecom_item in telecoms:
                telecom = ContactPoint(**telecom_item.__dict__)
                if telecom.use == "mobile":
                    return telecom.value
        return ""

    @staticmethod
    def get_address(patient: Patient) -> str:
        if patient.address and len(patient.address) > 0:
            address = Address(**patient.address[0].__dict__)
            return address.state + address.city + " ".join(address.line)
        return ""

    @staticmethod
    def get_zip(patient: Patient) -> str:
        if patient.address and len(patient.address) > 0:
            address = Address(**patient.address[0].__dict__)
            return address.postalCode
        return ""

    def put_orca_id_for_patient(self, orca_id: str, patient_id: UUID) -> Tuple[Optional[Exception], DomainResource]:
        resource = self.resource_client.get_resource(patient_id, "Patient")
        patient = Patient(**resource.dict())
        patient.extension = [
            ExtensionType(**{"valueString": orca_id, "url": Uri("orca-id")})
        ]
        patient = self.resource_client.put_resource(patient_id, patient)
        return None, patient


def remove_empty_string_from_address(addresses: list) -> list[AddressType]:
    lines = [address["line"] for address in addresses]
    modified_lines = [[item for item in line if item != ""] for line in lines]
    modified_addresses: list[AddressType] = []
    for idx, address in enumerate(addresses):
        # Create a Deep copy
        modified_address = address.copy()
        modified_address["line"] = modified_lines[idx]
        modified_addresses.append(modified_address)
    return modified_addresses
