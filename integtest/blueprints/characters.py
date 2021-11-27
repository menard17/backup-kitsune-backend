from typing import TypedDict


class Patient:
    def __init__(self, firebase_uid, patient):
        self.uid = firebase_uid
        self.fhir_data = patient


class Practitioner:
    def __init__(
        self, firebase_uid, practitioner_role=None, practitioner=None, schedule=None
    ):
        self.uid = firebase_uid
        self.fhir_data = practitioner_role
        self.fhir_practitioner_data = practitioner
        self.fhir_schedule = schedule


class Appointment(TypedDict):
    ...


class Encounter(TypedDict):
    ...


class Slot(TypedDict):
    ...


class DiagnosticReport(TypedDict):
    ...


class ServiceRequest(TypedDict):
    ...


class DocumentReference(TypedDict):
    ...
