Feature: Orca
    Scenario: Put orca id on patient does not exist orca id
        Given a patient
        And a back-office staff
        When put orca id for patient details
        Then patient details have orca id and orca code
    Scenario: Orca id already exists and tries to update one
        Given a patient
        And a back-office staff
        When put orca id for patient details
        Then patient details have orca id and orca code
        When change orca id for patient already have orca id
        Then patient details have orca id and orca code
