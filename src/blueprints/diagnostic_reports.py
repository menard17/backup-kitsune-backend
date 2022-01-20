import json

from fhir.resources import construct_fhir_element
from flask import Blueprint, request
from flask.wrappers import Response

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
    return DiagnosticReportController().create_diagnostic_report()


@diagnostic_reports_blueprint.route(
    "diagnostic_reports/<diagnostic_report_id>", methods=["PATCH"]
)
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def update_diagnostic_report(diagnostic_report_id: str) -> Response:
    request_body = request.get_json()
    conclusion = request_body.get("conclusion")
    return DiagnosticReportController().update_diagnostic_report(
        diagnostic_report_id, conclusion
    )


class DiagnosticReportController:
    def __init__(self, resource_client=None):
        self.resource_client = resource_client or ResourceClient()

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

        if diagnostic_report_search.total == 0:
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

    def create_diagnostic_report(self) -> Response:
        """Returns the details of a diagnostic report created.

        This creates a diagnostic report in FHIR
        Note that this function should only be called
        from the frontend client(by doctor or nurse) since everything assumes to use Firebase for
        authentication/authorization. diagnostic Report should be created after encounter is created
        sample json
        {
            'patient_id': '0d49bb25-97f7-4f6d-8459-2b6a18d4d170'
            'role_id': '0d49bb25-97f7-4f6d-8459-2b6a18d4d171',
            'encounter_id': '0d49bb25-97f7-4f6d-8459-2b6a18d4d172',
            'conclusion': 'conclusion'
        }

        :rtype: Response
        """

        request_body = request.get_json()
        if (
            (patient_id := request_body.get("patient_id")) is None
            or (encounter_id := request_body.get("encounter_id")) is None
            or (role_id := request_body.get("role_id")) is None
            or (conclusion := request_body.get("conclusion")) is None
        ):
            return Response(
                status=400,
                response="missing param: patient_id, encounter_id, practitioner_id, or conclusion",
            )

        # Check if there is diagnostic report
        diagnostic_report_search = self.resource_client.search(
            "DiagnosticReport", search=[("encounter", encounter_id)]
        )

        if diagnostic_report_search.total > 0:
            return self.update_diagnostic_report(
                diagnostic_report_search.entry[0].resource.id, conclusion
            )

        diagnostic_report_jsondict = {
            "resourceType": "DiagnosticReport",
            "status": "final",
            "subject": {"reference": f"Patient/{patient_id}"},
            "encounter": {"reference": f"Encounter/{encounter_id}"},
            "performer": [{"reference": f"PractitionerRole/{role_id}"}],
            "conclusion": conclusion,
            "code": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "448337001",
                        "display": "Telemedicine",
                    }
                ]
            },
        }
        diagnostic_report = construct_fhir_element(
            diagnostic_report_jsondict["resourceType"], diagnostic_report_jsondict
        )
        diagnostic_report = self.resource_client.create_resource(diagnostic_report)
        return Response(status=201, response=datetime_encoder(diagnostic_report.json()))

    def update_diagnostic_report(
        self,
        diagnostic_report_id: str,
        conclusion: str,
    ) -> Response:
        """Update diagnostic report

        This overwrites current result of diagnostic report

        :param diagnostic_report_id: uuid of diagnostic report.
        :type diagnostic_report_id: str
        :param conclusion: conclusion you want to override
        :type conclusion: str

        :rtype: Response
        """
        value = [{"op": "add", "path": "/conclusion", "value": conclusion}]

        new_diagnostic_report = self.resource_client.patch_resource(
            diagnostic_report_id, "DiagnosticReport", value
        )

        return Response(status=201, response=new_diagnostic_report.json())
