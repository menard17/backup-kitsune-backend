from typing import TypedDict


class Patient:
    def __init__(self, firebase_uid, patient):
        self.uid = firebase_uid
        self.fhir_data = patient


class Practitioner:
    def __init__(
        self,
        firebase_uid,
        practitioner_role=None,
        practitioner_id=None,
        practitioner_name=None,
    ):
        self.uid = firebase_uid
        self.fhir_data = practitioner_role
        self.practitioner_id = practitioner_id
        self.practitioner_name = practitioner_name


class User:
    def __init__(self, uid, email, token):
        self.uid = uid
        self.email = email
        self.token = token


class Account(TypedDict):
    ...


class Appointment(TypedDict):
    ...


class Encounter(TypedDict):
    ...


class Invoice(TypedDict):
    ...


class Slot(TypedDict):
    ...


class DiagnosticReport(TypedDict):
    ...


class ServiceRequest(TypedDict):
    ...


class DocumentReference(TypedDict):
    ...
