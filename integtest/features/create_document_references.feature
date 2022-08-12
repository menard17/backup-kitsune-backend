Feature: Document References
    Scenario: A patient can create document reference
        Given a user
        And patient A
        And patient B
        And patient C
        And doctor D
        And doctor E is created with the same user as patientC
        When patient A creates a document reference
        Then patient A, the creator, can access the document reference
        And patient B, another patient, cannot access the document reference
        And doctor D can access the document reference
        And doctor E, who is also a patient, can access the document reference
    Scenario: A practitioner creates clinical note
        Given a user
        And patient A
        And doctor D
        When patient A creates an appointment with doctor D
        And patient A creates different appointment with doctor D
        And doctor D creates an encounter
        And doctor D creates another encounter
        And doctor D creates three clinical note for patient A
        And doctor D creates three clinical note for patient A
        And doctor D creates different clinical note for patient A
        Then doctor D can access two clinical note
