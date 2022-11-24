from datetime import datetime, timedelta, timezone

from fhir.resources.appointment import Appointment
from fhir.resources.encounter import Encounter
from fhir.resources.medicationrequest import MedicationRequest
from fhir.resources.patient import Patient
from fhir.resources.servicerequest import ServiceRequest

from adapters.fire_store import FireStoreClient
from services.appointment_service import AppointmentService
from services.medication_request_service import MedicationRequestService
from services.patient_service import PatientService
from services.service_request_service import ServiceRequestService

FINISHED = "finished"
INITIAL_STATUS = "unassigned"
JST = timezone(timedelta(hours=+9), "JST")
DATE_FORMATTER = "%Y%m%d"
COLLECTION = "encounters"


class EncounterCollection:
    """
    Encounter collection for FireStore
    """

    def __init__(
        self,
        appointment: Appointment,
        service_request: ServiceRequest,
        patient: Patient,
        medication_request: MedicationRequest,
    ):
        self.appointment = appointment
        self.service_request = service_request
        self.patient = patient
        self.medication_request = medication_request

    def to_fire_store(self) -> dict:
        """Returns json of data matches with firestore schema
        :rtype: dict
        """
        return {
            "address": PatientService.get_address(self.patient),
            "area": "",
            "date": get_today(),
            "kana": PatientService.get_kana(self.patient),
            "name": PatientService.get_name(self.patient),
            "medicines": MedicationRequestService.get_medications(
                self.medication_request
            ),
            "phone": PatientService.get_phone(self.patient),
            "porter": "",
            "porterId": "",
            "status": INITIAL_STATUS,
            "tests": ServiceRequestService.get_service_request(self.service_request),
            "time": AppointmentService.get_start_time(self.appointment),
            "zip": PatientService.get_zip(self.patient),
        }


class FireStoreService:
    def sync_encounter_to_firestore(
        self,
        appointment: Appointment = None,
        encounter: Encounter = None,
        patient: Patient = None,
        medication_request: MedicationRequest = None,
        service_request: ServiceRequest = None,
    ):
        # Only encounter with finished state is syned to firebase store
        if encounter.status == FINISHED:
            encounter_collection = EncounterCollection(
                appointment, service_request, patient, medication_request
            )
            output = encounter_collection.to_fire_store()
            fire_store_client = FireStoreClient()
            fire_store_client.add_value(COLLECTION, output, encounter.id)


def get_today() -> str:
    """Returns current day in YYYYMMDD format
    :rtype: str
    """
    now = datetime.now(JST)
    return now.strftime(DATE_FORMATTER)
