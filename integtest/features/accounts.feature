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
    Scenario: All accounts can be searched
        Given a patient
        And a back-office staff
        When account can be created by the staff
        And account can be created by the staff
        Then all accounts can be searched
