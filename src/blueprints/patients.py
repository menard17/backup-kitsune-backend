import json

from fhir.resources.patient import Patient
from flask import Blueprint, Response, request

from adapters.fhir_store import ResourceClient
from utils import role_auth
from utils.datetime_encoder import datetime_encoder
from utils.middleware import jwt_authenticated, jwt_authorized

patients_blueprint = Blueprint("patients", __name__, url_prefix="/patients")


@patients_blueprint.route("/<patient_id>", methods=["GET"])
@jwt_authenticated()
@jwt_authorized("/Patient/{patient_id}")
def get_patient(patient_id: str) -> Response:
    return Controller().get_patient(patient_id)


@patients_blueprint.route("/", methods=["GET"])
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def get_patients() -> Response:
    return Controller().get_patients()


@patients_blueprint.route("/", methods=["POST"])
@jwt_authenticated()
def create_patient() -> tuple:
    return Controller().create_patient(request)


@patients_blueprint.route("/<patient_id>", methods=["PATCH"])
@jwt_authenticated()
@jwt_authorized("/Patient/{patient_id}")
def patch_patient(patient_id: str) -> tuple:
    return Controller().patch_patient(request, patient_id)


class Controller:
    def __init__(self, resource_client=None):
        self.resource_client = resource_client or ResourceClient()

    def get_patient(self, patient_id: str) -> Response:
        """Returns details of a patient.

        :param patient_id: uuid for patient
        :type patient_id: str

        :rtype: Response
        """
        patient = self.resource_client.get_resource(patient_id, "Patient")
        return Response(
            status=200, response=json.dumps({"data": datetime_encoder(patient.dict())})
        )

    def get_patients(self) -> Response:
        """
        Returns details of all patients.
        Access to this function should be limited.
        Have to get FHIR's UUID from UID bypass for test.

        :rtype: Response
        """
        patients = self.resource_client.get_resources("Patient")
        return Response(
            status=200, response=json.dumps({"data": datetime_encoder(patients.dict())})
        )

    def create_patient(self, request) -> tuple:
        """Returns the details of a patient created.

        This creates a patient in FHIR, as well as create a custom claims with
        Patient role in Firebase. Note that this function should only be called
        from the frontend client since everything assumes to use Firebase for
        authentication/authorization.

        Currently there is no check for duplicate entry or retryable, all
        assuming that the operations here succeeded without failure.

        :param request: the request for this operation
        :rtype: (dict, int)
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
        role_auth.grant_role(request.claims, "Patient", patient.id)

        return patient.dict(), 201

    def patch_patient(self, request, patient_id: str) -> tuple:
        """Returns the details of an updated patient.

        This updates a patient in FHIR

        :param request: the request for this operation
        :param patient_id: uuid for patients id
        :rtype: (dict, int)
        """
        # First create a resource in FHIR and acquire a Patient resource with ID
        patient = request.get_json()
        patient = self.resource_client.patch_resource(patient_id, "Patient", patient)

        return datetime_encoder(patient.dict()), 200
