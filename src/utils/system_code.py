from typing import TypedDict


class ServiceURL:
    service_type = "http://hl7.org/fhir/valueset-service-type.html"
    service_category = "http://hl7.org/fhir/codesystem-service-category.html"
    appointment_type = "http://terminology.hl7.org/CodeSystem/v2-0276"
    service_request_code = "http://snomed.info/sct"
    practition_type = "http://terminology.hl7.org/CodeSystem/practitioner-role"
    communication_code = "urn:ietf:bcp:47"
    document_type = "http://loinc.org"


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


class SystemCode:
    @staticmethod
    def online_service():
        return create_coding_clause(ServiceURL.service_type, "540", "Online Service")

    @staticmethod
    def home_visit():
        return create_coding_clause(ServiceURL.service_type, "497", "Home Visits")

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
        elif service_type == "followup":
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
    def document_type_code(document_type: str):
        if document_type == "insurance_card":
            return create_coding_clause(
                ServiceURL.document_type, "64290-0", "Insurance Card"
            )
        elif document_type == "medical_record":
            return create_coding_clause(
                ServiceURL.document_type, "34117-2", "Medical Record"
            )
        else:
            return document_type

    @staticmethod
    def document_type_token(document_type: str):
        if document_type == "insurance_card":
            return create_token(ServiceURL.document_type, "64290-0")
        elif document_type == "medical_record":
            return create_token(ServiceURL.document_type, "34117-2")
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
