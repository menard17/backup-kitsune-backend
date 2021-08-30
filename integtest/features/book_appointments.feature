Feature: Book Appointment
    Scenario: Patient can book an appointment
        Given a doctor
        Given a patient
        When the patient books a free time of the doctor
        Then an appointment is created
        Then the period would be set as busy slots
        Then the patient can see his/her own appointment

    Scenario: Patient no show
        Given a doctor
        Given a patient
        When the patient books a free time of the doctor
        When the patients end up not showing up so doctor set the appointment status as no show
        Then the appointment status is updated as no show
        Then frees the slot
