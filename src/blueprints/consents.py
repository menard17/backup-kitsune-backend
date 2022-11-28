import json

from flask import Blueprint, request
from flask.wrappers import Response

from adapters.fhir_store import ResourceClient
from json_serialize import json_serial
from utils import role_auth
from utils.datetime_encoder import datetime_encoder
from utils.middleware import jwt_authenticated

consent_blueprint = Blueprint("consents", __name__, url_prefix="/consents")


@consent_blueprint.route("/", methods=["GET"])
@jwt_authenticated()
def search_consents() -> Response:
    """
    Search the consents. Currently it accepts the following search parameters:
    * grantee (optional): the ID that is granted the consent. For instance, the primary patient ID.
        One of the `grantee` or `patient` parameter must be supplied.
    * patient (optional): the subject of the consent (if it is a patient). For instance, the secondary patient ID.
        One of the `grantee` or `patient` parameter must be supplied.
    * include_patient (optional): include the patient data as part of the response.
    """
    return ConsentsController().search(request)


class ConsentsController:
    def __init__(self, resource_client=None):
        self.resource_client = resource_client or ResourceClient()

    def search(self, request) -> Response:
        grantee_id = request.args.get("grantee")
        patient_id = request.args.get("patient")
        include_patient = request.args.get("include_patient")

        if patient_id is None and grantee_id is None:
            return Response(status=400, response="grantee or patient must be provided")

        claim_roles = role_auth.extract_roles(request.claims)
        if patient_id is not None:
            if not role_auth.is_authorized(
                claim_roles,
                "Patient",
                patient_id,
            ):
                return Response(
                    status=401,
                    response="Not Authorized for Consent Search (patient_id)",
                )

        if grantee_id is not None:
            if not role_auth.is_authorized(
                claim_roles,
                "Patient",
                grantee_id,
            ):
                return Response(
                    status=401,
                    response="Not Authorized for Consent Search (grantee_id)",
                )

        # see: http://hl7.org/fhir/2021Mar/consent.html#search
        # note that this is not the latest version of FHIR and the search parameters
        # are not the same.
        search_clause = []
        if patient_id is not None:
            search_clause.append(("patient", patient_id))
        if grantee_id is not None:
            search_clause.append(("actor", grantee_id))
        if include_patient:
            search_clause.append(("_include:iterate", "Consent:patient:Patient"))
        return self._search(search_clause)

    def _search(self, search_clause) -> Response:
        """
        Helper function to return resources based on search clauses

        :param search_clause: search parameters
        :type search_clause: list(tuple(str, str))

        :rtype: Response
        """
        search_result = self.resource_client.search("Consent", search=search_clause)

        if search_result.total == 0:
            return Response(
                status=200, response=json.dumps({"data": []}, default=json_serial)
            )
        return Response(
            status=200,
            response=json.dumps(
                {
                    "data": [
                        datetime_encoder(e.resource.dict()) for e in search_result.entry
                    ]
                },
                default=json_serial,
            ),
        )
