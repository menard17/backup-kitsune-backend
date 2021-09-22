Feature: Create and Get Practitioner Role
    Scenario: The practitioner role can be created and get the info from api
        When a practitioner role is created
        Then the practitioner role can be found in all practitioners
        Then the practitioner role can be get by specifying the id
