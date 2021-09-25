import json

from fhir.resources.diagnosticreport import DiagnosticReport
from firebase_admin import auth
from flask import Blueprint, request
from flask.wrappers import Response
from pydantic.types import Json

from adapters.fhir_store import ResourceClient
from json_serialize import json_serial
from utils.datetime_encoder import datetime_encoder
from utils.middleware import jwt_authenticated, jwt_authorized

diagnostic_reports_blueprint = Blueprint("diagnostic_reports", __name__, url_prefix="/")


@diagnostic_reports_blueprint.route(
    "patients/<patient_id>/diagnostic_reports/<diagnostic_report_id>", methods=["GET"]
)
@jwt_authenticated()
@jwt_authorized("/Patient/{patient_id}")
def get_diagnostic_report(patient_id: str, diagnostic_report_id: str) -> Response:
    return DiagnosticReportController().get_diagnostic_report(
        patient_id, diagnostic_report_id
    )


@diagnostic_reports_blueprint.route(
    "patients/<patient_id>/encounters/<encounter_id>/diagnostic_reports",
    methods=["GET"],
)
@jwt_authenticated()
@jwt_authorized("/Patient/{patient_id}")
def get_diagnostic_report_by_encounter(patient_id: str, encounter_id: str) -> Response:
    return DiagnosticReportController().get_diagnostic_report_by_encounter(
        patient_id, encounter_id
    )


@diagnostic_reports_blueprint.route(
    "practitioners/<practitioner_id>/diagnostic_reports", methods=["GET"]
)
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def get_diagnostic_reports(practitioner_id: str) -> Response:
    return DiagnosticReportController().get_diagnostic_reports(practitioner_id)


@diagnostic_reports_blueprint.route("diagnostic_reports", methods=["POST"])
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def create_diagnostic_report() -> Response:
    return DiagnosticReportController().create_diagnostic_report(request.get_json())


@diagnostic_reports_blueprint.route(
    "diagnostic_reports/<diagnostic_report_id>", methods=["PATCH"]
)
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def update_diagnostic_report(diagnostic_report_id: str) -> Response:
    return DiagnosticReportController().update_diagnostic_report(
        diagnostic_report_id, request.get_json()
    )


class DiagnosticReportController:
    def __init__(self, resource_client=None, firebase_auth=None):
        self.resource_client = resource_client or ResourceClient()
        self.firebase_auth = firebase_auth or auth

    def _search_diagnostic_report(self, search_clause):
        """
        Helper function to return details of diagnostic report search result

        :param search_clause: parameters to search on DiagnosticReport
        :type search_clause: List(Tuple(str, str))

        :rtype: Response
        """
        diagnostic_report_search = self.resource_client.search(
            "DiagnosticReport", search=search_clause
        )

        if diagnostic_report_search.entry is None:
            return Response(
                status=200, response=json.dumps({"data": []}, default=json_serial)
            )
        return Response(
            status=200,
            response=json.dumps(
                {
                    "data": [
                        datetime_encoder(e.resource.dict())
                        for e in diagnostic_report_search.entry
                    ]
                },
                default=json_serial,
            ),
        )

    def get_diagnostic_report(
        self, patient_id: str, diagnostic_report_id: str
    ) -> Response:
        """
        Returns details of a diagnostic report given patient_id

        :param patient_id: uuid for patient
        :type patient_id: str
        :param diagnostic_report_id: uuid for diagnostic report
        :type diagnostic_report_id: str

        :rtype: Response
        """
        search_list = [("patient", patient_id), ("id", diagnostic_report_id)]
        return self._search_diagnostic_report(search_list)

    def get_diagnostic_report_by_encounter(self, patient_id: str, encounter_id: str):
        """
        Returns details of diagnostic report returned by patient id and encounter id

        :param patient_id: uuid for patient
        :type patient_id: str
        :param encounter_id: uuid for encounter
        :type encounter_id: str

        :rtype: Response
        """
        search_list = [("patient", patient_id), ("encounter", encounter_id)]
        return self._search_diagnostic_report(search_list)

    def get_diagnostic_reports(self, practitioner_id: str) -> Response:
        """
        Returns details of diagnostic report by doctor id

        :param practitioner_id: uuid for doctor
        :type practitioner_id: str

        :rtype: Response
        """
        search_list = [("performer", practitioner_id)]
        return self._search_diagnostic_report(search_list)

    def create_diagnostic_report(self, data: Json) -> Response:
        """Returns the details of a diagnostic report created.

        This creates a diagnostic report in FHIR
        Note that this function should only be called
        from the frontend client(by doctor) since everything assumes to use Firebase for
        authentication/authorization. diagnostic Report should be created after encounter is created

        Body should contain appointment, practitionerRole, and patient

        :param data: FHIR data for diagnostic report
        :type data: JSON

        :rtype: Response
        """
        diagnostic_report = DiagnosticReport.parse_obj(data)
        diagnostic_report = self.resource_client.create_resource(diagnostic_report)

        return Response(status=201, response=datetime_encoder(diagnostic_report.json()))

    def update_diagnostic_report(
        self, diagnostic_report_id: str, data: Json
    ) -> Response:
        """Update diagnostic report

        This overwrites current result of diagnostic report

        :param diagnostic_report_id: uuid of diagnostic report. e.g. { data: "conclusion"}
        :type diagnostic_report_id: str
        :param data: data you want to overwrite
        :type data: Json

        :rtype: Response
        """
        value = [{"op": "add", "path": "/conclusion", "value": data["conclusion"]}]

        new_diagnostic_report = self.resource_client.patch_resource(
            diagnostic_report_id, "DiagnosticReport", value
        )

        return Response(status=200, response=new_diagnostic_report.json())
