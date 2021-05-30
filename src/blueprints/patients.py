from flask import Blueprint, request, jsonify
from adapters import fhir_store
from middleware import jwt_authenticated

patients_blueprint = Blueprint("patients", __name__, url_prefix="/patients")


@patients_blueprint.route("/<user_id>", methods=["GET"])
@jwt_authenticated
def get_patient(user_id):
    # Have to get FHIR's UUID from UID somehow, bypassing for testing only
    return fhir_store.get_patient(user_id).dict()
