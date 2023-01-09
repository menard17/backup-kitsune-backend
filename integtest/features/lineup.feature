Feature: Patient Lineup
    Scenario: Create a list for lineup
        Given an admin
        And a doctor
        And a patient
        When the admin creates a list
        Then the doctor can see all lists
        And the doctor can see the list
        And the patient cannot see all lists
        And the patient cannot see the list
        And the patient can see the number of item in the list: 0
        And inactivate doctor
    Scenario: Patients can join and remove from the lineup
        Given an admin
        And a patient
        And a patient B
        When the admin creates a list
        Then the patient can join the lineup
        And the patientB can also join the lineup
        And the patient can see the number of item in the list: 2
        And the patient can remove from the lineup
    Scenario: Optimistic Locking the List
        Given an admin
        When the admin creates a list
        And multiple patients trying to join the lineup at the same time
        Then not all can successfully join
