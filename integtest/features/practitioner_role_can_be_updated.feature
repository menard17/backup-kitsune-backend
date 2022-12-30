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
    Scenario: Doctor can change their start and end dates
        Given a user
        And a doctor
        When the doctor updates the start and end dates
        Then the start and end dates are updated
    Scenario: Doctor can change their start date without changing end date
        Given a user
        And a doctor
        When the doctor updates the start date
        Then the start date is updated but not the end date
    Scenario: Doctor can change their end date without changing start date
        Given a user
        And a doctor
        When the doctor updates the end date
        Then the end date is updated but not the start date
    Scenario: Doctor can change their end date without changing start date
        Given a user
        And a doctor
        When the doctor updates the end date
        Then the end date is updated but not the start date
    Scenario: Doctor can change their visit type to walk in
        Given a user
        And a doctor
        When the doctor updates the visit type to walk-in
        Then the visit type is updated to walk-in
    Scenario: Doctor can change their visit type to appointment
        Given a user
        And a doctor
        When the doctor updates the visit type to appointment
        Then the visit type is updated to appointment
