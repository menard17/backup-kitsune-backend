Feature: Practitioners
    Scenario: Practitioner can be created correctly
        Given a user
        When a doctor is created
        Then the doctor can be searched by email
    Scenario: Practitioner cannot be created with wrong photo format
        Given a user
        When a doctor is tried to be created with jpeg
    Scenario: Practitioner cannot be created with the same email
        Given a user
        And other user
        When a doctor is created
        Then second doctor cannot be created with user but with other user
    Scenario: Nurse is created with correct prefix
        Given a user
        When a nurse is created
        Then the nurse has correct prefix
