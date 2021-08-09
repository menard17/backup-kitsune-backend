Feature: Book Appointment
    Scenario: Patient can book an appointment with the doctor
        Given a doctor
        Given a patient
        When the patient books a free time of the doctor
        Then an appointment is created
        Then the period would be set as busy slots
