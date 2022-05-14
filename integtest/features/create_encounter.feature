Feature: Encounters
    Scenario: Doctor can update the encounter
        Given a doctor
        And patient A
        When patient A makes an appointment
        And the doctor creates an encounter
        And the doctor starts the encounter
        Then the doctor can finish the encounter
        And patient A cannot change the status of encounter

    Scenario: Patient can only see themselves for encounters but doctor can see all
        Given a doctor
        And patient A
        And patient B
        When patient A makes an appointment
        And the doctor creates an encounter
        Then patient A can see the encounter but patient B cannnot see the encounter
        And patient A can see encounter by appointment id

    Scenario: Appointment status is updated when encounter is created
        Given a doctor
        And patient A
        When patient A makes an appointment
        And the doctor creates an encounter
        Then appointment status is changed to fulfilled

    Scenario: Only one encounter per appointment
        Given a doctor
        And patient A
        When patient A makes an appointment
        And the doctor creates an encounter
        Then the doctor cannot create another encounter for the same appointment
