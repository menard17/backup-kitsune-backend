from adapters.fhir_store import ResourceClient
from fhir.resources.patient import Patient
from firebase_admin import auth
from flask import Blueprint, Response, request
from utils.middleware import jwt_authenticated, jwt_authorized


patients_blueprint = Blueprint("patients", __name__, url_prefix="/patients")


@patients_blueprint.route("/<patient_id>", methods=["GET"])
@jwt_authenticated()
@jwt_authorized("/Patient/{patient_id}")
def get_patient(patient_id: str) -> dict:
    return Controller().get_patient(patient_id)


@patients_blueprint.route("/", methods=["GET"])
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def get_patients() -> dict:
    return Controller().get_patients()


@patients_blueprint.route("/", methods=["POST"])
@jwt_authenticated()
def create_patient():
    return Controller().create_patient(request)


@patients_blueprint.route("/<patient_id>", methods=["PATCH"])
@jwt_authenticated()
@jwt_authorized("/Patient/{patient_id}")
def patch_patient(patient_id: str) -> dict:
    return Controller().patch_patient(request, patient_id)


class Controller:
    def __init__(self, resource_client=None, firebase_auth=None):
        self.resource_client = resource_client or ResourceClient()
        self.firebase_auth = firebase_auth or auth

    def get_patient(self, patient_id: str) -> dict:
        """Returns details of a patient.

        :param patient_id: uuid for patient
        :type patient_id: str

        :rtype: dict
        """
        return self.resource_client.get_resource(patient_id, "Patient").dict()

    def get_patients(self) -> dict:
        """
        Returns details of all patients.
        Access to this function should be limited.
        Have to get FHIR's UUID from UID bypass for test.

        :rtype: dict
        """
        return self.resource_client.get_resources("Patient").dict()

    def create_patient(self, request) -> dict:
        """Returns the details of a patient created.

        This creates a patient in FHIR, as well as create a custom claims with
        Patient role in Firebase. Note that this function should only be called
        from the frontend client since everything assumes to use Firebase for
        authentication/authorization.

        Currently there is no check for duplicate entry or retryable, all
        assuming that the operations here succeeded without failure.

        :param request: the request for this operation
        :rtype: dict
        """
        # Only allow user with verified email to create patient
        if (
            "email_verified" not in request.claims
            or not request.claims["email_verified"]
        ):
            return Response(
                status=401,
                response="User not authorized due to missing email verification",
            )

        # First create a resource in FHIR and acquire a Patient resource with ID
        patient = Patient.parse_obj(request.get_json())
        patient = self.resource_client.create_resource(patient)

        # Then grant the custom claim for the caller in Firebase
        custom_claims = {}
        custom_claims["role"] = "Patient"
        custom_claims["role_id"] = patient.id
        self.firebase_auth.set_custom_user_claims(request.claims["uid"], custom_claims)

        return patient.dict(), 202

    def patch_patient(self, request, patient_id: str) -> dict:
        """Returns the details of an updated patient.

        This updates a patient in FHIR

        :param request: the request for this operation
        :param patient_id: uuid for patients id
        :rtype: dict
        """
        # First create a resource in FHIR and acquire a Patient resource with ID
        patient = request.get_json()
        patient = self.resource_client.patch_resource(patient_id, "Patient", patient)

        return patient.dict(), 202
