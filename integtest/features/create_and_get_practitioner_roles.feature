Feature: Create and Get Practitioner Role
    Scenario: The practitioner role can be created and get the info from api
        When a practitioner role is created
        Then the practitioner role can be found in all practitioners
        And the practitioner role can be get by specifying the id
    Scenario: Create practitioner role for normal appointment
        When a practitioner role is created with appointment visit type
        Then the practitioner role can be found in all practitioners
        And the practitioner role has the appointment visit type code
    Scenario: Create practitioner role for lineup patients
        When a practitioner role is created with walk-in visit type
        Then the practitioner role has the walk-in visit type code
        And the practitioner role can be found if specify walk-in visit type
