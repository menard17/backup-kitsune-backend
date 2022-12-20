Feature: Update Patients
    Scenario: Update patient without any changes
        Given a patient
        Given a practitioner
        When practitioner tries to update patient with empty request
        Then patient will remain to have the same value
    Scenario: Update name for patient
        Given a patient
        Given a practitioner
        When the practitioner updates patients name, gender, phone number, dob, and address
        Then patient returns correct updated profile
    Scenario: Add new ORCA Id
        Given a patient
        When orca id, 0, is added
        Then patient can have one orca id: 0
    Scenario: Add second ORCA Id
        Given a patient
        When orca id, 0, is added
        And orca id, 1, is added
        Then patient can have one orca id: 1
