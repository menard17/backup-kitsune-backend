Feature: Encounters
    Scenario: Doctor can update the encounter
        Given a doctor
        Given patient A
        When patient A makes an appointment
        When the doctor creates an encounter
        When the doctor starts the encounter
        Then the doctor can finish the encounter
        Then patient A cannot change the status of encounter

    Scenario: Patient can only see themselves for encounters but doctor can see all
        Given a doctor
        Given patient A
        Given patient B
        When patient A makes an appointment
        When the doctor creates an encounter
        Then patient A can see the encounter but patient B cannnot see the encounter
        Then patient A can see encounter by appointment id
