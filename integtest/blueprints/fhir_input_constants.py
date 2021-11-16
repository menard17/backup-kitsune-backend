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

DOCUMENT_REFERENCE_DATA = {
    "resourceType": "DocumentReference",
    "status": "current",
    "date": "2018-12-24T09:43:41+11:00",
    "type": {"coding": [{"code": "34108-1", "display": "Outpatient Note"}]},
    "content": [
        {
            "attachment": {
                "contentType": "application/hl7-v3+xml",
                "language": "en-US",
                "url": "http://example.org/xds/mhd/Binary/07a6483f-732b-461e-86b6-edb665c45510",
                "size": 3654,
                "hash": "2jmj7l5rSw0yVb/vlWAYkK/YBwk=",
                "title": "Physical",
                "creation": "2005-12-24T09:35:00+11:00",
            },
            "format": {
                "system": "urn:oid:1.3.6.1.4.1.19376.1.2.3",
                "code": "urn:ihe:pcc:handp:2008",
                "display": "History and Physical Specification",
            },
        }
    ],
}
