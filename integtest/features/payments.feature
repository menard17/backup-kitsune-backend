Feature: Create a payment
    Scenario: Patient is charged correctly
        Given a doctor
        And a patient
        And an appointment
        And an encounter
        When account status is correctly set: active
        And the payment is processed
        Then account status is correctly set: inactive
        And invoice status is correctly set: any balanced
    Scenario: Patient was not charged correctly
        Given a doctor
        And a patient
        And an appointment
        And an encounter
        When account status is correctly set: active
        And the charging is failed
        Then account status is correctly set: active
        And invoice status is correctly set: all cancelled
        And payment is charged manually
        And account status is correctly set: inactive
        And invoice status is correctly set: any balanced
