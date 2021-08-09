from flask import request, Blueprint, Response
from middleware import jwt_authenticated

from fhir.resources import construct_fhir_element
from adapters.fhir_store import ResourceClient
from slots.slots_service import SlotService

appointment_blueprint = Blueprint("appointments", __name__, url_prefix="/appointments")


@appointment_blueprint.route("/", methods=["POST"])
@jwt_authenticated()
def book_appointment():
    request_body = request.get_json()
    role_id = request_body.get("practitioner_role_id")
    patient_id = request_body.get("patient_id")
    start = request_body.get("start")
    end = request_body.get("end")

    if role_id is None:
        return Response(status=400, response="missing param: practitioner_role_id")
    if request.claims["role"] == "Patient" and patient_id != request.claims["role_id"]:
        return Response(
            status=401, response="could only book appointment for the patient"
        )
    if start is None:
        return Response(status=400, response="missing param: start")
    if end is None:
        return Response(status=400, response="missing param: end")

    resource_client = ResourceClient()
    slot_service = SlotService(resource_client)
    err, slot = slot_service.create_slot_for_practitioner_role(
        role_id,
        start,
        end,
        "busy",
    )

    if err is not None:
        return Response(status=400, response=err.args[0])

    appointment_data = {
        "resourceType": "Appointment",
        "status": "booked",
        "description": "Booking practitioner role",
        "start": start,
        "end": end,
        "serviceType": [
            {
                "coding": [
                    {
                        "system": "http://hl7.org/fhir/valueset-service-type.html",
                        "code": "540",
                        "display": "Online Service",
                    }
                ]
            }
        ],
        "serviceCategory": [
            {
                "coding": [
                    {
                        "system": "http://hl7.org/fhir/valueset-service-category.html",
                        "code": "17",
                        "display": "General Practice",
                    }
                ]
            }
        ],
        "slot": [{"reference": f"Slot/{slot.id}"}],
        "participant": [
            {
                "actor": {
                    "reference": f"Patient/{patient_id}",
                },
                "required": "required",
                "status": "accepted",
            },
            {
                "actor": {
                    "reference": f"PractitionerRole/{role_id}",
                },
                "required": "required",
                "status": "accepted",
            },
        ],
    }
    appointment = construct_fhir_element("Appointment", appointment_data)
    appointment = resource_client.create_resource(appointment)
    return Response(status=202, response=appointment.json())
