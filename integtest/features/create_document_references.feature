Feature: Document References
    Scenario: A patient can create document reference
        Given a user
        Given patient A
        Given patient B
        Given patient C
        Given doctor D
        Given doctor E is created with the same user as patientC
        When patient A creates a document reference
        Then patient A, the creator, can access the document reference
        Then patient B, another patient, cannot access the document reference
        Then doctor D can access the document reference
        Then doctor E, who is also a patient, can access the document reference
