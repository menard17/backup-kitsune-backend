Feature: Claims
    Scenario: Practitioners can see all patients
        Given a doctor
        Then all patients can be access by the practitioner

    Scenario: Patients can only see themselves
        Given a patient
        Then only one patient can be accessed
