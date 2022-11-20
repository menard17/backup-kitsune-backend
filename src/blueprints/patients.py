import json

from fhir.resources.consent import Consent
from fhir.resources.patient import Patient
from flask import Blueprint, Request, Response, request

from adapters.fhir_store import ResourceClient
from json_serialize import json_serial
from services.patient_service import PatientService
from utils import role_auth
from utils.datetime_encoder import datetime_encoder
from utils.middleware import jwt_authenticated, jwt_authorized

DEFAULT_PAGE_COUNT = "300"

patients_blueprint = Blueprint("patients", __name__, url_prefix="/patients")


@patients_blueprint.route("/<patient_id>", methods=["GET"])
@jwt_authenticated()
@jwt_authorized("/Patient/{patient_id}")
def get_patient(patient_id: str) -> Response:
    return PatientController().get_patient(request, patient_id)


@patients_blueprint.route("/", methods=["GET"])
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def get_patients() -> Response:
    if next_link := request.args.get("next_link"):
        return PatientController().link(next_link)
    return PatientController().get_patients(request)


@patients_blueprint.route("/", methods=["POST"])
@jwt_authenticated()
def create_patient() -> tuple:
    return PatientController().create_patient(request)


@patients_blueprint.route("/<patient_id>", methods=["PATCH"])
@jwt_authenticated()
@jwt_authorized("/Patient/{patient_id}")
def patch_patient(patient_id: str) -> tuple:
    return PatientController().patch_patient(request, patient_id)


@patients_blueprint.route("/<patient_id>", methods=["PUT"])
@jwt_authenticated()
@jwt_authorized("/Patient/{patient_id}")
def put_patients(patient_id: str) -> Response:
    return PatientController().update_patient(request, patient_id)


class PatientController:
    def __init__(self, resource_client=None, patient_service=None):
        self.resource_client = resource_client or ResourceClient()
        self.patient_service = patient_service or PatientService(self.resource_client)

    def link(self, link: str) -> Response:
        ok, err_resp = self.patient_service.check_link(link)
        if not ok:
            return err_resp

        patients = self.resource_client.link(link)
        return Response(
            status=200, response=json.dumps({"data": datetime_encoder(patients.dict())})
        )

    def get_patient(self, request: Request, patient_id: str) -> Response:
        """Returns details of a patient.

        :param patient_id: uuid for patient
        :type patient_id: str

        :rtype: Response
        """

        search_clause = [("_id", patient_id)]
        if (is_active := request.args.get("active")) is not None:
            search_clause.append(("active", is_active))
        patient = (
            self.resource_client.search("Patient", search_clause).entry[0].resource
        )

        return Response(
            status=200, response=json.dumps({"data": datetime_encoder(patient.dict())})
        )

    def get_patients(self, request: Request) -> Response:
        """
        Returns details of all patients.
        Access to this function should be limited.
        Have to get FHIR's UUID from UID bypass for test.

        :rtype: Response
        """
        count = request.args.get("count", DEFAULT_PAGE_COUNT)
        search_clause = []
        if (is_active := request.args.get("active")) is not None:
            search_clause.append(("active", is_active))
        search_clause.append(("_count", count))
        patients = self.resource_client.search("Patient", search_clause)
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

        # First time creation -> the primary account
        role = role_auth.extract_roles(request.claims)
        if role is None or "Patient" not in role:
            role_auth.grant_role(request.claims, "Patient", patient.id)
        else:
            # delegate the Firebase auth
            primary_patient_id = request.claims["roles"]["Patient"]["id"]
            role_auth.delegate_role(
                request.claims, "Patient", primary_patient_id, patient.id
            )

            # create the consent resource
            # ref: http://hl7.org/fhir/2021Mar/consent.html
            consent_data = {
                "resourceType": "Consent",
                "status": "active",
                "patient": {
                    "reference": f"Patient/{patient.id}",
                },
                "scope": {
                    "text": "all access",
                },
                "policyRule": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                            "code": "ACALL",
                        }
                    ]
                },
                "provision": {
                    "type": "permit",
                    "actor": [
                        {
                            "role": {
                                "text": "grantee",
                            },
                            "reference": {"reference": f"Patient/{primary_patient_id}"},
                        }
                    ],
                },
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                                "code": "ACALL",  # All access
                            }
                        ]
                    }
                ],
            }
            consent = Consent.parse_obj(consent_data)
            self.resource_client.create_resource(consent)

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

    def update_patient(self, request: Request, patient_id: str) -> Response:
        """Returns the response of the updated patient.

        This updates a patient in FHIR

        :param request: the request for this operation including body of put calls
        :type request: Request from flask
        :param patient_id: uuid for patient
        :type patient_id: str

        :rtype: Response

        Sample Request Body:
        {
            "family_name": "family name",
            "given_name": ["given name"],
            "gender": "male",
            "phone": "00011111111"
            "dob": "1990-01-01",
            "address": [{"country": "JP"}]
        }
        """
        request_body = request.get_json()
        family_name = request_body.get("family_name")
        given_name = request_body.get("given_name")
        phone = request_body.get("phone")
        gender = request_body.get("gender")
        dob = request_body.get("dob")
        address = request_body.get("address")

        err, patient = self.patient_service.update(
            patient_id, family_name, given_name, gender, phone, dob, address
        )
        if err is not None:
            return Response(status=400, response=err.args[0])

        if patient:
            return Response(
                status=200,
                response=json.dumps({"data": datetime_encoder(patient.dict())}),
            )
        else:
            return Response(
                status=200, response=json.dumps({"data": []}, default=json_serial)
            )
