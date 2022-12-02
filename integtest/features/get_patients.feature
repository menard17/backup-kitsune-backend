Feature: Get Patients
    Scenario: Get Patients with pagination
        Given a doctor
        Given multiple patients
        When the doctor calls get_patients endpoint
        Then return the first page of patients
        When the doctor gets the next page of the patients
        Then return the next page of patients
    Scenario: Get Patients filtered by name
        Given a doctor
        Given multiple patients with some specific names
        When the doctor calls get_patients endpoint with a name
        Then return the patients that match that name
