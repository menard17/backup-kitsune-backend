Feature: Get Practitioner Slots
    Scenario: Patient can get busy slots set by doctor
        Given a doctor with defined schedule
        When the practitioner role set the period to busy
        Then the user can fetch those busy slots
    Scenario: Patient can get available slots by doctor
        Given a doctor with defined schedule
        Then the user can fetch all available slots
    Scenario: Patient cannot get available slots outside doctor's schedule
        Given a doctor with defined schedule
        Then the user cannot fetch available slots outside doctor's schedule
    Scenario: Patient can get available slots apart except busy slots set by doctor
        Given a doctor with defined schedule
        When the practitioner role set the period to busy
        Then the user can fecth all available slots except busy slots
