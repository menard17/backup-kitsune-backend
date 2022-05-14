Feature: Book Appointment
    Scenario: Patient can book an appointment
        Given a doctor
        And a patient
        When the patient books a free time of the doctor
        Then an appointment is created
        And the period would be set as busy slots
        And the patient can see his/her own appointment
        And the doctor can see the appointment being booked
    Scenario: Patient no show
        Given a doctor
        And a patient
        When the patient books a free time of the doctor
        And the patients end up not showing up so doctor set the appointment status as no show
        Then the appointment status is updated as no show
        And frees the slot
    Scenario: Yesterday's appointment should not show up
        Given a doctor
        And a patient
        When yesterday appointment is created
        Then no appointment should show up
    Scenario: Patient cancels an appointment
        Given a doctor
        And a patient
        When the patient books a free time of the doctor
        Then patient cannot book an appointment
        And patient cancels the appointment
        And patient can book an appointment
    Scenario: Appointment can be seen by a doctor who is patient
        Given a user
        And a doctor is created with the same user as patientA
        And patientA
        And patientB
        When an appointment is created by patientB
        Then the doctor can see list of appointments
    Scenario: Appointment can be booked for time which is a freed slot
        Given a doctor
        And a patient
        When a time has been blocked by doctor and then freed
        Then the patient can book at the same start time
