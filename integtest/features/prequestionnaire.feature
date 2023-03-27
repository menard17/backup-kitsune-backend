Feature: Prequestionnaire
    Scenario: Create a questionnaire for prequestionnaire
        Given an admin
        And a back-office staff
        And a doctor
        And a patient
        When the admin creates a prequestionnaire
        Then the back-office staff can see all prequestionnaires
        And the doctor can see the prequestionnaire
        And the patient can see all prequestionnaires
    Scenario: Staff can add and update and remove the questionnaire items
        Given an admin
        And a back-office staff
        And a patient
        When the admin creates a prequestionnaire
        Then the back-office staff can add new prequestionnaire question
        And the back-office staff can update a question in the prequestionnaire
        And the back-office staff can remove from a question in the prequestionnaire
        And the patient cannot add new prequestionnaire question
        And the patient cannot update a question in the prequestionnaire
        And the patient cannot remove from a question in the prequestionnaire
