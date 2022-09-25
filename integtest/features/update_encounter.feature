Feature: Update Encounter
    Scenario: Cancel encounter should inactivate account
        Given a patient
        Given a practitioner
        When patient makes an appointment
        And the doctor creates an encounter
        When the doctor cancels the encounter
        Then account should be inactivated
