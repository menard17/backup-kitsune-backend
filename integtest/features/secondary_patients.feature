Feature: Secondary Patients
    Scenario: Create a secondary patient
        Given a primary patient
        And a secondary patient
        Then primary patient can get the secondary patient data
        And primary patient can search consents granted by the secondary patient
    Scenario: Primary patient can fetch all secondary patients data
        Given a primary patient
        And a secondary patient
        And another secondary patient
        Then primary patient can get the list of secondary patients
        And primary patient can get the appointments of each secondary patient
    Scenario: Primary patient can update secondary patients data
        Given a primary patient
        And a secondary patient
        And a doctor
        Then primary patient can update secondary patient information
        And primary patient can create insurance for the secondary patient
        And primary patient can book appointment for the seondary patient
