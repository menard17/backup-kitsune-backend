import json
from uuid import UUID

from flask import Blueprint, Request, request
from flask.wrappers import Response

from adapters.fhir_store import ResourceClient
from services.questionnaire_response_service import QuestionnaireResponseService
from utils.datetime_encoder import datetime_encoder
from utils.middleware import jwt_authenticated, jwt_authorized

questionnaire_response_blueprint = Blueprint(
    "questionnaireresponse", __name__, url_prefix="/questionnaire-response"
)


@questionnaire_response_blueprint.route(
    "<questionnaire_id>/patient/<patient_id>", methods=["POST"]
)
@jwt_authenticated()
@jwt_authorized("/Patient/{patient_id}")
def upsert_response(patient_id: UUID, questionnaire_id: UUID) -> Response:
    return QuestionnaireResponseController().upsert_response(
        patient_id, questionnaire_id, request
    )


@questionnaire_response_blueprint.route(
    "<questionnaire_id>/patient/<patient_id>", methods=["GET"]
)
@jwt_authenticated()
def get_questionnaire_response(patient_id: UUID, questionnaire_id: UUID) -> Response:
    return QuestionnaireResponseController().get_questionnaire_response(
        patient_id, questionnaire_id
    )


class QuestionnaireResponseController:
    def __init__(self, resource_client=None, questionnaire_response_service=None):
        self.resource_client = resource_client or ResourceClient()
        self.questionnaire_response_service = (
            questionnaire_response_service
            or QuestionnaireResponseService(self.resource_client)
        )

    def upsert_response(
        self, patient_id: UUID, questionnaire_id: UUID, request: Request
    ):
        request_data = request.json
        if request_data is None:
            return Response(
                status=400, response="The request must include a valid JSON body."
            )

        if questionnaire_response_id := self.questionnaire_response_service.find_response_id(
            patient_id, questionnaire_id
        ):
            questionnaire_response_data = (
                self.questionnaire_response_service.update_questionnaire_response(
                    questionnaire_response_id, request_data
                )
            )
        else:
            (
                _,
                questionnaire_response_data,
            ) = self.questionnaire_response_service.insert_questionnaire_response(
                request_data, patient_id, questionnaire_id
            )

        return Response(
            status=201,
            response=json.dumps(datetime_encoder(questionnaire_response_data.dict())),
        )

    def get_questionnaire_response(
        self, patient_id: UUID, questionnaire_id: UUID
    ) -> Response:
        if not (
            questionnaire_response_id := self.questionnaire_response_service.find_response_id(
                patient_id, questionnaire_id
            )
        ):
            return Response(status=404, response="no questionnaire response found")

        questionnaire_response_resource = self.resource_client.get_resource(
            questionnaire_response_id, "QuestionnaireResponse"
        )
        return Response(
            status=200,
            response=json.dumps(
                datetime_encoder(questionnaire_response_resource.dict())
            ),
        )
