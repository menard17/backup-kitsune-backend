Feature: Process Serivce Request
    Scenario: Patient can see in-coming nurse's visit and Nurse can view service request
        Given a patient
        Given a doctor
        Given a nurse
        When the doctor creates an encounter
        When the doctor creates a diagnostic report
        When the doctor creates appointment for nurse with service request
        Then patient can fetch next appointment from doctor encounter
        Then the nurse can fethc service request with given id
