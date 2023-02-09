import base64
import os
from enum import Enum, auto
from typing import Optional

from fhir.resources.account import Account
from fhir.resources.appointment import Appointment
from fhir.resources.documentreference import DocumentReference
from fhir.resources.medicationrequest import MedicationRequest
from fhir.resources.patient import Patient
from fhir.resources.practitionerrole import PractitionerRole
from fhir.resources.servicerequest import ServiceRequest
from notion_client import Client

from utils.notion_setup import NotionSingleton

ENCOUNTER_DATABASE_ID = os.getenv("NOTION_ENCOUNTER_DATABASE_ID")


class NotionClientDoesNotExistException(Exception):
    pass


class NotionDBDoesNotExistException(Exception):
    pass


class NotionService:
    def __init__(
        self,
        client: Client = None,
        encounter_database_id: str = None,
    ) -> None:
        self._client = client or NotionSingleton.client()
        if self._client is None:
            raise NotionClientDoesNotExistException("Notion client cannot be None")
        self._encounter_database_id = encounter_database_id or ENCOUNTER_DATABASE_ID
        if self._encounter_database_id is None:
            raise NotionDBDoesNotExistException(
                "Notion encounter database ID cannot be None"
            )

    def query_encounter_page(self, encounter_id: str):
        return self._client.databases.query(
            database_id=self._encounter_database_id,
            filter={"property": "encounter_id", "rich_text": {"equals": encounter_id}},
        )

    def create_encounter_page(self, encounter_id: str):
        return self._client.pages.create(
            parent={"database_id": self._encounter_database_id},
            properties={
                "encounter_id": {
                    "title": [{"type": "text", "text": {"content": encounter_id}}]
                }
            },
        )

    def sync_encounter_to_notion(
        self,
        encounter_page_id: str,
        account: Account = None,
        appointment: Appointment = None,
        patient: Patient = None,
        practitioner_role: PractitionerRole = None,
        clinical_note: DocumentReference = None,
        medication_request: MedicationRequest = None,
        service_request: ServiceRequest = None,
        insurance_card: DocumentReference = None,
        medical_card: DocumentReference = None,
    ):
        # Have to add a default date
        properties = {}

        delivery_date = (
            "1994-04-04" if appointment is None else appointment.start.isoformat()
        )
        properties["delivery_date"] = get_propery_value(
            delivery_date, PropertyType.Date
        )
        properties["email"] = get_propery_value(self._render_email(patient))
        properties["user_name"] = get_propery_value(self._render_full_name(patient))
        properties["user_name_kana"] = get_propery_value(
            self._render_kana_name(patient)
        )
        phone_number = (
            ""
            if patient is None
            else next(x for x in patient.telecom if x.system == "phone").value
        )
        properties["phone_number"] = get_propery_value(phone_number)
        gender = "" if patient is None or patient.gender is None else patient.gender
        properties["gender"] = get_propery_value(gender)
        dob = (
            ""
            if patient is None or patient.birthDate is None
            else str(patient.birthDate)
        )
        properties["dob"] = get_propery_value(dob)
        properties["address"] = get_propery_value(self._render_address(patient))
        properties["emr"] = get_propery_value(self._render_emr(clinical_note))

        # We use PractitionerRole instead of the Practitioner since the result
        # from the search bundle is only PractitionerRole. The "practitioner"
        # field in this resource is a reference type which has the "display"
        # field and can be used for displaying doctor name.
        doctor = (
            "" if practitioner_role is None else practitioner_role.practitioner.display
        )
        properties["doctor"] = get_propery_value(doctor)
        insurance_card_front = (
            ""
            if insurance_card is None
            else self._find_attachment(insurance_card, "front").url
        )
        properties["insurance_card_front"] = get_propery_value(insurance_card_front)
        medical_card_attachments = ""
        if medical_card is not None:
            page = 0
            attachment = self._find_attachment(medical_card, f"Page {page}")
            while attachment:
                medical_card_attachments += attachment.url + "\n"
                page += 1
                attachment = self._find_attachment(medical_card, f"Page {page}")
        properties["medical_card"] = get_propery_value(medical_card_attachments)
        account_id = "" if account is None else account.id
        properties["account_id"] = get_propery_value(account_id)
        properties["prescription"] = get_propery_value(
            self._render_medication_codes(medication_request)
        )
        properties["tests"] = get_propery_value(
            self._render_service_codes(service_request)
        )

        return self._client.pages.update(
            page_id=encounter_page_id, properties=properties
        )

    def _render_email(self, patient: Optional[Patient]):
        if patient is None:
            return ""

        email = next(
            (x for x in patient.telecom if x.system == "email" and x.use == "home"),
            None,
        )
        if email is None:
            return ""

        return email.value

    def _render_full_name(self, patient: Optional[Patient]):
        if patient is None:
            return ""

        name = next((x for x in patient.name if x.use == "official"), None)
        if name is None:
            return ""

        first_name = "" if len(name.given) == 0 else name.given[0]
        last_name = name.family
        full_name = f"{last_name} {first_name}"
        return full_name

    def _render_kana_name(self, patient: Optional[Patient]):
        if patient is None:
            return ""
        kana_name = next(
            (
                x
                for x in patient.name
                if x.extension and x.extension[0].valueString == "SYL"
            ),
            None,
        )
        if kana_name is None:
            return ""

        kana_first_name = "" if len(kana_name.given) == 0 else kana_name.given[0]
        kana_last_name = kana_name.family
        kana_full_name = f"{kana_last_name} {kana_first_name}"
        return kana_full_name

    def _render_address(self, patient: Optional[Patient]):
        if patient is None:
            return ""

        address = next((x for x in patient.address if x.use == "home"), None)
        if address is None:
            return ""

        return " ".join(
            [address.postalCode, address.state, address.city] + address.line
        )

    def _render_emr(self, clinical_note: Optional[DocumentReference]):
        if clinical_note is None:
            return ""

        attachment_content_list = clinical_note.content
        return "\n".join(
            [
                base64.b64decode(x.attachment.data).decode("utf-8")
                for x in attachment_content_list
            ]
        )

    def _find_attachment(self, document_reference: DocumentReference, title: str):
        attachment = next(
            (
                x.attachment
                for x in document_reference.content
                if x.attachment.title == title
            ),
            None,
        )
        return attachment

    def _render_medication_codes(self, medication_request: Optional[MedicationRequest]):
        if (
            medication_request is None
            or medication_request.medicationCodeableConcept is None
            or medication_request.medicationCodeableConcept.coding is None
        ):
            return ""

        coding_list = medication_request.medicationCodeableConcept.coding
        return "\n".join([x.display for x in coding_list])

    def _render_service_codes(self, service_request: ServiceRequest):
        if (
            service_request is None
            or service_request.code is None
            or service_request.code.coding is None
        ):
            return ""
        coding_list = service_request.code.coding
        return "\n".join([x.display for x in coding_list])


class PropertyType(Enum):
    Text = auto()
    Date = auto()


def get_propery_value(value: str, type: PropertyType = PropertyType.Text):
    if type == PropertyType.Date:
        return {"date": {"start": value}}
    return {"rich_text": [{"text": {"content": value}}]}
