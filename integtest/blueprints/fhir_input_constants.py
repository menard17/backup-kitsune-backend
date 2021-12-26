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
            "country": "US",
        }
    ],
}

DOCUMENT_REFERENCE_DATA = {
    "subject": "Patient/c696cd08-babf-4ec2-8b40-73ffd422d571",
    "document_type": "medical_record",
    "pages": [
        {
            "url": "http://example.org/xds/mhd/Binary/07a6483f-732b-461e-86b6-edb665c45510",
            "title": "Page 1",
        },
        {
            "url": "http://example.org/xds/mhd/Binary/07a6483f-732b-461e-86b6-edb665c45510",
            "title": "Page 2",
        },
        {
            "url": "http://example.org/xds/mhd/Binary/07a6483f-732b-461e-86b6-edb665c45510",
            "title": "Page 3",
        },
        {
            "url": "http://example.org/xds/mhd/Binary/07a6483f-732b-461e-86b6-edb665c45510",
            "title": "Page 4",
        },
    ],
}
