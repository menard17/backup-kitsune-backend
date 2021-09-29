Feature: Practitioners
    Scenario: Practitioner Id can be fetched by Email
        Given a user
        When a doctor is created
        Then the doctor can be searched by email
