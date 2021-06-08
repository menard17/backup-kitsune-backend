from flask import Blueprint
from adapters.fhir_store import ResourceClient
from middleware import jwt_authenticated
from fhir.resources.patient import Patient


patients_blueprint = Blueprint("patients", __name__, url_prefix="/patients")


@patients_blueprint.route("/<user_id>", methods=["GET"])
@jwt_authenticated
def get_patient(user_id: str) -> dict:
    """Returns details of a patient.
    Have to get FHIR's UUID from UID bypass for test.

    :param user_id: uuid for patient
    :type user_id: str

    :rtype: Dictionary
    """
    resourse_client = ResourceClient()
    return resourse_client.get_resource(user_id, Patient()).dict()


@patients_blueprint.route("/", methods=["GET"])
@jwt_authenticated
def get_patients() -> dict:
    """
    Returns details of all patients.
    Access to this function should be limited.
    Have to get FHIR's UUID from UID bypass for test.

    :rtype: Dictionary
    """
    resourse_client = ResourceClient()
    return resourse_client.get_resources(Patient()).dict()
