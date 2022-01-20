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
