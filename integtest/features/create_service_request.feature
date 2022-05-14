Feature: Process Serivce Request
    Scenario: Patient can see in-coming nurse's visit and Nurse can view service request
        Given a patient
        And a doctor
        And a nurse
        And an appointment
        When the doctor creates an encounter
