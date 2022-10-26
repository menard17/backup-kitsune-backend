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
    Scenario: Patient cannot get available slots outside doctor's serving date range
        Given a doctor with defined schedule
        Then the user cannot fetch available slots before the doctor's serving date range
        And the user cannot fetch available slots after the doctor's serving date range
    Scenario: Patient can get available slots apart except busy slots set by doctor
        Given a doctor with defined schedule
        When the practitioner role set the period to busy
        Then the user can fetch all available slots except busy slots
    Scenario: Patient can get available slots only after minimum delay booking
        Given a doctor with full schedule
        Then the user can only fetch slots after minimum delay booking
