Feature: Practitioners
    Scenario: Practitioner can be created correctly
        Given a user
        When a doctor is created
        Then the doctor can be searched by email
    Scenario: Practitioner cannot be created with wrong photo format
        Given a user
        When a doctor is tried to be created with jpeg
