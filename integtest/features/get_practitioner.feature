Feature: Get Practitioner Roles
    Scenario: Patient can get all doctors
        Given a doctor
        And a nurse
        And a patient
        Then the patient can fetch all doctors info
        And the patient can fetch all nurses info
        And practitioner can be included in practitioner role
    Scenario: Patient cannot get inactive doctors
        Given a doctor
        And a patient
        When the doctor gets disabled
        Then the patient cannot fetch disabled doctor
