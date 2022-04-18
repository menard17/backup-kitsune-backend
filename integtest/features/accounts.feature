Feature: Cancel Account
    Scenario: Account is cancelled
        Given a doctor
        And a patient
        And a back-office staff
        And an appointment
        And an encounter
        When account status is correctly set: active
        And the payment is cancelled
        Then account status is correctly set: inactive
    Scenario: Account is cancelled after charged
        Given a doctor
        And a patient
        And a back-office staff
        And an appointment
        And an encounter
        When account status is correctly set: active
        And the charging is failed
        And the payment is cancelled
        Then account status is correctly set: inactive
