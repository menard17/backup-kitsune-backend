def get_diagnostic_report_data(
    patient_id: str, practitioner_id: str, encounter_id: str
) -> dict:
    diagnostic_report = {
        "resourceType": "DiagnosticReport",
        "status": "final",
        "subject": {"reference": f"Patient/{patient_id}"},
        "encounter": {"reference": f"Encounter/{encounter_id}"},
        "performer": [{"reference": f"Practitioner/{practitioner_id}"}],
        "conclusion": "conclusion",
        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "448337001",
                    "display": "Telemedicine",
                }
            ],
        },
    }
    return diagnostic_report


def get_service_request_data(patient_id: str, doctor_id: str, nurse_id: str) -> dict:
    service_request = {
        "resourceType": "ServiceRequest",
        "status": "active",
        "intent": "order",
        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "103693007",
                    "display": "Diagnostic procedure (procedure)",
                }
            ],
            "text": "Colonoscopy",
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "requester": {
            "reference": f"Practitioner/{doctor_id}",
            "display": "Dr. Beverly Crusher",
        },
        "performer": [
            {"reference": f"Practitioner/{nurse_id}", "display": "Dr Adam Careful"}
        ],
    }
    return service_request


def get_encounter_data(
    patient_id: str, practitioner_id: str, appointment_id: str
) -> dict:
    encounter = {
        "resourceType": "Encounter",
        "status": "in-progress",
        "appointment": [{"reference": f"Appointment/{appointment_id}"}],
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "HH",
            "display": "home health",
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "participant": [
            {
                "individual": {
                    "reference": f"Practitioner/{practitioner_id}",
                },
            }
        ],
    }
    return encounter
