Feature: Practitioner Role can be updated
    Scenario: Doctor can update his working hour
        Given a doctor
        When the doctor updates the working hour
        Then the working hour is updated
    Scenario: Doctor can update only his English biography
        Given a doctor
        When the doctor updates only English biography
        Then English biography is updated
