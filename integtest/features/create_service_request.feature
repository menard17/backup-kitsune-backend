Feature: Process Serivce Request
    Scenario: Doctor requesting pcr tests
        Given a patient
        And a doctor
        And an appointment
        When the doctor creates an encounter
        And the doctor creates a request for pcr test
        Then the doctor can fetch service request for the encounter
