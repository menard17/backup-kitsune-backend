from adapters.fhir_store import ResourceClient
from fhir.resources.patient import Patient
from firebase_admin import auth
from flask import Blueprint, request
from middleware import jwt_authenticated, jwt_authorized


patients_blueprint = Blueprint("patients", __name__, url_prefix="/patients")


@patients_blueprint.route("/<patient_id>", methods=["GET"])
@jwt_authenticated()
@jwt_authorized("/Patient/{patient_id}")
def get_patient(patient_id: str) -> dict:
    """Returns details of a patient.

    :param patient_id: uuid for patient
    :type patient_id: str

    :rtype: Dictionary
    """
    resourse_client = ResourceClient()
    return resourse_client.get_resource(patient_id, "Patient").dict()


@patients_blueprint.route("/", methods=["GET"])
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def get_patients() -> dict:
    """
    Returns details of all patients.
    Access to this function should be limited.
    Have to get FHIR's UUID from UID bypass for test.

    :rtype: Dictionary
    """
    resourse_client = ResourceClient()
    return resourse_client.get_resources("Patient").dict()


@patients_blueprint.route("/", methods=["POST"])
@jwt_authenticated()
def create_patient():

    # First create a resource in FHIR and acquire an ID
    # Use a testing ID for now
    patient_id = "fake_id"

    # First grant the customer the role Patient
    custom_claims = {}
    custom_claims["role"] = "Patient"
    custom_claims["role_id"] = patient_id
    auth.set_custom_user_claims(request.claims["sub"], custom_claims)

    # Normally you should only return the created Patient JSON so that the
    # frontend can do additional operation with it, for now printing the
    # resulted claims for testing purpose
    user = auth.get_user(request.claims["uid"])
    return user.custom_claims, 202
