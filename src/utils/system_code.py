from typing import TypedDict


class ServiceURL:
    service_type = "http://hl7.org/fhir/valueset-service-type.html"
    service_category = "http://hl7.org/fhir/codesystem-service-category.html"
    appointment_type = "http://terminology.hl7.org/CodeSystem/v2-0276"
    service_request_code = "http://snomed.info/sct"
    practition_type = "http://terminology.hl7.org/CodeSystem/practitioner-role"


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
