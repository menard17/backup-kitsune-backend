def get_role(id: str) -> dict:
    role = {
        "resourceType": "PractitionerRole",
        "active": True,
        "period": {"start": "2001-01-01", "end": "2099-03-31"},
        "practitioner": {
            "reference": f"Practitioner/{id}",
            "display": "Dr Cool in test",
        },
        "availableTime": [
            {
                "daysOfWeek": ["mon", "tue", "wed"],
                "availableStartTime": "09:00:00",
                "availableEndTime": "16:30:00",
            },
            {
                "daysOfWeek": ["thu", "fri"],
                "availableStartTime": "09:00:00",
                "availableEndTime": "12:00:00",
            },
        ],
        "notAvailable": [
            {
                "description": "Adam will be on extended leave during May 2017",
                "during": {"start": "2017-05-01", "end": "2017-05-20"},
            }
        ],
        "availabilityExceptions": "Adam is generally unavailable on public holidays and during the Christmas/New Year break",
    }
    return role


def get_encounter(patient_id: str, practitioner_id: str, appointment_id: str) -> dict:
    encounter = {
        "resourceType": "Encounter",
        "status": "in-progress",
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
