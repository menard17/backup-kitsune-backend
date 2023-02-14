from datetime import datetime
from uuid import UUID

from adapters.fire_store import FireStoreClient

CALLING_STATUS = "calling"
CREATED_STATUS = "created"
PATIENT_CALL_LOGS = "patient_call_logs"


class PatientCallLogsService:
    def __init__(self, firestore_client=None):
        self.firestore_client = firestore_client or FireStoreClient()

    def upsert_call_docs(self, appointment_id: UUID, patient_id: UUID) -> tuple:
        call_ref = self.firestore_client.get_collection(PATIENT_CALL_LOGS)
        call_log_collection = call_ref.where(
            "appointment_id", "==", appointment_id
        ).stream()
        call_log_data = [{**doc.to_dict(), "id": doc.id} for doc in call_log_collection]

        try:
            if call_log_data:
                for log in call_log_data:
                    self.firestore_client.update_value(
                        PATIENT_CALL_LOGS, log["id"], {"status": CALLING_STATUS}
                    )
            else:
                value = {
                    "patient_id": patient_id,
                    "status": CREATED_STATUS,
                    "appointment_id": appointment_id,
                    "timestamp": datetime.now(),
                }
                self.firestore_client.add_value(
                    PATIENT_CALL_LOGS, value, appointment_id
                )
            return None, "Successfully saved call logs."
        except Exception as err:
            return f"Error while saving call logs: {err}", None
