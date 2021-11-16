Feature: Document References
    Scenario: A patient can create document reference
        Given patient A
        Given patient B
        Given a doctor
        When patient A creates a document reference
        Then patient A can access the document reference
        Then doctor can access the document reference
        Then patient B cannot access the document reference
