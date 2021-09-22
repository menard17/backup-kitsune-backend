Feature: Practitioner Role can be updated
    Scenario: Doctor can update his/her working hour
        Given a doctor
        When the doctor updates the working hour
        Then the working hour is updated
