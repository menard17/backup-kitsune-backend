Feature: Patients
    Scenario: Create Patients
        Given a patient
        When patient get call is called
        Then patient returns correct non-updated birthday format: 1990-01-01
    Scenario: Update birthday for patient
        Given a patient
        When patient updates birthday to 2000-01-01
        Then patient returns correct updated birthday format: 2000-01-01
