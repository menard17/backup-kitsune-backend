PRACTITIONER_DATA = {
    "resourceType": "Practitioner",
    "active": True,
    "name": [{"family": "Test", "given": ["Cool"], "prefix": ["Dr"]}],
}

PATIENT_DATA = {
    "resourceType": "Patient",
    "id": "example",
    "active": True,
    "name": [{"use": "official", "family": "Chalmers", "given": ["Peter", "James"]}],
    "gender": "male",
    "birthDate": "1990-01-01",
    "deceasedBoolean": False,
    "address": [
        {
            "use": "home",
            "type": "both",
            "text": "534 Erewhon St PeasantVille, Rainbow, Vic  3999",
            "line": ["534 Erewhon St"],
            "city": "PleasantVille",
            "district": "Rainbow",
            "state": "Vic",
            "postalCode": "3999",
            "period": {"start": "1974-12-25"},
        }
    ],
}
