Feature: Process Medication Request
    Scenario: Doctor requesting medications
        Given a patient
        And a doctor
        And an appointment
        When the doctor creates an encounter
        And the doctor creates medication requests
        Then the doctor can fetch medication requests for the encounter
