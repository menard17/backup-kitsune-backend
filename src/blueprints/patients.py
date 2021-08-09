from adapters.fhir_store import ResourceClient
from fhir.resources.patient import Patient
from firebase_admin import auth
from flask import Blueprint, Response, request
from middleware import jwt_authenticated, jwt_authorized


patients_blueprint = Blueprint("patients", __name__, url_prefix="/patients")


@patients_blueprint.route("/<patient_id>", methods=["GET"])
@jwt_authenticated()
@jwt_authorized("/Patient/{patient_id}")
def get_patient(patient_id: str) -> dict:
    """Returns details of a patient.

    :param patient_id: uuid for patient
    :type patient_id: str

    :rtype: dict
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

    :rtype: dict
    """
    resourse_client = ResourceClient()
    return resourse_client.get_resources("Patient").dict()


@patients_blueprint.route("/", methods=["POST"])
@jwt_authenticated()
def create_patient():
    """Returns the details of a patient created.

    This creates a patient in FHIR, as well as create a custom claims with
    Patient role in Firebase. Note that this function should only be called
    from the frontend client since everything assumes to use Firebase for
    authentication/authorization.

    Currently there is no check for duplicate entry or retryable, all assuming
    that the operations here succeeded without failure.

    :rtype: dict
    """
    # Only allow user with verified email to create patient
    if "email_verified" not in request.claims or not request.claims["email_verified"]:
        return Response(
            status=401, response="User not authorized due to missing email verification"
        )

    # First create a resource in FHIR and acquire a Patient resource with ID
    resourse_client = ResourceClient()
    patient = Patient.parse_obj(request.get_json())
    patient = resourse_client.create_resource(patient)

    # Then grant the custom claim for the caller in Firebase
    custom_claims = {}
    custom_claims["role"] = "Patient"
    custom_claims["role_id"] = patient.id
    auth.set_custom_user_claims(request.claims["uid"], custom_claims)

    return patient.dict(), 202


@patients_blueprint.route("/<patient_id>", methods=["PATCH"])
@jwt_authenticated()
@jwt_authorized("/Patient/{patient_id}")
def patch_patient(patient_id: str) -> dict:
    """Returns the details of an updated patient.
    This updates a patient in FHIR
    :param patient_id: uuid for patients id
    :rtype: dict
    """
    # First create a resource in FHIR and acquire a Patient resource with ID
    resourse_client = ResourceClient()
    patient = request.get_json()
    patient = resourse_client.patch_resource(patient_id, "Patient", patient)

    return patient.dict(), 202
