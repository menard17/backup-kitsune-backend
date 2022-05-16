Feature: Practitioner Role can be updated
    Scenario: Doctor can update his working hour
        Given a user
        And a doctor
        When the doctor updates the working hour
        Then the working hour is updated
    Scenario: Doctor can update only his English biography
        Given a user
        And a doctor
        When the doctor updates only English biography
        Then English biography is updated
    Scenario: available time can be empty
        Given a user
        And a doctor
        When the doctor updates available time empty
        Then the doctor has empty avaialbe time
    Scenario: Doctor can change their prefix to nurse
        Given a user
        And a doctor
        When the doctor updates to nurse
        Then the doctor is converted to have prefix for nurse
