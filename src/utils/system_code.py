from typing import TypedDict


class ServiceURL:
    service_type = "http://hl7.org/fhir/valueset-service-type.html"
    service_category = "http://hl7.org/fhir/codesystem-service-category.html"
    appointment_type = "http://terminology.hl7.org/CodeSystem/v2-0276"
    service_request_code = "http://snomed.info/sct"
    practitioner_type = "http://terminology.hl7.org/CodeSystem/practitioner-role"
    practitioner_visit_type = (
        "https://www.notion.so/umed-group/code-system/practitioner-role"
    )
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


class ExtensionContent(TypedDict):
    url: ServiceURL
    valueString: str


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


def create_extension(url: ServiceURL, value_string: str) -> ExtensionContent:
    result = {"url": url, "valueString": value_string}
    return result


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
        elif document_type == "medical_card":
            return create_coding_clause(
                ServiceURL.document_type, "00001-1", "Medical Card"
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
        elif document_type == "medical_card":
            return create_token(ServiceURL.document_type, "00001-1")
        else:
            return document_type

    @staticmethod
    def service_request_code(request, display):
        if not request and not display:
            return create_coding_clause(
                ServiceURL.service_request_code,
                "103693007",
                "Diagnostic procedure (procedure)",
            )
        else:
            return create_coding_clause("ServiceRequest", request, display)

    @staticmethod
    def practitioner_code(role_type: str):
        if role_type == "doctor":
            return create_coding_clause(ServiceURL.practitioner_type, "doctor")
        elif role_type == "nurse":
            return create_coding_clause(ServiceURL.practitioner_type, "nurse")
        elif role_type == "staff":
            return create_coding_clause(
                ServiceURL.practitioner_type,
                "224608005",
                "Administrative healthcare staff",
            )
        raise TypeError()

    @staticmethod
    def visit_type_code(visit_type: str):
        if visit_type == "walk-in":
            return create_coding_clause(
                ServiceURL.practitioner_visit_type,
                "walk-in",
                "Walk In",
            )
        if visit_type == "appointment":
            return create_coding_clause(
                ServiceURL.practitioner_visit_type,
                "appointment",
                "Appointment",
            )
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

    @staticmethod
    def billing():
        return create_coding_clause(
            ServiceURL.encounter_code, "PBILLACCT", "patient billing account"
        )

    @staticmethod
    def payment_intent(payment_intent_id: str):
        return create_extension(ServiceURL.payment_url, payment_intent_id)
