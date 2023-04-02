Feature: Book Appointment
    Scenario: Patient can book an appointment and see an encounter
        Given a doctor
        And a patient
        When the patient books a free time of the doctor: 0
        Then an appointment is created
        And the period would be set as busy slots
        And the patient can see his/her own appointment
        And the encounter is created
        And the doctor can see the appointment being booked
    Scenario: Patient no show
        Given a doctor
        And a patient
        When the patient books a free time of the doctor: 0
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
        When the patient books a free time of the doctor: 0
        Then patient cannot book an appointment
        And patient cancels the appointment
        And patient can book an appointment
    Scenario: Appointment can be seen by a doctor who is patient
        Given a user
        And a doctor is created with the same user as patient A
        And patient A
        And patient B
        When an appointment is created by patient B
        Then the doctor can see list of appointments
    Scenario: Appointment can be booked for time which is a freed slot
        Given a doctor
        And a patient
        When a time has been blocked by doctor and then freed
        Then the patient can book at the same start time
    Scenario: Appointments can be paginated
        Given a doctor
        And a patient
        When the patient books a free time of the doctor: 0
        Then an appointment is created
        When the patient books another free time of the doctor
        Then an appointment is created
        When pagination count being 1
        Then the doctor can see the first appointment page
        And the doctor can see the next appointment page
    Scenario: Appointment can be filter by specified status
        Given a doctor
        And a patient
        When the patient books a free time of the doctor: 1
        And the patient books a free time of the doctor again: 2
        Then patient cancels the appointment
        And the doctor can get booked appointments
        And the doctor can get cancelled appointments
    Scenario: All appointment can be seen by back office staff
        Given a doctor
        And a patient
        And a back-office staff
        When the patient books a free time of the doctor: 0
        Then the back-office staff can see the booked appointment
    Scenario: One doctor picks up the appointment in list
        Given a patient
        And a doctor
        And an admin
        When the admin creates a list
        Then the patient can join the lineup
        When the doctor updates the visit type to walk-in
        Then the doctor picks up the appointment
        And the patient is no longer on the list
    Scenario: Two Doctor picks up the appointment and one doctor cannot pick
        Given a patient
        And a doctor
        And a doctor B
        And an admin
        When the admin creates a list
        Then the patient can join the lineup
        When the doctor updates the visit type to walk-in
        Then the doctor picks up the appointment
        When the doctor B updates the visit type to walk-in
        Then the doctor B cannot pick up the appointment
    Scenario: Two Doctor picks up the appointment
        Given a patient
        And a patient A
        And a doctor
        And a doctor B
        And an admin
        When the admin creates a list
        Then the patient can join the lineup
        And the patinet A can join the lineup
        When the doctor updates the visit type to walk-in
        Then the doctor picks up the appointment
        When the doctor B updates the visit type to walk-in
        Then the doctor B picks up the appointment
    Scenario: Doctor picks up the appointment outside of the avaible hours
        Given a patient
        And a doctor
        And an admin
        When the admin creates a list
        Then the patient can join the lineup
        When the doctor updates the visit type to walk-in and change avaible time
        Then the doctor cannot pick up the appointment outside of the avaible time
    Scenario: One doctor picks up and cancel the appointment in list
        Given a patient
        And a doctor
        And an admin
        When the admin creates a list
        Then the patient can join the lineup
        When the doctor updates the visit type to walk-in
        Then the doctor picks up the appointment
        When the doctor cancels the appointment
        Then the appointment status is updated as cancelled
