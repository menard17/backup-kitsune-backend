from typing import TypedDict


class ServiceURL:
    service_type = "http://hl7.org/fhir/valueset-service-type.html"
    service_category = "http://hl7.org/fhir/codesystem-service-category.html"
    appointment_type = "http://terminology.hl7.org/CodeSystem/v2-0276"
    service_request_code = "http://snomed.info/sct"
    practition_type = "http://terminology.hl7.org/CodeSystem/practitioner-role"
    communication_code = "urn:ietf:bcp:47"
    document_type = "http://loinc.org"
    cancel_reason_type = (
        "http://terminology.hl7.org/CodeSystem/appointment-cancellation-reason"
    )
    encounter_code = "http://terminology.hl7.org/CodeSystem/v3-ActCode"
    payment_url = "https://stripe.com/docs/api/payment_intents"
    clinical_note = "http://fhir.org/guides/argonaut-clinicalnotes/CodeSystem/documentreference-category"


class Code(TypedDict):
    system: ServiceURL
    code: str
    display: str


def create_coding_clause(url: ServiceURL, code: str, display: str = None) -> Code:
    result = {
        "system": url,
        "code": code,
    }
    if display:
        result["display"] = display
    return result


def create_token(url: ServiceURL, code: str):
    return f"{url}|{code}"


class ServiceType:
    walkin: str
    routine: str
    followup: str


class CancelType:
    portal: str
    patient: str


class ProvidingType:
    online: str
    visit: str


class SystemCode:
    @staticmethod
    def service(providing_type: ProvidingType):
        if providing_type == "online":
            return create_coding_clause(
                ServiceURL.service_type, "540", "Online Service"
            )
        elif providing_type == "visit":
            return create_coding_clause(ServiceURL.service_type, "497", "Home Visits")
        else:
            return create_coding_clause(
                ServiceURL.service_type, "124", "General Practice"
            )

    @staticmethod
    def general_practice():
        return create_coding_clause(
            ServiceURL.service_category, "17", "General Practice"
        )

    @staticmethod
    def appointment_service_type(service_type: ServiceType is None):
        if service_type == "walkin":
            return create_coding_clause(
                ServiceURL.appointment_type,
                "WALKIN",
                "A previously unscheduled walk-in visit",
            )
        elif service_type == "routine":
            return create_coding_clause(
                ServiceURL.appointment_type, "ROUTINE", "Routine appointment"
            )
        else:
            return create_coding_clause(
                ServiceURL.appointment_type,
                "FOLLOWUP",
                "A follow up visit from a previous appointment",
            )

    @staticmethod
    def appointment_cancel_type(cancel_type: CancelType is None):
        if cancel_type == "patient":
            return create_coding_clause(ServiceURL.cancel_reason_type, "pat", "Patient")
        elif cancel_type == "portal":
            return create_coding_clause(
                ServiceURL.cancel_reason_type,
                "pat-cpp",
                "Patient: Canceled via Patient Portal",
            )

    @staticmethod
    def document_type_code(document_type: str):
        if document_type == "insurance_card":
            return create_coding_clause(
                ServiceURL.document_type, "64290-0", "Insurance Card"
            )
        elif document_type == "medical_record":
            return create_coding_clause(
                ServiceURL.document_type, "34117-2", "Medical Record"
            )
        elif document_type == "clinical_note":
            return create_coding_clause(
                ServiceURL.document_type, "55110-1", "Conclusions Document"
            )
        else:
            return document_type

    def document_category_code(document_type: str):
        if document_type == "clinical_note":
            return create_coding_clause(
                ServiceURL.clinical_note, "clinical-note", "Clinical Note"
            )

    @staticmethod
    def document_type_token(document_type: str):
        if document_type == "insurance_card":
            return create_token(ServiceURL.document_type, "64290-0")
        elif document_type == "medical_record":
            return create_token(ServiceURL.document_type, "34117-2")
        elif document_type == "clinical_note":
            return create_token(ServiceURL.document_type, "55110-1")
        else:
            return document_type

    @staticmethod
    def service_request_code():
        return create_coding_clause(
            ServiceURL.service_request_code,
            "103693007",
            "Diagnostic procedure (procedure)",
        )

    @staticmethod
    def practitioner_code(practition: str):
        if practition == "doctor":
            return create_coding_clause(ServiceURL.practition_type, "doctor")
        elif practition == "nurse":
            return create_coding_clause(ServiceURL.practition_type, "nurse")
        raise TypeError()

    @staticmethod
    def communication(language: str):
        if language == "ja":
            return create_coding_clause(
                ServiceURL.communication_code, language, "Japanese"
            )
        elif language == "en":
            return create_coding_clause(
                ServiceURL.communication_code, language, "English"
            )
        raise TypeError()

    @staticmethod
    def enconuter():
        return create_coding_clause(ServiceURL.encounter_code, "HH", "home health")
