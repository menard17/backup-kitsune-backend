import uuid

from fhir.resources import construct_fhir_element

from adapters.fhir_store import ResourceClient
from utils.system_code import ServiceType, SystemCode


class AppointmentService:
    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def create_appointment_for_practitioner_role(
        self,
        role_id,
        start,
        end,
        slot_id,
        patient_id,
        service_type: ServiceType,
        service_request_id,
        appointment_uuid: str = None,
    ):
        appointment_jsondict = {
            "resourceType": "Appointment",
            "status": "booked",
            "description": "Booking practitioner role",
            "start": start,
            "end": end,
            "serviceType": [{"coding": [SystemCode.online_service()]}],
            "serviceCategory": [{"coding": [SystemCode.general_practice()]}],
            "appointmentType": {
                "coding": [SystemCode.appointment_service_type(service_type)]
            },
            "slot": [{"reference": slot_id}],
            "participant": [
                {
                    "actor": {
                        "reference": patient_id,
                    },
                    "required": "required",
                    "status": "accepted",
                },
                {
                    "actor": {
                        "reference": role_id,
                    },
                    "required": "required",
                    "status": "accepted",
                },
            ],
        }

        if service_request_id is not None:
            appointment_jsondict["basedOn"] = [
                {
                    "reference": service_request_id,
                    "display": "Instruction",
                }
            ]
        appointment = construct_fhir_element(
            appointment_jsondict["resourceType"], appointment_jsondict
        )
        appointment = self.resource_client.get_post_bundle(
            appointment, appointment_uuid
        )
        return None, appointment

    def update_appointment_status(self, appointment_id: uuid, status: str):
        appointment_response = self.resource_client.get_resource(
            appointment_id, "Appointment"
        )
        appointment_response.status = status
        appointment = construct_fhir_element("Appointment", appointment_response)
        appointment = self.resource_client.get_put_bundle(appointment, appointment_id)

        return None, appointment
