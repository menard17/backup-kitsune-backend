from flask import Blueprint
from adapters import fhir_store
from middleware import jwt_authenticated

patients_blueprint = Blueprint("patients", __name__, url_prefix="/patients")


@patients_blueprint.route("/<user_id>", methods=["GET"])
@jwt_authenticated
def get_patient(user_id):
    # Have to get FHIR's UUID from UID somehow, bypassing for testing only
    patient_id = user_id
    return fhir_store.get_resource("Patient", patient_id).dict()
