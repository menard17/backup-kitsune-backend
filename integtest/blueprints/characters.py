class Patient:
    def __init__(self, firebase_uid, patient):
        self.uid = firebase_uid
        self.fhir_data = patient


class Doctor:
    def __init__(self, firebase_uid, practitioner_role=None, practitioner=None):
        self.uid = firebase_uid
        self.fhir_data = practitioner_role
        self.fhir_practitioner_data = practitioner
