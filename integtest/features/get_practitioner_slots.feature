Feature: Get Practitioner Slots
    Scenario: Patient can get busy slots set by doctor
        Given a doctor
        When the practitioner role set the period to busy
        Then the user can fetch those busy slots
