Feature: Process Serivce Request
    Scenario: Patient can see in-coming nurse's visit and Nurse can view service request
        Given a patient
        Given a doctor
        Given a nurse
        Given an appointment
        When the doctor creates an encounter
