Feature: Practitioners
    Scenario: Practitioner can be created correctly
        Given a user
        When a doctor is created
        Then the doctor can be searched by email
