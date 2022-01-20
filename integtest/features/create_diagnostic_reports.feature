Feature: Diagnosis Report
    Scenario: Diagnostic report can be read by a patient and a doctor but not other patient
        Given patient A
        Given patient B
        Given a doctor
        When patient A makes an appointment
        When the doctor creates an encounter
        When the doctor creates a diagnostic report
        Then the doctor and patient A can access diagnostic report but patient B cannot access diagnostic report
    Scenario: Diagnostic report can be correctly updated
        Given patient A
        Given a doctor
        When patient A makes an appointment
        When the doctor creates an encounter
        When the doctor creates a diagnostic report
        When the doctor updates diagnostic report
        Then the diagnostic report gets updated
        Then the diagnostic report can be fetched by encounter id
    Scenario: Only one Diagnostic report can be created per encounter
        Given patient A
        Given a doctor
        When patient A makes an appointment
        When the doctor creates an encounter
        When the doctor creates a diagnostic report
        And the doctor creates another diagnostic report
        Then the diagnostic report can be fetched by encounter id
