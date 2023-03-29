import json
from uuid import UUID

from fhir.resources import construct_fhir_element
from fhir.resources.questionnaire import QuestionnaireItem
from flask import Blueprint, Request, request
from flask.wrappers import Response

from adapters.fhir_store import ResourceClient
from services.prequestionnaire_service import PrequestionnaireService
from utils.datetime_encoder import datetime_encoder
from utils.middleware import jwt_authenticated, jwt_authorized

prequestionnaire_blueprint = Blueprint(
    "prequestionnaire", __name__, url_prefix="/prequestionnaire"
)


@prequestionnaire_blueprint.route("/", methods=["POST"])
@jwt_authenticated()
@jwt_authorized("/Admin/*")
def create_questionnaire() -> Response:
    """
    This creates an empty prequestionnaire.
    """
    return PrequestionnaireController().create()


@prequestionnaire_blueprint.route("/<questionnaire_id>/items", methods=["POST"])
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def create_questionnaire_item(questionnaire_id: UUID) -> Response:
    return PrequestionnaireController().create_questionnaire_item(
        questionnaire_id, request
    )


@prequestionnaire_blueprint.route(
    "/<questionnaire_id>/items/<link_id>", methods=["PATCH"]
)
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def update_question(questionnaire_id: UUID, link_id: UUID) -> Response:
    return PrequestionnaireController().update_question(
        link_id, questionnaire_id, request
    )


@prequestionnaire_blueprint.route("/<questionnaire_id>/items", methods=["PUT"])
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def reorder_item_list(questionnaire_id: UUID) -> Response:
    return PrequestionnaireController().reorder_item_list(questionnaire_id, request)


@prequestionnaire_blueprint.route(
    "/<questionnaire_id>/items/<link_id>", methods=["DELETE"]
)
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def remove_question(questionnaire_id: UUID, link_id: UUID) -> Response:
    return PrequestionnaireController().remove_question(link_id, questionnaire_id)


@prequestionnaire_blueprint.route("/<questionnaire_id>", methods=["GET"])
@jwt_authenticated()
def get_prequestionnaire(questionnaire_id: UUID) -> Response:
    return PrequestionnaireController().get_prequestionnaire(questionnaire_id)


class PrequestionnaireController:
    def __init__(self, resource_client=None, prequestionnare_service=None):
        self.resource_client = resource_client or ResourceClient()
        self.prequestionnare_service = (
            prequestionnare_service or PrequestionnaireService(self.resource_client)
        )

    def create(self) -> Response:
        empty_questionnaire = {
            "resourceType": "Questionnaire",
            "id": "example-prequestionnaire-id",
            "status": "active",
            "subjectType": ["Patient"],
        }

        fhir_prequestionnaire = construct_fhir_element(
            "Questionnaire", empty_questionnaire
        )
        fhir_prequestionnaire = self.resource_client.create_resource(
            fhir_prequestionnaire
        )
        return Response(
            status=201,
            response=json.dumps(datetime_encoder(fhir_prequestionnaire.dict())),
        )

    def create_questionnaire_item(
        self, prequestionnaire_id: UUID, request: Request
    ) -> Response:
        request_data = request.json
        if not request_data:
            return Response(status=400, response="Request must include JSON body")

        validation_error = self.prequestionnare_service.validate_questionnaire_item(
            request_data
        )
        if validation_error:
            return Response(
                status=400,
                response=json.dumps(validation_error),
            )

        fhir_prequestionnaire = self.resource_client.get_resource(
            prequestionnaire_id, "Questionnaire"
        )
        if not fhir_prequestionnaire:
            return Response(status=404, response="No questionnaire found")

        _, updated_prequestionnaire = self.prequestionnare_service.add_question(
            request_data, fhir_prequestionnaire
        )

        return Response(
            status=201,
            response=json.dumps(datetime_encoder(updated_prequestionnaire.dict())),
        )

    def update_question(
        self, link_id: UUID, prequestionnaire_id: UUID, request: Request
    ) -> Response:
        request_data = request.json
        if not request_data:
            return Response(status=400, response="Request must include JSON body")

        validation_error = self.prequestionnare_service.validate_questionnaire_item(
            request_data
        )
        if validation_error:
            return Response(
                status=400,
                response=json.dumps(validation_error),
            )

        fhir_prequestionnaire = self.resource_client.get_resource(
            prequestionnaire_id, "Questionnaire"
        )

        if not fhir_prequestionnaire:
            return Response(status=404, response="No questionnaire found")

        # Find the index of the item to update
        item_index = None
        for idx, item in enumerate(fhir_prequestionnaire.item):
            if item.linkId == link_id:
                item_index = idx
                break

        if item_index is None:
            return Response(
                status=404, response=f"No question with linkId {link_id} found"
            )

        localization_list = self.prequestionnare_service.get_localization_items(
            request_data.get("localization", [])
        )
        enable_conditions = self.prequestionnare_service.get_enable_conditions(
            request_data, fhir_prequestionnaire
        )

        updated_item = QuestionnaireItem(
            linkId=link_id,
            text=request_data["text"],
            type=request_data["type"],
            answerOption=request_data.get("answerOption"),
            enableWhen=enable_conditions,
            extension=localization_list,
        )

        if fhir_prequestionnaire.item[item_index].type == "choice":
            old_options = list(map(lambda item: item.valueCoding.display, fhir_prequestionnaire.item[item_index].answerOption))
            new_options = []
            if updated_item.answerOption:
                new_options = list(map(lambda item: item.valueCoding.display, updated_item.answerOption))

            deleted_options = [option for option in old_options if option not in new_options]

            for deleted_option in deleted_options:
                for item in fhir_prequestionnaire.item or []:
                    if not item.enableWhen:
                        continue
                    item.enableWhen = [
                        ew for ew in item.enableWhen if ew.answerCoding.display != deleted_option
                    ]

        fhir_prequestionnaire.item[item_index] = updated_item

        updated_prequestionnaire = self.resource_client.put_resource(
            fhir_prequestionnaire.id, fhir_prequestionnaire
        )

        return Response(
            status=201,
            response=json.dumps(datetime_encoder(updated_prequestionnaire.dict())),
        )

    def remove_question(self, link_id: UUID, questionnaire_id: UUID) -> Response:
        # Get the questionnaire resource
        questionnaire = self.resource_client.get_resource(
            questionnaire_id, "Questionnaire"
        )
        if not questionnaire:
            return Response(status=404, response="No questionnaire found")

        # Find the question with the specified linkId and remove it from the questionnaire's items
        for idx, item in enumerate(questionnaire.item or []):
            if item.linkId == str(link_id):
                questionnaire.item.pop(idx)
                break

        # Remove any enableWhen items that reference the removed question
        for item in questionnaire.item or []:
            if not item.enableWhen:
                continue
            item.enableWhen = [
                ew for ew in item.enableWhen if ew.question != str(link_id)
            ]

        # Update the questionnaire resource on the FHIR server
        updated_prequestionnaire = self.resource_client.put_resource(
            questionnaire.id, questionnaire
        )

        return Response(
            status=200,
            response=json.dumps(datetime_encoder(updated_prequestionnaire.dict())),
        )

    def get_prequestionnaire(self, questionnaire_id: UUID) -> Response:
        questionnaire = self.resource_client.get_resource(
            questionnaire_id, "Questionnaire"
        )
        if not questionnaire:
            return Response(status=404, response="No questionnaire found")

        return Response(
            status=200,
            response=json.dumps(datetime_encoder(questionnaire.dict())),
        )

    def reorder_item_list(self, questionnaire_id: UUID, request: Request) -> Response:
        request_data = request.json
        if not request_data:
            return Response(status=400, response="Request must include JSON body")

        if not all(key in request_data for key in ["indexToMove", "linkId"]):
            return Response(
                status=400, response="Missing one or more required parameters"
            )

        fhir_questionnaire = self.resource_client.get_resource(
            questionnaire_id, "Questionnaire"
        )

        if not fhir_questionnaire:
            return Response(status=404, response="No questionnaire found")

        _, updated_questionnaire = self.prequestionnare_service.rearrange_question(
            fhir_questionnaire, request_data["indexToMove"], request_data["linkId"]
        )

        return Response(
            status=201,
            response=json.dumps(datetime_encoder(updated_questionnaire.dict())),
        )
