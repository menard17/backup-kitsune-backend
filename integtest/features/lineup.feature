Feature: Patient Lineup
    Scenario: Create a list for lineup
        Given an admin
        And a patient
        When the admin create a list
        Then the patient can see all lists
        And the patient can see the list
    Scenario: Patients can join and remove from the lineup
        Given an admin
        And a patient
        And a patient B
        When the admin create a list
        Then the patient can join the lineup
        And the patientB can also join the lineup
        And the patient can remove from the lineup
    Scenario: Optimistic Locking the List
        Given an admin
        When the admin create a list
        And multiple patients trying to join the lineup at the same time
        Then not all can successfully join
