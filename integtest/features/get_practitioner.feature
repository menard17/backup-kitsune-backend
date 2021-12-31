Feature: Get Practitioner Roles
    Scenario: Patient can get all doctors
        Given a doctor
        Given a nurse
        Given a patient
        Then the patient can fetch all doctors info
        Then the patient can fetch all nurses info
